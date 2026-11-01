// Package linkutil is imported by the orders service and by three other teams'
// modules, some of which still build with Go 1.24.
package linkutil

import (
	"net/url"
	"strings"
)

// LastSegment returns the final path segment of u ("" if the path ends in "/").
func LastSegment(u *url.URL) string {
	i := strings.LastIndex(u.Path, "/")
	if i < 0 {
		return u.Path
	}
	return u.Path[i+1:]
}

// WithParam returns a copy of u with key=value set.
func WithParam(u *url.URL, key, value string) *url.URL {
	c := *u
	if u.User != nil {
		user := *u.User
		c.User = &user
	}
	q := c.Query()
	q.Set(key, value)
	c.RawQuery = q.Encode()
	return &c
}
