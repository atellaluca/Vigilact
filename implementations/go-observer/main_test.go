// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 Luca Atella
package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"path/filepath"
	"sync"
	"testing"
	"time"
)

func setup(t *testing.T) (*Observer, *time.Time, string) {
	t.Helper()
	path := filepath.Join(t.TempDir(), "observer.json")
	obs, err := newObserver(path, map[string]Identity{
		"node-a": {Role: "agent", Key: "a-very-long-test-secret-key"},
		"node-b": {Role: "agent", Key: "another-long-test-secret-key"},
		"ops":    {Role: "operator", Key: "the-operator-long-test-secret-key"},
	})
	if err != nil {
		t.Fatal(err)
	}
	now := time.Date(2031, 4, 5, 12, 0, 0, 0, time.UTC)
	obs.now = func() time.Time { return now }
	return obs, &now, path
}
func call(t *testing.T, o *Observer, method, path, principal string, payload interface{}) *httptest.ResponseRecorder {
	t.Helper()
	var body []byte
	if payload != nil {
		var e error
		body, e = json.Marshal(payload)
		if e != nil {
			t.Fatal(e)
		}
	}
	req := httptest.NewRequest(method, path, bytes.NewReader(body))
	if payload != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	if principal != "" {
		req.Header.Set("X-Vigilact-Principal", principal)
		keys := map[string]string{
			"node-a": "a-very-long-test-secret-key", "node-b": "another-long-test-secret-key", "ops": "the-operator-long-test-secret-key"}
		req.Header.Set("X-Vigilact-Key", keys[principal])
	}
	w := httptest.NewRecorder()
	o.ServeHTTP(w, req)
	return w
}
func create(t *testing.T, o *Observer, now time.Time) Contract {
	t.Helper()
	response := call(t, o, "POST", "/v1/contracts", "node-a", Proposal{
		ClientRef: "backup-1", Subject: "backup://node-a", Observation: Observation{Kind: "expected_event", EventType: "backup.completed", DeadlineAt: timestamp(now.Add(time.Minute))},
	})
	if response.Code != 201 {
		t.Fatalf("contract %d: %s", response.Code, response.Body.String())
	}
	var c Contract
	if e := json.Unmarshal(response.Body.Bytes(), &c); e != nil {
		t.Fatal(e)
	}
	return c
}
func validEvent() Event {
	return Event{Specversion: "1.0", ID: "run-1", Source: "urn:vigilact:agent:node-a", Type: "backup.completed", Subject: "backup://node-a", Data: map[string]interface{}{"ok": true}}
}
func TestSatisfactionDuplicateAndPersistence(t *testing.T) {
	o, now, path := setup(t)
	c := create(t, o, *now)
	evidence := validEvent()
	first := call(t, o, "POST", "/v1/events", "node-a", evidence)
	if first.Code != 200 {
		t.Fatal(first.Body.String())
	}
	var receipt struct {
		Status    string   `json:"status"`
		Satisfied []string `json:"satisfied_contracts"`
	}
	if e := json.Unmarshal(first.Body.Bytes(), &receipt); e != nil {
		t.Fatal(e)
	}
	if receipt.Status != "accepted" || len(receipt.Satisfied) != 1 || receipt.Satisfied[0] != c.ID {
		t.Fatalf("bad receipt: %+v", receipt)
	}
	second := call(t, o, "POST", "/v1/events", "node-a", evidence)
	if second.Code != 200 {
		t.Fatalf("duplicate: %s", second.Body.String())
	}
	if e := json.Unmarshal(second.Body.Bytes(), &receipt); e != nil {
		t.Fatal(e)
	}
	if receipt.Status != "duplicate" || len(receipt.Satisfied) != 0 {
		t.Fatalf("bad duplicate %+v", receipt)
	}
	changed := validEvent()
	changed.Data = map[string]interface{}{"ok": false}
	if got := call(t, o, "POST", "/v1/events", "node-a", changed); got.Code != 409 {
		t.Fatalf("conflicting event: %s", got.Body.String())
	}
	restarted, err := newObserver(path, o.identities)
	if err != nil {
		t.Fatal(err)
	}
	if view := call(t, restarted, "GET", "/v1/contracts/"+c.ID, "node-a", nil); view.Code != 200 || !bytes.Contains(view.Body.Bytes(), []byte("SATISFIED")) {
		t.Fatal(view.Body.String())
	}
	if page := call(t, restarted, "GET", "/v1/outbox", "ops", nil); page.Code != 200 || !bytes.Contains(page.Body.Bytes(), []byte("observation.satisfied")) {
		t.Fatal(page.Body.String())
	}
}
func TestMissingBoundaryAndLateEvidence(t *testing.T) {
	o, now, _ := setup(t)
	c := create(t, o, *now)
	*now = now.Add(time.Minute)
	if e := o.sweep(); e != nil {
		t.Fatal(e)
	}
	if got := call(t, o, "GET", "/v1/contracts/"+c.ID, "node-a", nil); !bytes.Contains(got.Body.Bytes(), []byte("PENDING")) {
		t.Fatal("exact boundary must still be pending")
	}
	*now = now.Add(time.Microsecond)
	if e := o.sweep(); e != nil {
		t.Fatal(e)
	}
	if got := call(t, o, "POST", "/v1/events", "node-a", validEvent()); got.Code != 200 || !bytes.Contains(got.Body.Bytes(), []byte(`"satisfied_contracts":[]`)) {
		t.Fatal(got.Body.String())
	}
	view := call(t, o, "GET", "/v1/contracts/"+c.ID, "node-a", nil)
	if !bytes.Contains(view.Body.Bytes(), []byte("NOT_OBSERVED")) {
		t.Fatal(view.Body.String())
	}
	page := call(t, o, "GET", "/v1/outbox", "ops", nil)
	if bytes.Count(page.Body.Bytes(), []byte("observation.not_observed")) != 1 {
		t.Fatal(page.Body.String())
	}
}
func TestAuthorizationAndConcurrency(t *testing.T) {
	o, now, _ := setup(t)
	c := create(t, o, *now)
	if got := call(t, o, "GET", "/v1/contracts/"+c.ID, "node-b", nil); got.Code != 404 {
		t.Fatalf("cross-tenant leak: %d", got.Code)
	}
	if got := call(t, o, "GET", "/v1/outbox", "node-a", nil); got.Code != 403 {
		t.Fatalf("outbox leak: %d", got.Code)
	}
	if got := call(t, o, "POST", "/v1/events", "node-b", validEvent()); got.Code != 403 {
		t.Fatalf("source spoofing: %d", got.Code)
	}
	var wg sync.WaitGroup
	statuses := make(chan int, 20)
	for i := 0; i < 20; i++ {
		wg.Add(1)
		go func() { defer wg.Done(); statuses <- call(t, o, "POST", "/v1/events", "node-a", validEvent()).Code }()
	}
	wg.Wait()
	close(statuses)
	for v := range statuses {
		if v != 200 {
			t.Fatalf("concurrent retry returned %d", v)
		}
	}
	if len(o.state.Outbox) != 1 {
		t.Fatalf("duplicate effects: %d", len(o.state.Outbox))
	}
}
func TestInvalidPayloadAndIdempotency(t *testing.T) {
	o, now, _ := setup(t)
	p := Proposal{ClientRef: "backup-1", Subject: "backup://node-a", Observation: Observation{Kind: "expected_event", EventType: "backup.completed", DeadlineAt: timestamp(now.Add(time.Minute))}}
	if response := call(t, o, "POST", "/v1/contracts", "", p); response.Code != 401 {
		t.Fatal(response.Code)
	}
	first := call(t, o, "POST", "/v1/contracts", "node-a", p)
	second := call(t, o, "POST", "/v1/contracts", "node-a", p)
	if first.Code != 201 || second.Code != 201 || first.Body.String() != second.Body.String() {
		t.Fatal("non-idempotent contract")
	}
	p.Observation.EventType = "different"
	if got := call(t, o, "POST", "/v1/contracts", "node-a", p); got.Code != 409 {
		t.Fatal(got.Body.String())
	}
	bad := validEvent()
	bad.Specversion = "2.0"
	if got := call(t, o, "POST", "/v1/events", "node-a", bad); got.Code != 403 && got.Code != 422 {
		t.Fatalf("invalid event passed: %s", got.Body.String())
	}
}

// Build is intentionally checked independently of Python; tests exercise the public HTTP surface.
var _ = http.MethodGet
