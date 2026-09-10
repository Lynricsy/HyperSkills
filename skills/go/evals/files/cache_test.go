package cache

import (
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestCache(t *testing.T) {
	dir, err := os.MkdirTemp("", "cache")
	if err != nil {
		t.Fatal(err)
	}
	defer os.RemoveAll(dir)

	c := New(filepath.Join(dir, "cache.db"))

	cases := []struct {
		name  string
		key   string
		value string
	}{
		{"ascii", "a", "1"},
		{"unicode", "b", "\u4e8c"},
		{"empty", "c", ""},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()
			c.Put(tc.key, tc.value)
			if got := c.Get(tc.key); got != tc.value {
				t.Errorf("bad")
			}
		})
	}
}

func TestExpiry(t *testing.T) {
	c := New("")
	c.PutTTL("k", "v", 50*time.Millisecond)
	time.Sleep(200 * time.Millisecond)
	if c.Get("k") != "" {
		t.Fatal("expected the entry to expire")
	}
}

func BenchmarkGet(b *testing.B) {
	c := New("")
	c.Put("k", "v")
	for i := 0; i < b.N; i++ {
		c.Get("k")
	}
}
