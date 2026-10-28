#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""merge_all.py — 合并主评论 + 楼中楼"""
import glob
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r"C:\total workspace\Deepseek harness\one\bili_crawl"
PARTS = os.path.join(BASE, 'parts2')
OUT = os.path.join(BASE, 'full_pv_1028.json')

META = {"aid": 117494736158923, "pages": 5642, "allCount": 194820,
        "note": "2026-10-28 re-crawl, mode=2, ps=30"}


def load(prefix):
    rows, bad = [], 0
    for f in sorted(glob.glob(os.path.join(PARTS, f'{prefix}*.ndjson'))):
        with open(f, encoding='utf-8') as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    bad += 1
    return rows, bad


def main():
    main_rows, b1 = load('m')
    sub_rows, b2 = load('s')
    # t 开头是主评论尾部
    tail_rows, b3 = load('t')
    main_rows += tail_rows

    seen = set()
    uniq = []
    for r in main_rows:
        if r[0] in seen:
            continue
        seen.add(r[0])
        uniq.append(r)

    seen2 = set()
    uniq2 = []
    for r in sub_rows:
        if r[0] in seen2:
            continue
        seen2.add(r[0])
        uniq2.append(r)

    print(f"主评论: {len(uniq):,} 条 (解析失败 {b1+b3})")
    print(f"楼中楼: {len(uniq2):,} 条 (解析失败 {b2})")
    print(f"合计  : {len(uniq)+len(uniq2):,} 条")

    users = set(r[1] for r in uniq) | set(r[2] for r in uniq2)
    print(f"独立用户: {len(users):,} 人")

    data = {
        "meta": {**META, "rows": len(uniq)},
        "subMeta": {"rows": len(uniq2), "roots": 7995},
        "rows": uniq,
        "subs": uniq2,
    }
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    print(f"\n已写出: {OUT} ({os.path.getsize(OUT)/1024/1024:.1f} MB)")


if __name__ == '__main__':
    main()
