#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
official_final.py — 指向官方的两组口径（最终修正版）

关键修正：
  「孝子 / 洗地 / 强度区 / 也够 / 理中客 / 精神股东」这些词，
  是**冲锋方骂护官方者**的话术，本身就是在支持冲官方。
  所以它们不是"内战噪声"，而是**指向官方的攻击性表达**，应当计入。

真正该剔除的只有：
  · 反冲锋方：骂冲的人（百万塔厨/节奏狗/看戏/闹麻/游戏而已）
"""
import csv
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BR = re.compile(r'\[[^\]]{1,14}\]')
P = re.compile(r'[\s，。！？、；：""' + "''" +
               r'（）《》【】…—～·,.!?;:"\'()\[\]{}<>~`@#$%^&*+=|\\/_\-\u200b\ufe0f‼️]+')


def c(s):
    return P.sub('', BR.sub('', s or ''))


# ---------- 指向官方 ----------
OFFICIAL = re.compile(
    r'鹰角|yjwl|yj|YJ|海猫|设计师|策划|官方|丫丁|sjs|'
    r'加强|削弱|重做|改机制|回调|调整|优化|增强|修改|'
    r'还我|救救|把手还回来|修墙|'
    r'强度|数值|膨胀|抑制|天花板|超模|法穿|点伤|总伤|dps|DPS|回转|'
    r'技能|天赋|模组|专精|满潜|倍率|刮痧|初始技力|二技能|三技能|一技能|'
    r'断臂|断手|失臂|立绘|小人|模型|人设|塑造|剧情|文案|吃书|'
    r'限定|常驻|池子|抽卡|吃相|圈钱|骗氪|逼氪|'
    r'内部恨|内部爱|区别对待|后妈|'
    r'原始人|下水道|垫底|白给|泯|疲软|拉胯|残废|敷衍|摆烂|做废'
)

# ---------- 冲锋方话术（计入！支持冲官方）----------
PRO_BRIGADE = re.compile(
    r'孝子|洗地|强度区|mmr|MMR|也够|理中客|精神股东|股东|'
    r'卫兵|狗腿|好狗|舔|护主|洗白|'
    r'捂嘴|别装死|装死|青蒜|清算'
)

# ---------- 反冲锋方（剔除）----------
ANTI_BRIGADE = re.compile(
    r'百万塔厨|百万.{0,4}厨|只有.{0,8}个人|就这么点人|'
    r'闹麻|闹斯特麻麻|节奏狗|魔怔|'
    r'看戏|吃瓜|你们继续|吵起来|打起来|保留节目|'
    r'不就一个游戏|游戏而已|至于吗|多大点事|'
    r'别冲了|消停点吧|停一停|玻璃心|戏多'
)


def main():
    rows = list(csv.DictReader(open('contextual_v2.csv', encoding='utf-8-sig')))
    neg = [r for r in rows if r['label'] == '负面']
    print(f"contextual_v2 判为负面: {len(neg):,} 条")

    kept = []
    d_anti = d_none = 0
    prohit = 0

    for r in neg:
        x = c(r['message'])
        if ANTI_BRIGADE.search(x):
            d_anti += 1
            continue
        is_off = bool(OFFICIAL.search(x))
        is_pro = bool(PRO_BRIGADE.search(x))
        if is_pro and not is_off:
            prohit += 1
        if is_off or is_pro:          # 指向官方 或 用冲锋话术骂护官方者
            kept.append(r)
        else:
            d_none += 1

    print(f"  剔除反冲锋方: {d_anti:,} 条")
    print(f"  计入（含骂孝子/洗地/强度区）: {prohit:,} 条")
    print(f"  其它无关: {d_none:,} 条")
    print(f"保留: {len(kept):,} 条")

    per = Counter(r['mid'] for r in kept)
    wide = set(per)
    strict = {m for m, n in per.items() if n >= 2}
    TOTAL = 16225

    print("\n" + "=" * 64)
    print("【指向官方 · 最宽】至少 1 条")
    print(f"  {len(wide):,} 人 = {len(wide)/TOTAL:.1%}")
    print("\n【指向官方 · 最严】至少 2 条")
    print(f"  {len(strict):,} 人 = {len(strict)/TOTAL:.1%}")
    print("=" * 64)

    print("\n【条数分布】")
    for lo, hi, lb in [(1, 1, '1 条'), (2, 2, '2 条'), (3, 5, '3-5 条'),
                       (6, 10, '6-10 条'), (11, 30, '11-30 条'),
                       (31, 100, '31-100 条'), (101, 10 ** 9, '101+ 条')]:
        g = [m for m in per if lo <= per[m] <= hi]
        print(f"  {lb:<10}{len(g):>7,} 人   合计 {sum(per[m] for m in g):>7,} 条")

    with open('official_final.csv', 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['mid', 'uname', 'message', 'tier'])
        for r in kept:
            w.writerow([r['mid'], r['uname'], r['message'],
                        'strict' if r['mid'] in strict else 'wide_only'])
    print(f"\n导出 official_final.csv（{len(kept):,} 行）")

    print("\n=== 含「孝子/洗地/强度区」的样本 ===")
    k = 0
    for r in kept:
        if PRO_BRIGADE.search(c(r['message'])) and not OFFICIAL.search(c(r['message'])):
            print(f"  「{r['message'][:66]}」")
            k += 1
            if k >= 10:
                break


if __name__ == '__main__':
    main()
