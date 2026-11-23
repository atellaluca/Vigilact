// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 Luca Atella
//
// Independent, dependency-free semantic evaluator for the experimental
// expected-event fixture profile. NOT a second Vigilact HTTP server.
package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"reflect"
)

type Event struct {
	Offset     int            `json:"offset_seconds"`
	ID         string         `json:"id"`
	Agent      string         `json:"agent"`
	Source     string         `json:"source"`
	Type       string         `json:"type"`
	Subject    string         `json:"subject"`
	TimeOffset *int           `json:"time_offset_seconds"`
	Data       map[string]any `json:"data"`
}
type Expected struct {
	Outcome   string   `json:"outcome"`
	Receipts  []string `json:"receipts"`
	Emissions []string `json:"emissions"`
}
type Case struct {
	ID       string   `json:"id"`
	Deadline int      `json:"deadline_offset_seconds"`
	Events   []Event  `json:"events"`
	End      int      `json:"evaluate_at_seconds"`
	Expected Expected `json:"expected"`
}
type Fixture struct {
	Schema    string `json:"schema"`
	Owner     string `json:"contract_owner"`
	Subject   string `json:"subject"`
	EventType string `json:"event_type"`
	Cases     []Case `json:"cases"`
}
type Output struct {
	ID        string   `json:"id"`
	Outcome   string   `json:"outcome"`
	Receipts  []string `json:"receipts"`
	Emissions []string `json:"emissions"`
}

func evaluate(c Case, f Fixture) Output {
	result := Output{ID: c.ID, Outcome: "PENDING", Receipts: []string{}, Emissions: []string{}}
	seen := make(map[string][]byte)
	for _, ev := range c.Events {
		if ev.Offset > c.Deadline && result.Outcome == "PENDING" {
			result.Outcome = "NOT_OBSERVED"
			result.Emissions = append(result.Emissions, "not_observed")
		}
		agent := ev.Agent
		if agent == "" {
			agent = f.Owner
		}
		source := ev.Source
		if source == "" {
			source = "urn:vigilact:agent:" + agent
		}
		if source != "urn:vigilact:agent:"+agent {
			result.Receipts = append(result.Receipts, "source_mismatch")
			continue
		}
		data := ev.Data
		if data == nil {
			data = map[string]any{"result": "ok"}
		}
		// The event's optional asserted time is part of its identity's payload,
		// but NOT a substitute for observer receipt time when evaluating.
		signature := []any{source, ev.ID, ev.Type, ev.Subject, data, ev.TimeOffset}
		encoded, _ := json.Marshal(signature)
		key := source + "\x00" + ev.ID
		if prior, ok := seen[key]; ok {
			if bytes.Equal(prior, encoded) {
				result.Receipts = append(result.Receipts, "duplicate:0")
			} else {
				result.Receipts = append(result.Receipts, "event_conflict")
			}
			continue
		}
		seen[key] = encoded
		if result.Outcome == "PENDING" && ev.Offset <= c.Deadline && agent == f.Owner && ev.Type == f.EventType && ev.Subject == f.Subject {
			result.Outcome = "SATISFIED"
			result.Emissions = append(result.Emissions, "satisfied")
			result.Receipts = append(result.Receipts, "accepted:1")
		} else {
			result.Receipts = append(result.Receipts, "accepted:0")
		}
	}
	if c.End > c.Deadline && result.Outcome == "PENDING" {
		result.Outcome = "NOT_OBSERVED"
		result.Emissions = append(result.Emissions, "not_observed")
	}
	return result
}
func main() {
	path := flag.String("fixtures", "spec/vectors/expected-event.json", "fixture path")
	check := flag.Bool("check", false, "check expected results")
	flag.Parse()
	raw, err := os.ReadFile(*path)
	if err != nil {
		panic(err)
	}
	var fixture Fixture
	if err = json.Unmarshal(raw, &fixture); err != nil {
		panic(err)
	}
	if fixture.Schema != "vigilact.expected-event.vectors/0.1" {
		panic("unknown fixture schema")
	}
	results := make([]Output, 0, len(fixture.Cases))
	for _, c := range fixture.Cases {
		actual := evaluate(c, fixture)
		results = append(results, actual)
		if *check && !reflect.DeepEqual(actual, Output{ID: c.ID, Outcome: c.Expected.Outcome, Receipts: c.Expected.Receipts, Emissions: c.Expected.Emissions}) {
			fmt.Fprintf(os.Stderr, "FAIL %s: got %+v expected %+v\n", c.ID, actual, c.Expected)
			os.Exit(1)
		}
	}
	if *check {
		fmt.Printf("PASS: %d independent Go evaluator vectors\n", len(results))
	} else {
		output, _ := json.MarshalIndent(results, "", "  ")
		fmt.Println(string(output))
	}
}
