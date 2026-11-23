// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 Luca Atella
// Vigilact independent Go observer: experimental core.expected_event/0.1 profile.
// Only the Go standard library is used. This is a reference experiment, not a production server.
package main

import (
	"crypto/rand"
	"crypto/subtle"
	"encoding/hex"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"log"
	"mime"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"
)

const maxBody = 262144
const protocol = "vigilact/0.1-experimental"

var safeAgent = regexp.MustCompile(`^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$`)
var safeRef = regexp.MustCompile(`^[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}$`)
var rfc3339micro = regexp.MustCompile(`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})$`)

type Identity struct {
	Role string `json:"role"`
	Key  string `json:"key"`
}
type Observation struct {
	Kind       string `json:"kind"`
	EventType  string `json:"event_type"`
	DeadlineAt string `json:"deadline_at"`
}
type Proposal struct {
	ClientRef   string      `json:"client_ref"`
	Subject     string      `json:"subject"`
	Observation Observation `json:"observation"`
}
type Contract struct {
	ID          string      `json:"id"`
	Owner       string      `json:"owner"`
	ClientRef   string      `json:"client_ref"`
	Subject     string      `json:"subject"`
	Observation Observation `json:"observation"`
	State       string      `json:"state"`
	Outcome     string      `json:"outcome"`
	AcceptedAt  string      `json:"accepted_at"`
	ResolvedAt  *string     `json:"resolved_at"`
}
type StoredContract struct {
	View Contract `json:"view"`
}

// JSONData is an object-only CloudEvents data payload: explicit null is not an object.
type JSONData map[string]interface{}

func (d *JSONData) UnmarshalJSON(value []byte) error {
	if strings.TrimSpace(string(value)) == "null" {
		return errors.New("data must be a JSON object, not null")
	}
	var decoded map[string]interface{}
	if err := json.Unmarshal(value, &decoded); err != nil {
		return err
	}
	if decoded == nil {
		return errors.New("data must be a JSON object")
	}
	*d = decoded
	return nil
}

type Event struct {
	Specversion     string   `json:"specversion"`
	ID              string   `json:"id"`
	Source          string   `json:"source"`
	Type            string   `json:"type"`
	Subject         string   `json:"subject"`
	Time            string   `json:"time,omitempty"`
	Datacontenttype string   `json:"datacontenttype"`
	Data            JSONData `json:"data"`
}
type OutboxEntry struct {
	Seq   int   `json:"seq"`
	Event Event `json:"event"`
}
type State struct {
	Contracts  map[string]StoredContract `json:"contracts"`
	References map[string]string         `json:"references"`
	Received   map[string]string         `json:"received"`
	Outbox     []OutboxEntry             `json:"outbox"`
}
type Observer struct {
	mu         sync.Mutex
	state      State
	path       string
	identities map[string]Identity
	now        func() time.Time
}

func emptyState() State {
	return State{Contracts: map[string]StoredContract{}, References: map[string]string{}, Received: map[string]string{}, Outbox: []OutboxEntry{}}
}
func timestamp(t time.Time) string {
	return t.UTC().Truncate(time.Microsecond).Format(time.RFC3339Nano)
}
func newID() string {
	var b [16]byte
	if _, e := rand.Read(b[:]); e != nil {
		panic(e)
	}
	return hex.EncodeToString(b[:])
}
func validateString(s string, length int) bool { return len(s) > 0 && len(s) <= length }
func parseTime(value string) (time.Time, error) {
	if !rfc3339micro.MatchString(value) {
		return time.Time{}, errors.New("timestamp must be RFC 3339 with at most 6 fractional digits")
	}
	t, err := time.Parse(time.RFC3339Nano, value)
	return t.UTC().Truncate(time.Microsecond), err
}
func newObserver(path string, identities map[string]Identity) (*Observer, error) {
	if len(identities) == 0 {
		return nil, errors.New("identities must not be empty")
	}
	for name, ident := range identities {
		if !safeAgent.MatchString(name) || (ident.Role != "agent" && ident.Role != "operator") || len(ident.Key) < 16 {
			return nil, fmt.Errorf("invalid identity %q", name)
		}
	}
	o := &Observer{path: path, identities: identities, now: time.Now, state: emptyState()}
	data, err := os.ReadFile(path)
	if err == nil {
		if e := json.Unmarshal(data, &o.state); e != nil {
			return nil, fmt.Errorf("invalid database: %w", e)
		}
		if o.state.Contracts == nil || o.state.References == nil || o.state.Received == nil || o.state.Outbox == nil {
			return nil, errors.New("incomplete database")
		}
	} else if !os.IsNotExist(err) {
		return nil, err
	}
	return o, nil
}

