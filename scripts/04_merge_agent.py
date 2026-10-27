#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
final_clean.py — 完全尊重子代理判定，不做任何覆盖

规则：
  1. 子代理判 A → 冲官方
  2. 子代理判 B → 支持官方
  3. 子代理判 C → 保持中立（不再用规则二次判定）
  4. 子代理未覆盖的用户（非中立池）→ 用规则判定结果
"""
import csv
import json
import os
import sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.abspath(__file__))


def main():
    # 子代理判定
    agent = {}
    for i in range(1, 6):
        p = os.path.join(BASE, 'batches', f'result{i}.tsv')
        if not os.path.exists(p):
            print(f"[!] 缺少 {p}")
            continue
        n = 0
        for line in open(p, encoding='utf-8'):
            parts = line.rstrip('\n').split('\t')
            if len(parts) >= 2 and parts[1].strip().upper() in ('A', 'B', 'C'):
                agent[parts[0].strip()] = parts[1].strip().upper()
                n += 1
        print(f"  result{i}: {n} 条")

    ac = Counter(agent.values())
    print(f"\n子代理原始判定: A={ac['A']}  B={ac['B']}  C={ac['C']}  共 {len(agent)}")

    # 基础立场表（规则判定）
    base = {}
    counts = {}
    for r in csv.DictReader(open(os.path.join(BASE, 'stance_fixed.csv'),
                                 encoding='utf-8-sig')):
        base[r['mid']] = r['stance']
        counts[r['mid']] = int(r['comment_count'])

    # 应用：子代理优先，C 保持中立
    stance = dict(base)
    applied_a = applied_b = 0
    for mid, lab in agent.items():
        if mid not in stance:
            continue
        if lab == 'A':
            if stance[mid] != '冲官方':
                applied_a += 1
            stance[mid] = '冲官方'
        elif lab == 'B':
            if stance[mid] != '支持官方':
                applied_b += 1
            stance[mid] = '支持官方'
        # C → 不改动，保持原状（若原来是中立就是中立）

    cnt = Counter(stance.values())
    TOTAL = sum(cnt.values())

    print("\n" + "=" * 76)
    print("【完全尊重子代理判定的最终数据】")
    print("=" * 76)
    print(f"  子代理改判为 A: {applied_a:,} 人")
    print(f"  子代理改判为 B: {applied_b:,} 人")
    print()
    for k in ['冲官方', '支持官方', '中立', '无实质']:
        print(f"  {k:<8}: {cnt[k]:>6,} 人   {cnt[k]/TOTAL:>6.1%}")
    print(f"  {'合计':<8}: {TOTAL:>6,} 人")
    print(f"\n  冲官方 : 支持官方 = {cnt['冲官方']/max(cnt['支持官方'],1):.1f} : 1")

    valid = TOTAL - cnt['无实质']
    print(f"\n【有效分母 {valid:,}】")
    print(f"  冲官方 {cnt['冲官方']:,} ({cnt['冲官方']/valid:.1%})  "
          f"支持官方 {cnt['支持官方']:,} ({cnt['支持官方']/valid:.1%})  "
          f"中立 {cnt['中立']:,} ({cnt['中立']/valid:.1%})")

    # 校验：子代理判 C 的是否都还是中立
    bad = []
    for mid, lab in agent.items():
        if lab == 'C' and stance.get(mid) in ('冲官方', '支持官方'):
            bad.append(mid)
    print(f"\n【校验】子代理判 C 但被归入立场的人数: {len(bad)}  "
          f"（应为 0）")

    with open(os.path.join(BASE, 'stance_final.csv'), 'w',
              encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['mid', 'stance', 'comment_count', 'from_agent'])
        for mid, s in stance.items():
            w.writerow([mid, s, counts.get(mid, 0),
                        'Y' if mid in agent else ''])
    print(f"\n导出 stance_final.csv")


if __name__ == '__main__':
    main()
