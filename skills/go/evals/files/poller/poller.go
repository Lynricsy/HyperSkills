package rates

import (
	"context"
	"io"
	"net/http"
	"sync"
	"time"
)

// Poller fetches the latest exchange-rate snapshot once per Interval until its
// context ends.
type Poller struct {
	URL      string
	Interval time.Duration
	Timeout  time.Duration
	Client   *http.Client

	mu      sync.Mutex
	fetched int
	last    []byte
}

func NewPoller(url string, client *http.Client) *Poller {
	return &Poller{URL: url, Interval: time.Minute, Timeout: 5 * time.Second, Client: client}
}

func (p *Poller) Run(ctx context.Context) {
	tick := time.NewTicker(p.Interval)
	defer tick.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-tick.C:
			p.fetch(ctx)
		}
	}
}

func (p *Poller) fetch(ctx context.Context) {
	ctx, cancel := context.WithTimeout(ctx, p.Timeout)
	defer cancel()
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, p.URL, nil)
	if err != nil {
		return
	}
	resp, err := p.Client.Do(req)
	if err != nil {
		return
	}
	defer resp.Body.Close()
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return
	}
	p.mu.Lock()
	p.fetched++
	p.last = body
	p.mu.Unlock()
}

// Fetched reports how many snapshots have been stored.
func (p *Poller) Fetched() int {
	p.mu.Lock()
	defer p.mu.Unlock()
	return p.fetched
}