// Durable per-mutation snapshots are intentionally simple. Single-process writer only.
// Write and fsync temp file, rename, sync directory, and publish memory state on success.
func (o *Observer) save(next State) error {
	if err := os.MkdirAll(filepath.Dir(o.path), 0700); err != nil {
		return err
	}
	f, err := os.CreateTemp(filepath.Dir(o.path), ".vigilact-*.tmp")
	if err != nil {
		return err
	}
	defer os.Remove(f.Name())
	if err = f.Chmod(0600); err != nil {
		f.Close()
		return err
	}
	enc := json.NewEncoder(f)
	err = enc.Encode(next)
	if err == nil {
		err = f.Sync()
	}
	e := f.Close()
	if err == nil {
		err = e
	}
	if err != nil {
		return err
	}
	if err = os.Rename(f.Name(), o.path); err != nil {
		return err
	}
	if d, e := os.Open(filepath.Dir(o.path)); e == nil {
		err = d.Sync()
		d.Close()
		if err != nil {
			return err
		}
	}
	o.state = next
	return nil
}
func cloneState(s State) (State, error) {
	b, e := json.Marshal(s)
	if e != nil {
		return State{}, e
	}
	var result State
	e = json.Unmarshal(b, &result)
	return result, e
}
func (o *Observer) mutate(fn func(*State) (bool, error)) error {
	o.mu.Lock()
	defer o.mu.Unlock()
	next, err := cloneState(o.state)
	if err != nil {
		return err
	}
	changed, err := fn(&next)
	if err != nil {
		return err
	}
	if !changed {
		return nil
	}
	return o.save(next)
}
func addOutbox(s *State, c Contract, when time.Time, typ string) {
	event := Event{Specversion: "1.0", ID: newID(), Source: "urn:vigilact:go-observer", Type: typ,
		Subject: c.ID, Time: timestamp(when), Datacontenttype: "application/json",
		Data: map[string]interface{}{"contract_id": c.ID, "owner": c.Owner, "subject": c.Subject,
			"deadline_at": c.Observation.DeadlineAt, "expected_event_type": c.Observation.EventType}}
	s.Outbox = append(s.Outbox, OutboxEntry{Seq: len(s.Outbox) + 1, Event: event})
}
func evaluateDue(s *State, now time.Time) bool {
	// Deterministic ordering makes replayed evaluation streams reproducible.
	due := []string{}
	for id, record := range s.Contracts {
		deadline, _ := parseTime(record.View.Observation.DeadlineAt)
		if record.View.Outcome == "PENDING" && now.After(deadline) {
			due = append(due, id)
		}
	}
	sort.Slice(due, func(i, j int) bool {
		a := s.Contracts[due[i]].View.Observation.DeadlineAt
		b := s.Contracts[due[j]].View.Observation.DeadlineAt
		if a == b {
			return due[i] < due[j]
		}
		return a < b
	})
	for _, id := range due {
		c := s.Contracts[id].View
		c.Outcome = "NOT_OBSERVED"
		t := timestamp(now)
		c.ResolvedAt = &t
		s.Contracts[id] = StoredContract{View: c}
		addOutbox(s, c, now, "dev.vigilact.observation.not_observed")
	}
	return len(due) != 0
}
func (o *Observer) sweep() error {
	return o.mutate(func(s *State) (bool, error) { return evaluateDue(s, o.now().UTC().Truncate(time.Microsecond)), nil })
}
func problem(w http.ResponseWriter, status int, code, detail string) {
	writeJSON(w, status, map[string]interface{}{"type": "about:blank", "title": "Protocol error", "status": status, "detail": detail, "error": code}, "application/problem+json")
}
func writeJSON(w http.ResponseWriter, status int, value interface{}, media string) {
	b, e := json.Marshal(value)
	if e != nil {
		http.Error(w, "serialization failed", 500)
		return
	}
	w.Header().Set("Content-Type", media)
	w.Header().Set("Cache-Control", "no-store")
	w.WriteHeader(status)
	w.Write(append(b, '\n'))
}
func decode(w http.ResponseWriter, r *http.Request, dest interface{}) bool {
	media, _, mediaErr := mime.ParseMediaType(r.Header.Get("Content-Type"))
	if mediaErr != nil || media != "application/json" {
		problem(w, 415, "unsupported_media_type", "Send application/json")
		return false
	}
	dec := json.NewDecoder(http.MaxBytesReader(w, r.Body, maxBody))
	dec.DisallowUnknownFields()
	if err := dec.Decode(dest); err != nil {
		if strings.Contains(err.Error(), "http: request body too large") {
			problem(w, 413, "payload_too_large", "Request body too large")
		} else {
			problem(w, 422, "validation_error", "Invalid request JSON")
		}
		return false
	}
	var tail interface{}
	if e := dec.Decode(&tail); e != io.EOF {
		problem(w, 422, "validation_error", "Unexpected trailing JSON")
		return false
	}
	return true
}
func (o *Observer) auth(w http.ResponseWriter, r *http.Request, role string) (string, bool) {
	name := r.Header.Get("X-Vigilact-Principal")
	key := r.Header.Get("X-Vigilact-Key")
	record, ok := o.identities[name]
	if !ok || key == "" || subtle.ConstantTimeCompare([]byte(key), []byte(record.Key)) != 1 {
		problem(w, 401, "http_error", "Invalid Vigilact credentials")
		return "", false
	}
	if role != "" && role != record.Role {
		problem(w, 403, "http_error", "Role not permitted")
		return "", false
	}
	return name, true
}
func validProposal(p Proposal) bool {
	if !safeRef.MatchString(p.ClientRef) || !validateString(p.Subject, 255) || p.Observation.Kind != "expected_event" || !validateString(p.Observation.EventType, 200) {
		return false
	}
	_, e := parseTime(p.Observation.DeadlineAt)
	return e == nil
}
func contractEqual(c Contract, p Proposal) bool {
	a, _ := parseTime(c.Observation.DeadlineAt)
	b, _ := parseTime(p.Observation.DeadlineAt)
	return c.ClientRef == p.ClientRef && c.Subject == p.Subject && c.Observation.EventType == p.Observation.EventType && a.Equal(b)
}
func (o *Observer) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	path := r.URL.Path
	switch {
	case path == "/healthz" && r.Method == "GET":
		writeJSON(w, 200, map[string]string{"status": "ok"}, "application/json")
		return
	case path == "/readyz" && r.Method == "GET":
		writeJSON(w, 200, map[string]string{"status": "ready"}, "application/json")
		return
	case path == "/v1/info" && r.Method == "GET":
		writeJSON(w, 200, map[string]interface{}{"implementation": "vigilact-go-reference", "version": "0.4.0a1-go-core", "protocol": protocol,
			"profiles": []string{"core.expected_event/0.1"}, "features": map[string]interface{}{"remote_commands": false, "max_request_bytes": maxBody},
			"transport": "HTTP/JSON", "events": "CloudEvents 1.0 (restricted JSON subset)"}, "application/json")
		return
	case path == "/v1/contracts" && r.Method == "POST":
		owner, ok := o.auth(w, r, "agent")
		if !ok {
			return
		}
		var p Proposal
		if !decode(w, r, &p) {
			return
		}
		if !validProposal(p) {
			problem(w, 422, "validation_error", "Invalid contract proposal")
			return
		}
		var result Contract
		var code string
		err := o.mutate(func(s *State) (bool, error) {
			ref := owner + "\x00" + p.ClientRef
			if id, ok := s.References[ref]; ok {
				result = s.Contracts[id].View
				if !contractEqual(result, p) {
					code = "reference_conflict"
				}
				return false, nil
			}
			now := o.now().UTC().Truncate(time.Microsecond)
			deadline, _ := parseTime(p.Observation.DeadlineAt)
			if !deadline.After(now) {
				code = "deadline_elapsed"
				return false, nil
			}
			id := newID()
			p.Observation.DeadlineAt = timestamp(deadline)
			result = Contract{ID: id, Owner: owner, ClientRef: p.ClientRef, Subject: p.Subject, Observation: p.Observation,
				State: "ACTIVE", Outcome: "PENDING", AcceptedAt: timestamp(now)}
			s.Contracts[id] = StoredContract{View: result}
			s.References[ref] = id
			return true, nil
		})
		if err != nil {
			problem(w, 500, "storage_error", "Storage commit failed")
			return
		}
		if code != "" {
			status := 409
			if code == "deadline_elapsed" {
				status = 422
			}
			problem(w, status, code, "Contract not accepted")
			return
		}
		writeJSON(w, 201, result, "application/json")
		return
	case strings.HasPrefix(path, "/v1/contracts/") && r.Method == "GET":
		principal, ok := o.auth(w, r, "")
		if !ok {
			return
		}
		id := strings.TrimPrefix(path, "/v1/contracts/")
		o.mu.Lock()
		item, exists := o.state.Contracts[id]
		o.mu.Unlock()
		if !exists || (item.View.Owner != principal && o.identities[principal].Role != "operator") {
			problem(w, 404, "not_found", "Contract not found")
			return
		}
		writeJSON(w, 200, item.View, "application/json")
		return
	case path == "/v1/events" && r.Method == "POST":
		owner, ok := o.auth(w, r, "agent")
		if !ok {
			return
		}
		var event Event
		if !decode(w, r, &event) {
			return
		}
		if event.Source != "urn:vigilact:agent:"+owner {
			problem(w, 403, "source_mismatch", "Event source does not match agent identity")
			return
		}
		if event.Specversion != "1.0" || !validateString(event.ID, 128) || !validateString(event.Type, 200) || !validateString(event.Subject, 255) || !validateString(event.Source, 255) {
			problem(w, 422, "validation_error", "Invalid event fields")
			return
		}
		if event.Datacontenttype == "" {
			event.Datacontenttype = "application/json"
		}
		if event.Datacontenttype != "application/json" {
			problem(w, 422, "validation_error", "Only JSON events supported")
			return
		}
		if event.Data == nil {
			// Explicit null is not accepted by the Python model; an omitted field
			// is filled by the Go decoder's defaulting behavior below.
			event.Data = map[string]interface{}{}
		}
		if event.Time != "" {
			t, e := parseTime(event.Time)
			if e != nil {
				problem(w, 422, "validation_error", "Invalid event timestamp")
				return
			}
			event.Time = timestamp(t)
		}
		canonical, _ := json.Marshal(event)
		result := map[string]interface{}{"status": "accepted", "satisfied_contracts": []string{}}
		var code string
		err := o.mutate(func(s *State) (bool, error) {
			key := event.Source + "\x00" + event.ID
			if old, ok := s.Received[key]; ok {
				if old != string(canonical) {
					code = "event_conflict"
				} else {
					result["status"] = "duplicate"
				}
				return false, nil
			}
			now := o.now().UTC().Truncate(time.Microsecond)
			evaluateDue(s, now)
			s.Received[key] = string(canonical)
			satisfied := []string{}
			ids := make([]string, 0, len(s.Contracts))
			for id := range s.Contracts {
				ids = append(ids, id)
			}
			sort.Strings(ids)
			for _, id := range ids {
				rec := s.Contracts[id]
				c := rec.View
				deadline, _ := parseTime(c.Observation.DeadlineAt)
				accepted, _ := parseTime(c.AcceptedAt)
				if c.Owner == owner && c.Subject == event.Subject && c.Observation.EventType == event.Type && c.Outcome == "PENDING" && !now.Before(accepted) && !now.After(deadline) {
					c.Outcome = "SATISFIED"
					t := timestamp(now)
					c.ResolvedAt = &t
					s.Contracts[id] = StoredContract{View: c}
					addOutbox(s, c, now, "dev.vigilact.observation.satisfied")
					satisfied = append(satisfied, id)
				}
			}
			result["satisfied_contracts"] = satisfied
			return true, nil
		})
		if err != nil {
			problem(w, 500, "storage_error", "Storage commit failed")
			return
		}
		if code != "" {
			problem(w, 409, code, "Event ID reused with conflicting data")
			return
		}
		writeJSON(w, 200, result, "application/json")
		return
	case path == "/v1/outbox" && r.Method == "GET":
		if _, ok := o.auth(w, r, "operator"); !ok {
			return
		}
		after := 0
		limit := 100
		if raw := r.URL.Query().Get("after"); raw != "" {
			parsed, err := strconv.ParseInt(raw, 10, 64)
			if err != nil || parsed < 0 || parsed > 2147483647 {
				problem(w, 422, "validation_error", "Invalid after cursor")
				return
			}
			after = int(parsed)
		}
		if raw := r.URL.Query().Get("limit"); raw != "" {
			parsed, err := strconv.Atoi(raw)
			if err != nil || parsed < 1 || parsed > 500 {
				problem(w, 422, "validation_error", "Invalid limit")
				return
			}
			limit = parsed
		}
		o.mu.Lock()
		entries := []OutboxEntry{}
		for _, e := range o.state.Outbox {
			if e.Seq > after {
				entries = append(entries, e)
				if len(entries) >= limit {
					break
				}
			}
		}
		o.mu.Unlock()
		cursor := after
		if len(entries) > 0 {
			cursor = entries[len(entries)-1].Seq
		}
		writeJSON(w, 200, map[string]interface{}{"entries": entries, "next_cursor": cursor}, "application/json")
		return
	default:
		problem(w, 404, "not_found", "Endpoint unavailable for this profile")
		return
	}
}
func main() {
	addr := flag.String("addr", "127.0.0.1:18949", "Local HTTP address")
	db := flag.String("db", "./vigilact-go-state.json", "File-backed JSON state (single-process)")
	flag.Parse()
	var identities map[string]Identity
	if err := json.Unmarshal([]byte(os.Getenv("VIGILACT_CREDENTIALS_JSON")), &identities); err != nil {
		log.Fatal("VIGILACT_CREDENTIALS_JSON required: ", err)
	}
	o, err := newObserver(*db, identities)
	if err != nil {
		log.Fatal(err)
	}
	if err := o.sweep(); err != nil {
		log.Fatal(err)
	}
	go func() {
		ticker := time.NewTicker(250 * time.Millisecond)
		defer ticker.Stop()
		for range ticker.C {
			if err := o.sweep(); err != nil {
				log.Printf("sweep failed: %v", err)
			}
		}
	}()
	server := &http.Server{Addr: *addr, Handler: o, ReadHeaderTimeout: 5 * time.Second, ReadTimeout: 10 * time.Second, WriteTimeout: 10 * time.Second, IdleTimeout: 30 * time.Second}
	log.Printf("Vigilact Go core observer (experimental), listening on %s", *addr)
	log.Fatal(server.ListenAndServe())
}
