#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dual_metrics.py — SOP v1.1：双口径并报 + 结构指标 + 组织化物证
"""
import csv
import json
import re
import sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r"C:\total workspace\Deepseek harness\one\bili_crawl"


def gini(values):
    v = sorted(values)
    n = len(v)
    if n == 0:
        return 0.0
    s = sum(v)
    if s == 0:
        return 0.0
    cum = 0
    for i, x in enumerate(v, 1):
        cum += i * x
    return (2 * cum) / (n * s) - (n + 1) / n


def main():
    stance = {}
    for r in csv.DictReader(open(f'{BASE}/stance_1028.csv', encoding='utf-8-sig')):
        stance[r['mid']] = r['stance']

    d = json.load(open(f'{BASE}/full_pv_1028.json', encoding='utf-8'))
    msgs = defaultdict(list)
    for r in d['rows']:
        msgs[r[1]].append(r[3])
    for r in d['subs']:
        msgs[r[2]].append(r[4])

    TOTAL = len(stance)
    per = {m: len(v) for m, v in msgs.items()}
    total_comments = sum(per.values())

    cnt = Counter(stance.values())

    # ===== 双口径 =====
    print("=" * 76)
    print("【双口径并报】（SOP v1.1 · 4.1.1）")
    print("=" * 76)
    print(f"\n{'口径':<24}{'批评者':>12}{'支持者':>12}{'中立':>12}")
    print("-" * 62)

    # 人头口径
    print(f"{'按独立用户（一人一票）':<24}"
          f"{cnt['冲官方']/TOTAL:>11.1%}{cnt['支持官方']/TOTAL:>12.1%}"
          f"{cnt['中立']/TOTAL:>12.1%}")

    # 声量口径
    vol = Counter()
    for m, s in stance.items():
        vol[s] += per.get(m, 0)
    print(f"{'按评论条数（原始声量）':<24}"
          f"{vol['冲官方']/total_comments:>11.1%}"
          f"{vol['支持官方']/total_comments:>12.1%}"
          f"{vol['中立']/total_comments:>12.1%}")

    print(f"\n  人头比 冲:支持 = {cnt['冲官方']/max(cnt['支持官方'],1):.1f} : 1")
    print(f"  声量比 冲:支持 = {vol['冲官方']/max(vol['支持官方'],1):.1f} : 1")

    # ===== 结构指标 =====
    print("\n" + "=" * 76)
    print("【结构指标】")
    print("=" * 76)
    vals = list(per.values())
    g = gini(vals)
    med = sorted(vals)[len(vals) // 2]
    one_only = sum(1 for x in vals if x == 1)
    print(f"  基尼系数        : {g:.3f}")
    print(f"  中位数发帖      : {med} 条")
    print(f"  只发 1 条的用户 : {one_only:,} 人（{one_only/TOTAL:.1%}）")
    print(f"  总评论          : {total_comments:,} 条")
    print(f"  人均            : {total_comments/TOTAL:.1f} 条")

    # 批评者内部分层
    print("\n  批评者内部分层：")
    crit = [m for m in stance if stance[m] == '冲官方']
    tiers = [(1, 1, '只发 1 条'), (2, 9, '2-9 条'),
             (10, 99, '10-99 条'), (100, 10**9, '≥100 条')]
    for lo, hi, lb in tiers:
        g2 = [m for m in crit if lo <= per.get(m, 0) <= hi]
        cm = sum(per.get(m, 0) for m in g2)
        print(f"    {lb:<12}{len(g2):>6,} 人  "
              f"{len(g2)/len(crit):>6.1%}  →  "
              f"{cm:>7,} 条  {cm/vol['冲官方']:>6.1%} 声量")

    # ===== 组织化物证 =====
    print("\n" + "=" * 76)
    print("【组织化物证扫描】（SOP v1.1 · 4.2.1）")
    print("=" * 76)

    tail_noise = re.compile(r'[a-z]{6,}\s*$')
    copy_cmd = re.compile(r'复制我这个|加上乱码|从别的评论区搬|复制这段|直接复制')
    silver = re.compile(r'复刻银灰|银灰.{0,6}复刻|银灰.{0,4}剧本|又是一?个银灰|'
                        r'银灰节奏|去年银灰|百万银灰|银灰厨')

    n_noise = n_cmd = n_silver = 0
    samples = {'noise': [], 'cmd': [], 'silver': []}
    for r in d['rows']:
        t = r[3] or ''
        if tail_noise.search(t):
            n_noise += 1
            if len(samples['noise']) < 3:
                samples['noise'].append(t[:70])
        if copy_cmd.search(t):
            n_cmd += 1
            if len(samples['cmd']) < 3:
                samples['cmd'].append(t[:70])
        if silver.search(t):
            n_silver += 1
            if len(samples['silver']) < 3:
                samples['silver'].append(t[:70])

    print(f"  尾部随机乱码（规避折叠）: {n_noise:,} 条")
    for s in samples['noise']:
        print(f"    「{s}」")
    print(f"  含复制指令              : {n_cmd:,} 条")
    for s in samples['cmd']:
        print(f"    「{s}」")
    print(f"  「银灰剧本」类          : {n_silver:,} 条")

    # 预制同文簇
    txt_count = Counter(r[3] for r in d['rows'] if r[3] and len(r[3]) > 60)
    big = [(t, c) for t, c in txt_count.most_common(5) if c >= 30]
    print(f"\n  预制长文案同文簇（≥30 次）：")
    for t, c in big:
        print(f"    {c:>4} 次  「{t[:60]}」")

    # 导出
    out = {
        "date": "2026-10-28",
        "total_users": TOTAL,
        "total_comments": total_comments,
        "head_count": {k: cnt[k] for k in ['冲官方', '支持官方', '中立', '无实质']},
        "volume": {k: vol[k] for k in ['冲官方', '支持官方', '中立', '无实质']},
        "gini": round(g, 4),
        "median_posts": med,
        "one_post_only": one_only,
        "org_evidence": {
            "tail_noise": n_noise,
            "copy_command": n_cmd,
            "silver_script": n_silver,
            "prefab_clusters": [{"text": t[:80], "count": c} for t, c in big],
        },
    }
    with open(f'{BASE}/metrics_1028.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"\n导出 metrics_1028.json")


if __name__ == '__main__':
    main()
