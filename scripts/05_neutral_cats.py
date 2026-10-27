#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
neutral_cats.py — 7,342 条中立言论分类
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


CATS = [
    ('剧情考据/讨论', re.compile(
        r'乌萨斯|内卫|罗德岛|切尔诺伯格|泰拉|黑蛇|爱国者|阿丽娜|切城|'
        r'感染者|整合运动|陛下|殿下|教皇|霜星|雷德|红刀|剧情|设定|'
        r'第八章|主线|时间线|世界观|宿傩|帝王|赎罪')),
    ('玩梗/接龙', re.compile(
        r'阿一古|阿一占|马头|类魂|武松|格斯|白次男|香克斯|码头|健美|'
        r'太刀侠|升龙拳|邪魔|杨过|佐助|只狼|尼禄|山本|普通僵尸|伊利哇啦|'
        r'毅力哇啦|三要素|够童|意气风发|死仇时代|不要去恨|恨火|怒号光明')),
    ('许愿/抽卡', re.compile(
        r'许愿|出必还愿|保底|十连|抽到|抽中|欧气|必出|求求了|保佑我|'
        r'攒井|攒抽|黄票|源石|石头|出货|歪|井')),
    ('宣群/引流', re.compile(
        r'群号|进群|加群|关注我|主页|直播间|频道|友好老群|一起玩|私信|企鹅群')),
    ('排期/时间抱怨', re.compile(
        r'隔.{0,3}周|隔.{0,3}天|才开|什么时候开|何时开|几时开|还要等|等太久|'
        r'等这么久|等了好|排期|活动间隔|太慢|'
        r'11\.1|11月1|几号|什么时候更新|直播好短|前瞻')),
    ('纯提问', re.compile(
        r'请问|求教|萌新|新手|大佬|该不该抽|要不要抽|值不值得|怎么配|'
        r'打不过|卡关|阵容|怎么练|问一下|有没有|什么|怎么|为什么')),
    ('夸PV/画面', re.compile(
        r'好帅|好美|好看|画得|背景|立绘|音乐|BGM|bgm|pv|PV|作画|'
        r'精致|细节|震撼|燃|帅|美|好听|配音|俄语')),
    ('旁观/吃瓜', re.compile(
        r'吃瓜|看戏|围观|不明真相|热闹|前排|路过|什么情况|咋了这是|'
        r'谁解释|评论区|好多人|十万|13w|12w|w了')),
    ('角色喜爱', re.compile(
        r'喜欢|爱了|厨|抽爆|必抽|满潜|心疼|意难平|值得更好|欢迎上岛|'
        r'上岛|塔子姐|塔姐|塔厨')),
    ('纯表情/短句', re.compile(r'^.{0,4}$')),
]


def main():
    stance = {}
    for r in csv.DictReader(open('stance_rejudge.csv', encoding='utf-8-sig')):
        stance[r['mid']] = r['stance']

    d = json.load(open('full_pv.json', encoding='utf-8'))
    msgs = defaultdict(list)
    name = {}
    for r in d['rows']:
        msgs[r[1]].append(r[3]); name.setdefault(r[1], r[2])
    for r in d['subs']:
        msgs[r[2]].append(r[4]); name.setdefault(r[2], r[3])

    neutral = [m for m, s in stance.items() if s == '中立']
    buckets = defaultdict(list)
    unc = []

    for mid in neutral:
        texts = [c(m) for m in msgs[mid] if c(m).strip()]
        if not texts:
            buckets['纯表情/短句'].append(mid)
            continue
        joined = ' '.join(texts)
        if len(joined) <= 4 or joined.isdigit():
            buckets['纯表情/短句'].append(mid)
            continue
        placed = False
        for k, pat in CATS:
            if pat.search(joined):
                buckets[k].append(mid)
                placed = True
                break
        if not placed:
            unc.append(mid)

    total = len(neutral)
    print("=" * 80)
    print(f"中立 {total:,} 人 · 内容分类")
    print("=" * 80)
    for k, _ in CATS:
        arr = buckets.get(k, [])
        if not arr:
            continue
        bar = '█' * int(len(arr) / total * 50)
        print(f"  {k:<12}{len(arr):>6,} 人  {len(arr)/total:>6.1%}  {bar}")
    print(f"  {'其它/零散':<12}{len(unc):>6,} 人  {len(unc)/total:>6.1%}")

    print("\n" + "=" * 80)
    print("【各类样本】")
    print("=" * 80)
    for k, _ in CATS:
        arr = buckets.get(k, [])
        if not arr:
            continue
        print(f"\n-- {k} ({len(arr)} 人) --")
        random.seed(7)
        for mid in random.sample(arr, min(5, len(arr))):
            print(f"  「{msgs[mid][0][:62]}」")

    if unc:
        print(f"\n-- 其它/零散 ({len(unc)} 人) --")
        random.seed(13)
        for mid in random.sample(unc, min(12, len(unc))):
            print(f"  「{msgs[mid][0][:62]}」")

    with open('neutral_cats.csv', 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['category', 'count'])
        for k, _ in CATS:
            w.writerow([k, len(buckets.get(k, []))])
        w.writerow(['其它/零散', len(unc)])


if __name__ == '__main__':
    main()
