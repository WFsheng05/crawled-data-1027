#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
two_scopes_final.py — 最严 / 最宽 两档最终数据

最严 = stance_fixed.csv 的可核实结果（7,350 / 422）
最宽 = 对剩余中立再外推（抽样 50 条中 5 条实为冲官方 → 约 10%）
"""
import csv
import json
import re
import random
import sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BR = re.compile(r'\[[^\]]{1,14}\]')
P = re.compile(r'[\s，。！？、；：""' + "''" +
               r'（）《》【】…—～·,.!?;:"\'()\[\]{}<>~`@#$%^&*+=|\\/_\-\u200b\ufe0f‼️]+')


def c(s):
    return P.sub('', BR.sub('', s or ''))


WELCOME = re.compile(r'欢迎上岛|塔子姐.{0,4}欢迎|塔姐.{0,4}欢迎|'
                     r'塔露拉.{0,4}欢迎|欢迎.{0,4}上岛|终于上岛了')

# 最宽：把疑似、轻微、间接的全部算入
WIDE_CRIT = re.compile(
    r'难绷|绷|离谱|逆天|绝了|服了|无语|麻了|笑死|什么鬼|啥玩意|就这|'
    r'认真的吗|抽象|难评|一言难尽|这也叫|太过分|'
    r'阿一古|阿一占|断手|断臂|没手|少只手|残疾人|残废|义肢|假肢|截肢|断肢|'
    r'心疼|意难平|太惨了|可惜|遗憾|不该|差|烂|弱|废|丑|崩|敷衍|失望|难受|'
    r'不吃攻速|攻击力加成只有|这怎么上|值得更好|符合.{0,6}期待|'
    r'放六年前|新神已至|应有尽有|这样的结局|得改|该加强|必须加强|建议加强|'
    r'强度|数值|机制|倍率|法穿|总伤|回转|技能|天赋|模组|陪跑|借过|'
    r'鹰角|yj|设计师|策划|官方|加强|削弱|重做|改机制|'
    r'孝子|洗地|强度区|捂嘴|青蒜|堵嘴|扣帽子|'
    r'鹰八分钱|有感觉吗|有说法吗|差强人意|什么意思|'
    r'反对.{0,6}上岛|战犯|虐杀|滥杀')
WIDE_SUP = re.compile(r'评论区.{0,10}(乱|魔怔|烦|没法看)|戾气|乌烟瘴气|'
                      r'不想看|都是.{0,6}(刷|机器人)|来来回回都是那几个|'
                      r'别把舟冲关服|心累|'
                      r'(才|只有|半天才|两天了才)\s*\d+\s*[wW万]|'
                      r'这力度.{0,4}不行|你们这.{0,6}不行|杂鱼|史官来截图|'
                      r'强度没问题|并不弱|够用了|没必要加强|相信鹰角|相信yj|'
                      r'复刻银灰|银灰节奏|银灰厨')


def main():
    stance, counts, silver = {}, {}, set()
    for r in csv.DictReader(open('stance_fixed.csv', encoding='utf-8-sig')):
        stance[r['mid']] = r['stance']
        counts[r['mid']] = int(r['comment_count'])
        if r['is_silver'] == 'Y':
            silver.add(r['mid'])

    d = json.load(open('full_pv.json', encoding='utf-8'))
    msgs = defaultdict(list)
    for r in d['rows']:
        msgs[r[1]].append(r[3])
    for r in d['subs']:
        msgs[r[2]].append(r[4])

    TOTAL = len(msgs)
    cnt = Counter(stance.values())

    # ===== 最宽：再扫剩余中立 =====
    neutral = [m for m, s in stance.items() if s == '中立']
    extra_crit, extra_sup, stay = set(), set(), set()
    welcome_set = set()

    for mid in neutral:
        texts = [c(m) for m in msgs[mid] if c(m).strip()]
        if texts and all(WELCOME.search(t) for t in texts):
            welcome_set.add(mid)
            stay.add(mid)
            continue
        crit = sup = False
        for t in texts:
            if WIDE_SUP.search(t):
                sup = True
            elif WIDE_CRIT.search(t):
                crit = True
        if sup:
            extra_sup.add(mid)
        elif crit:
            extra_crit.add(mid)
        else:
            stay.add(mid)

    strict_c, strict_s = cnt['冲官方'], cnt['支持官方']
    wide_c = strict_c + len(extra_crit)
    wide_s = strict_s + len(extra_sup)
    wide_n = len(stay)

    print("=" * 80)
    print(f"全量用户: {TOTAL:,} 人")
    print("=" * 80)
    print(f"\n{'口径':<16}{'冲官方':>12}{'支持官方':>12}{'中立':>10}{'无实质':>9}")
    print("-" * 60)
    print(f"{'最严（可核实）':<16}{strict_c:>12,}{strict_s:>12,}"
          f"{cnt['中立']:>10,}{cnt['无实质']:>9,}")
    print(f"{'最宽（含外推）':<16}{wide_c:>12,}{wide_s:>12,}"
          f"{wide_n:>10,}{cnt['无实质']:>9,}")

    print(f"\n{'占比':<16}{'冲官方':>12}{'支持官方':>12}")
    print("-" * 42)
    print(f"{'最严':<16}{strict_c/TOTAL:>11.1%}{strict_s/TOTAL:>12.1%}")
    print(f"{'最宽':<16}{wide_c/TOTAL:>11.1%}{wide_s/TOTAL:>12.1%}")

    print(f"\n  最严 冲:支持 = {strict_c/max(strict_s,1):.1f} : 1")
    print(f"  最宽 冲:支持 = {wide_c/max(wide_s,1):.1f} : 1")

    # 有效分母
    valid = TOTAL - cnt['无实质'] - len(welcome_set)
    print("\n" + "=" * 80)
    print(f"【有效分母口径】去掉无实质 {cnt['无实质']} + 欢迎上岛 {len(welcome_set)}")
    print("=" * 80)
    print(f"  有效发言者: {valid:,} 人")
    print(f"  最严  冲 {strict_c:,} ({strict_c/valid:.1%})  "
          f"支持 {strict_s:,} ({strict_s/valid:.1%})")
    print(f"  最宽  冲 {wide_c:,} ({wide_c/valid:.1%})  "
          f"支持 {wide_s:,} ({wide_s/valid:.1%})")

    print("\n" + "=" * 80)
    print("【最宽口径新增的冲官方 · 样本】")
    print("=" * 80)
    random.seed(11)
    pool = [(m, msgs[m][0]) for m in extra_crit if msgs[m]]
    for i, (mid, msg) in enumerate(random.sample(pool, min(15, len(pool))), 1):
        print(f"  {i:>2}. 「{msg[:70]}」")

    with open('two_scopes.csv', 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['mid', 'strict', 'wide', 'comment_count', 'is_silver'])
        for mid, s in stance.items():
            ws = s
            if mid in extra_crit:
                ws = '冲官方'
            elif mid in extra_sup:
                ws = '支持官方'
            w.writerow([mid, s, ws, counts.get(mid, 0),
                        'Y' if mid in silver else ''])
    print(f"\n导出 two_scopes.csv")


if __name__ == '__main__':
    main()
