#!/bin/bash

set -euo pipefail

temp_dir=$(mktemp -d)
cleanup() {
    echo "Cleaning temporary directory $temp_dir" >&2
    rm -rf "$temp_dir"
}
trap cleanup EXIT

sizes=(16 32 48 128 256)
png_paths=()
for size in "${sizes[@]}"; do
    png_path="$temp_dir/lidske-aktivity-$size.png"
    echo "Writing $png_path" >&2
    rsvg-convert -w "$size" -h "$size" data/lidske-aktivity.svg > "$png_path"
    png_paths+=("$png_path")
done

echo "Writing lidske-aktivity.ico" >&2
magick convert "${png_paths[@]}" -colors 256 data/lidske-aktivity.ico

echo "Done" >&2
