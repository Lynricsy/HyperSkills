package hooks

import (
	"encoding/json"
	"time"
)

// Event is one delivery from the payment provider. Payloads arrive from the
// internet; Encode output is stored and replayed by the audit service, which
// expects the same JSON shape it has always received.
type Event struct {
	ID       string
	Type     string        `json:"type"`
	Retry    time.Duration `json:"retry"`
	Attempts int           `json:"attempts,omitempty"`
	Tags     []string      `json:"tags"`
}

func Decode(b []byte) (Event, error) {
	var e Event
	err := json.Unmarshal(b, &e)
	return e, err
}

func Encode(e Event) ([]byte, error) {
	return json.Marshal(e)
}
