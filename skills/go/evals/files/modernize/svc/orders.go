package svc

import (
	"context"
	"io"
	"log/slog"
	"net/url"
	"os"
	"strings"

	"github.com/google/uuid"
)

// NewOrderID returns the primary key for a new orders row. Rows are inserted in
// creation order and the index is a B-tree on this column.
func NewOrderID() string {
	return uuid.New().String()
}

// SplitSKU splits "vendor/line/item-42" into ("vendor/line", "item-42").
func SplitSKU(sku string) (prefix, item string, ok bool) {
	i := strings.LastIndex(sku, "/")
	if i < 0 {
		return sku, "", false
	}
	return sku[:i], sku[i+1:], true
}

// fanout sends every record to all handlers.
type fanout []slog.Handler

func (f fanout) Enabled(ctx context.Context, l slog.Level) bool {
	for _, h := range f {
		if h.Enabled(ctx, l) {
			return true
		}
	}
	return false
}

func (f fanout) Handle(ctx context.Context, r slog.Record) error {
	for _, h := range f {
		if h.Enabled(ctx, r.Level) {
			if err := h.Handle(ctx, r.Clone()); err != nil {
				return err
			}
		}
	}
	return nil
}

func (f fanout) WithAttrs(as []slog.Attr) slog.Handler {
	out := make(fanout, len(f))
	for i, h := range f {
		out[i] = h.WithAttrs(as)
	}
	return out
}

func (f fanout) WithGroup(name string) slog.Handler {
	out := make(fanout, len(f))
	for i, h := range f {
		out[i] = h.WithGroup(name)
	}
	return out
}

// NewLogger writes text to stderr and JSON to the audit file.
func NewLogger(audit io.Writer) *slog.Logger {
	return slog.New(fanout{slog.NewTextHandler(os.Stderr, nil), slog.NewJSONHandler(audit, nil)})
}

// PageURL returns base with page=n, leaving base untouched.
func PageURL(base *url.URL, n string) *url.URL {
	u := *base
	q := u.Query()
	q.Set("page", n)
	u.RawQuery = q.Encode()
	return &u
}
