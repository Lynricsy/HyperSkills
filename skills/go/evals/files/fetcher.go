package fetch

import (
	"io"
	"net/http"
	"sync"
	"time"
)

// Result is one downloaded URL.
type Result struct {
	URL  string
	Body []byte
	Err  error
}

var cache = map[string]*Result{}

// FetchAll downloads every URL with a pool of workers and returns the results.
func FetchAll(urls []string, workers int) []*Result {
	jobs := make(chan string)
	out := make(chan *Result)

	var wg sync.WaitGroup
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for u := range jobs {
				r := fetch(u)
				cache[u] = r
				out <- r
			}
		}()
	}

	go func() {
		for _, u := range urls {
			jobs <- u
		}
		close(jobs)
	}()

	results := make([]*Result, 0, len(urls))
	go func() {
		for r := range out {
			results = append(results, r)
		}
	}()

	wg.Wait()
	time.Sleep(100 * time.Millisecond) // let the collector drain
	return results
}

func fetch(u string) *Result {
	resp, err := http.Get(u)
	if err != nil {
		return &Result{URL: u, Err: err}
	}
	defer resp.Body.Close()
	b, err := io.ReadAll(resp.Body)
	return &Result{URL: u, Body: b, Err: err}
}
