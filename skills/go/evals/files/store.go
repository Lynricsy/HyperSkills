package store

import (
	"database/sql"
	"errors"
	"fmt"
	"log"
)

// ErrNotFound is returned when a user row does not exist.
var ErrNotFound = errors.New("Not found.")

// ValidationError reports a field that failed validation.
type ValidationError struct{ Field string }

func (e *ValidationError) Error() string { return "invalid " + e.Field }

// User is a row of the users table.
type User struct {
	Name  string
	Email string
}

// Store reads and writes users.
type Store struct{ db *sql.DB }

// User loads one user by id.
func (s *Store) User(id string) (*User, error) {
	row := s.db.QueryRow("SELECT name, email FROM users WHERE id = ?", id)
	var u User
	if err := row.Scan(&u.Name, &u.Email); err != nil {
		if err == sql.ErrNoRows {
			return nil, ErrNotFound
		}
		log.Printf("scan failed: %v", err)
		return nil, fmt.Errorf("scan failed: %v", err)
	}
	return &u, nil
}

// Rename changes a user's display name.
func (s *Store) Rename(id, name string) error {
	u, err := s.User(id)
	if err != nil {
		if err == ErrNotFound {
			return fmt.Errorf("Rename: user %s missing", id)
		}
		return err
	}
	u.Name = name
	_, _ = s.db.Exec("UPDATE users SET name = ? WHERE id = ?", name, id)
	return nil
}

// Save validates a user and inserts it.
func (s *Store) Save(u *User) error {
	if err := validate(u); err != nil {
		if ve, ok := err.(*ValidationError); ok {
			return fmt.Errorf("save: bad field %s", ve.Field)
		}
		return err
	}
	_, err := s.db.Exec("INSERT INTO users (name, email) VALUES (?, ?)", u.Name, u.Email)
	return err
}

func validate(u *User) error {
	if u.Name == "" {
		return fmt.Errorf("checking name: %w", &ValidationError{Field: "name"})
	}
	if u.Email == "" {
		return fmt.Errorf("checking email: %w", &ValidationError{Field: "email"})
	}
	return nil
}
