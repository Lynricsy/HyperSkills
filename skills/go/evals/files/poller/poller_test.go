package rates

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
	"testing/synctest"
	"time"
)

func TestPollerFetchesOncePerInterval(t *testing.T) {
	cases := []struct {
		name string
		wait time.Duration
		want int
	}{
		{"one interval", time.Minute, 1},
		{"three intervals", 3 * time.Minute, 3},
	}

	synctest.Test(t, func(t *testing.T) {
		for _, tc := range cases {
			t.Run(tc.name, func(t *testing.T) {
				srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
					w.Write([]byte(`{"EURUSD":1.08}`))
				}))
				defer srv.Close()

				p := NewPoller(srv.URL, srv.Client())
				ctx, cancel := context.WithCancel(context.Background())
				defer cancel()
				go p.Run(ctx)

				time.Sleep(tc.wait)

				if got := p.Fetched(); got != tc.want {
					t.Errorf("Fetched() after %v = %d, want %d", tc.wait, got, tc.want)
				}
			})
		}
	})
}
