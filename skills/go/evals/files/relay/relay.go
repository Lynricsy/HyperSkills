package relay

import (
	"context"
	"errors"
	"log/slog"
	"time"
)

// Message is one event read from the upstream feed.
type Message struct {
	ID   string
	Body []byte
}

// Sink forwards a message downstream.
type Sink interface {
	Send(ctx context.Context, m Message) error
}

// ErrIdle is returned when the upstream feed goes quiet for longer than idleTimeout.
var ErrIdle = errors.New("relay: upstream idle")

// Run forwards messages until ctx is cancelled or the feed goes quiet.
// Traffic is a few messages per minute per tenant; we run one Run per tenant
// (about 400 tenants per process).
func Run(ctx context.Context, in <-chan Message, out Sink, idleTimeout time.Duration) error {
	heartbeat := time.NewTicker(30 * time.Second)
	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		case m, ok := <-in:
			if !ok {
				return nil
			}
			if err := out.Send(ctx, m); err != nil {
				slog.Warn("relay: send failed", "id", m.ID, "err", err)
			}
		case <-heartbeat.C:
			slog.Debug("relay: alive")
		case <-time.After(idleTimeout):
			return ErrIdle
		}
	}
}
