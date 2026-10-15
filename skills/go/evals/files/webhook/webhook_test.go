package hooks

import (
	"testing"
	"time"
)

func TestDecode(t *testing.T) {
	e, err := Decode([]byte(`{"id":"evt_1","type":"invoice.paid","retry":30000000000,"attempts":2,"tags":["eu"]}`))
	if err != nil {
		t.Fatalf("Decode: %v", err)
	}
	if e.ID != "evt_1" || e.Type != "invoice.paid" || e.Retry != 30*time.Second || e.Attempts != 2 {
		t.Errorf("Decode = %+v", e)
	}
}

func TestEncodeRoundTrip(t *testing.T) {
	in := Event{ID: "evt_2", Type: "invoice.voided", Retry: time.Second, Attempts: 1, Tags: []string{"us"}}
	b, err := Encode(in)
	if err != nil {
		t.Fatalf("Encode: %v", err)
	}
	out, err := Decode(b)
	if err != nil {
		t.Fatalf("Decode(Encode): %v", err)
	}
	if out.ID != in.ID || out.Retry != in.Retry || out.Attempts != in.Attempts {
		t.Errorf("round trip = %+v, want %+v", out, in)
	}
}
