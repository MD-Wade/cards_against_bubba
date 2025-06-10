#!/usr/bin/env python3
import os
import json
import argparse
from pathlib import Path

import zstandard as zstd

def process_json_file(src_path: Path, dst_path: Path):
    # read original
    orig_bytes = src_path.read_bytes()
    orig_size = len(orig_bytes)

    # minify
    data = json.loads(orig_bytes.decode('utf-8'))
    minified = json.dumps(data, separators=(',',':'), ensure_ascii=False).encode('utf-8')
    min_size = len(minified)

    # ensure output dir
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    # compress with Zstd
    cctx = zstd.ZstdCompressor(level=22)
    comp = cctx.compress(minified)
    comp_size = len(comp)

    comp_path = dst_path.with_suffix(dst_path.suffix + '.zst')
    comp_path.write_bytes(comp)

    return orig_size, min_size, comp_size

def human_fmt(n: int):
    for unit in ['B','KB','MB','GB']:
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"

def main():
    p = argparse.ArgumentParser(
        description="Minify JSON from data_raw → data, compress with .zst, report ratios."
    )
    p.add_argument('-i','--input-dir', default='data_raw')
    p.add_argument('-o','--output-dir', default='data')
    args = p.parse_args()

    total_orig = total_min = total_comp = 0
    print(f"{'FILE':60}  {'orig':>9}  {'min':>9}  {'min%':>6}  {'zst':>9}  {'zst%':>6}")
    print("-"*100)

    for dirpath, _, files in os.walk(args.input_dir):
        for fn in files:
            if fn.lower().endswith('.json'):
                src = Path(dirpath)/fn
                rel = src.relative_to(args.input_dir)
                dst = Path(args.output_dir)/rel

                o,m,c = process_json_file(src, dst)
                total_orig+=o; total_min+=m; total_comp+=c

                print(f"{str(rel):60}  {human_fmt(o):>9}  {human_fmt(m):>9}  {(m/o):>5.1%}  {human_fmt(c):>9}  {(c/o):>5.1%}")

    print("\nOverall:")
    print(f"  Total orig = {human_fmt(total_orig)}, "
          f"minified = {human_fmt(total_min)} ({total_min/total_orig:.1%}), "
          f"zst = {human_fmt(total_comp)} ({total_comp/total_orig:.1%})")

if __name__=='__main__':
    main()
