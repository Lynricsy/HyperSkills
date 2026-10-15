#!/usr/bin/env bash
# Catalogue thumbnails: 400px WebP, metadata removed (privacy review: no GPS in
# anything we publish). Run from the repo root; reads photos/*.jpg, writes thumbs/.
set -euo pipefail

mkdir -p thumbs
vipsthumbnail photos/*.jpg --size 400x400 --smartcrop attention \
  -o "thumbs/%s.webp[Q=80,strip]"

echo "made $(ls thumbs/*.webp | wc -l) thumbnails"
