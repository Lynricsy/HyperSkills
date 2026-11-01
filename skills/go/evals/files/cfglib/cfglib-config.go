package cfglib

import (
	"cmp"
	"time"
)

// Config is filled from flags/env by callers; zero values mean "use the default".
type Config struct {
	Addr       string
	Timeout    time.Duration
	MaxRetries int
	UserAgent  string
}

// WithDefaults returns cfg with every zero field replaced by its default.
// PR #212 ("modernize defaults"): replaced four if-zero blocks with cmp.Or.
func WithDefaults(cfg Config) Config {
	cfg.Addr = cmp.Or(cfg.Addr, ":8080")
	cfg.Timeout = cmp.Or(cfg.Timeout, 30*time.Second)
	cfg.MaxRetries = cmp.Or(cfg.MaxRetries, 3)
	cfg.UserAgent = cmp.Or(cfg.UserAgent, "cfglib/1")
	return cfg
}
