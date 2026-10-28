#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""merge_rejudge2.py — 合并 10 批重判结果 + 校验"""
import csv
import glob
import os
import sys
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = os.path.dirname(os.path.abspath(__file__))


def main():
    verdict = {}
    per = {}
    problems = []

    for i in range(1, 11):
        src = os.path.join(BASE, 'rejudge2', f'r{i}.txt')
        out = os.path.join(BASE, 'rejudge2', f'v{i}.tsv')

        # 输入 mid
        src_mids = []
        with open(src, encoding='utf-8') as f:
            for line in f:
                if '\t' in line:
                    src_mids.append(line.split('\t')[0].strip())

        # 输出
        rows = []
        bad_fmt = 0
        with open(out, encoding='utf-8') as f:
            for line in f:
                p = line.rstrip('\n').split('\t')
                if len(p) < 2 or p[1].strip().upper() not in ('A', 'B', 'C'):
                    bad_fmt += 1
                    continue
                rows.append((p[0].strip(), p[1].strip().upper()))

        miss = set(src_mids) - {r[0] for r in rows}
        extra = {r[0] for r in rows} - set(src_mids)
        dup = len(rows) - len({r[0] for r in rows})
        c = Counter(r[1] for r in rows)
        per[i] = (len(rows), c, len(miss), len(extra), dup, bad_fmt)

        if miss or extra or dup or bad_fmt or len(rows) != len(src_mids):
            problems.append(f"v{i}: 输入{len(src_mids)} 输出{len(rows)} 缺{len(miss)} 多{len(extra)} 重{dup} 格式{bad_fmt}")

        for mid, lab in rows:
            verdict[mid] = lab

    print("=" * 72)
    print("【10 批重判汇总】")
    print("=" * 72)
    tot = Counter()
    for i in sorted(per):
        n, c, miss, extra, dup, bf = per[i]
        print(f"  v{i:<2}: {n:>4} 条   A={c['A']:>3}  B={c['B']:>3}  C={c['C']:>4}"
              f"   {'OK' if not(miss or extra or dup or bf) else '⚠'}")
        for k, v in c.items():
            tot[k] += v
    print(f"\n  合计: A={tot['A']}  B={tot['B']}  C={tot['C']}  共 {sum(tot.values())}")

    if problems:
        print("\n【问题】")
        for p in problems:
            print("  " + p)
    else:
        print("\n✅ 全部校验通过：无缺失、无重复、无错位")

    # 应用
    stance, counts = {}, {}
    for r in csv.DictReader(open(os.path.join(BASE, 'final_stance.csv'),
                                 encoding='utf-8-sig')):
        stance[r['mid']] = r['stance']
        counts[r['mid']] = int(r['comment_count'])

    changed = 0
    for mid, lab in verdict.items():
        if stance.get(mid) != '中立':
            continue
        if lab == 'A':
            stance[mid] = '冲官方'
            changed += 1
        elif lab == 'B':
            stance[mid] = '支持官方'
            changed += 1

    cnt = Counter(stance.values())
    TOTAL = sum(cnt.values())

    print("\n" + "=" * 72)
    print("【最终数据 · 2026-10-28】")
    print("=" * 72)
    for k in ['冲官方', '支持官方', '中立', '无实质']:
        print(f"  {k:<8}: {cnt[k]:>6,} 人   {cnt[k]/TOTAL:>6.1%}")
    print(f"  {'合计':<8}: {TOTAL:>6,} 人")
    print(f"\n  冲官方 : 支持官方 = {cnt['冲官方']/max(cnt['支持官方'],1):.1f} : 1")
    print(f"  本轮改判: {changed:,} 人")

    valid = TOTAL - cnt['无实质']
    print(f"\n【有效分母 {valid:,}】")
    print(f"  冲官方 {cnt['冲官方']:,} ({cnt['冲官方']/valid:.1%})")
    print(f"  支持官方 {cnt['支持官方']:,} ({cnt['支持官方']/valid:.1%})")
    print(f"  中立 {cnt['中立']:,} ({cnt['中立']/valid:.1%})")

    with open(os.path.join(BASE, 'stance_1028.csv'), 'w',
              encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['mid', 'stance', 'comment_count'])
        for mid, s in stance.items():
            w.writerow([mid, s, counts.get(mid, 0)])
    print(f"\n导出 stance_1028.csv")


if __name__ == '__main__':
    main()
