#!/bin/bash

set -euo pipefail

temp_dir="$(mktemp -d)"
cleanup() {
    echo "Cleaning temporary directory $temp_dir" >&2
    rm -rf "$temp_dir"
}
trap cleanup EXIT

iconset_dir="$temp_dir/LidskeAktivity.iconset"
mkdir -p "$iconset_dir"

# https://stackoverflow.com/a/20703594
sizes=(16 32 64 128 256 512)
png_paths=()
for size in "${sizes[@]}"; do
    png_path="$iconset_dir/icon_${size}x${size}.png"
    echo "Writing $png_path" >&2
    rsvg-convert -w "$size" -h "$size" data/lidske-aktivity.svg > "$png_path"
    png_paths+=("$png_path")
    png_path="$iconset_dir/icon_${size}x${size}@2x.png"
    echo "Writing $png_path" >&2
    rsvg-convert -w "$((size*2))" -h "$((size*2))" data/lidske-aktivity.svg > "$png_path"
    png_paths+=("$png_path")
done

echo "Writing lidske-aktivity.icns" >&2
iconutil -c icns -o data/lidske-aktivity.icns "$iconset_dir"

echo "Done" >&2
