package pipeline

import (
	"context"
	"time"
)

type Job struct {
	ID      int
	Payload string
}

// Dispatch fans jobs out to workers and collects their results.
func Dispatch(ctx context.Context, jobs []Job) []string {
	results := make(chan string)

	for _, job := range jobs {
		go func(j Job) {
			out, err := process(ctx, j)
			if err != nil {
				return
			}
			results <- out
		}(job)
	}

	collected := make([]string, 0, len(jobs))
	timeout := time.After(2 * time.Second)

	for range jobs {
		select {
		case r := <-results:
			collected = append(collected, r)
		case <-timeout:
			return collected
		}
	}

	return collected
}

func watch(ctx context.Context, tick time.Duration) <-chan time.Time {
	out := make(chan time.Time)
	go func() {
		t := time.NewTicker(tick)
		for now := range t.C {
			out <- now
		}
	}()
	return out
}

func process(ctx context.Context, j Job) (string, error) {
	time.Sleep(10 * time.Millisecond)
	return j.Payload, nil
}
