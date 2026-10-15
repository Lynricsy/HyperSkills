CREATE TABLE members (
  id          bigint PRIMARY KEY,
  email       text NOT NULL UNIQUE,
  points      integer NOT NULL DEFAULT 0 CHECK (points >= 0),
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE bonus_claims (
  member_id   bigint NOT NULL REFERENCES members (id),
  kind        text NOT NULL,
  claimed_at  timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (member_id, kind)
);

CREATE TABLE receipts (
  id            bigserial PRIMARY KEY,
  member_id     bigint NOT NULL REFERENCES members (id),
  object_key    text NOT NULL UNIQUE,
  original_name text NOT NULL
);

CREATE TABLE audit_log (
  id         bigserial PRIMARY KEY,
  actor_id   bigint NOT NULL,
  action     text NOT NULL,
  target_id  bigint,
  detail     jsonb,
  at         timestamptz NOT NULL DEFAULT now()
);
