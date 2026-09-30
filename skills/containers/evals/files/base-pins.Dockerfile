# syntax=docker/dockerfile:1
# Release notes: "runtime base is Alpine 3.23, build toolchain Go 1.26".

FROM golang:1.26-alpine@sha256:8ac98ca534ac3f51e1f420a1dd2c15e74c75cfa0f23f3ad27eb5d7236c349a0c AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN --mount=type=cache,target=/go/pkg/mod go mod download
COPY . .
RUN --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 go build -trimpath -o /out/ledger ./cmd/ledger

FROM alpine:3.23@sha256:28bd5fe8b56d1bd048e5babf5b10710ebe0bae67db86916198a6eec434943f8b
RUN apk add --no-cache ca-certificates tzdata
COPY --from=build /out/ledger /usr/local/bin/ledger
USER 65532:65532
ENTRYPOINT ["/usr/local/bin/ledger"]
