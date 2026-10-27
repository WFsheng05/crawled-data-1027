#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
final_count.py — 最终统计（不剔除 >100 条，全部按用户计入）

规则：
  1. >100 条的 261 个账号：不剔除、不合并，逐个计入「冲官方」
  2. 其余用户按「只要有任一条评论是冲官方信号」即归入冲官方
  3. 每个用户只归一类，互斥

优先级：冲官方 > 支持官方 > 中立 > 无实质
"""
import csv
import json
import re
import sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BR = re.compile(r'\[[^\]]{1,14}\]')
P = re.compile(r'[\s，。！？、；：""' + "''" +
               r'（）《》【】…—～·,.!?;:"\'()\[\]{}<>~`@#$%^&*+=|\\/_\-\u200b\ufe0f‼️]+')


def c(s):
    return P.sub('', BR.sub('', s or ''))


CRIT = re.compile(
    r'鹰角|yjwl|yj|YJ|海猫|设计师|策划|官方|丫丁|sjs|鹰小姐|'
    r'加强|削弱|重做|改机制|回调|优化|还我|救救|修墙|改改|'
    r'敷衍|摆烂|做废|垃圾|恶心|失望|离谱|无语|拉胯|疲软|残废|'
    r'膨胀|抑制|超模|天花板|毒点|下毒|'
    r'断臂|断手|失臂|立绘|人设|塑造|写崩|吃书|'
    r'圈钱|吃相|骗氪|逼氪|割韭菜|内部恨|内部爱|区别对待|后妈|'
    r'原始人|下水道|垫底|白给|'
    r'凭什么|为什么|这也叫|什么玩意|问心有愧|不应该|不该|可惜|遗憾|宁愿|哭坟|青蒜|'
    r'强度|数值|机制|倍率|法穿|点伤|总伤|dps|DPS|回转|技能|天赋|模组|'
    r'吃拐|超大上|超大杯|中杯|借过|陪跑|看齐|和银灰|不如|弱|废|差|烂|'
    r'致敬|太有面子|美美|装大方|笑死|呵呵|典|赢麻|神了|也够|'
    r'孝子|洗地|强度区|理中客|精神股东|捂嘴|别装死|装死|堵嘴|扣帽子|'
    r'差强人意|有感觉吗|有说法吗')

SUPPORT = re.compile(r'强度没问题|并不弱|不弱啊|够用了|日常够用|可以接受|没必要加强|'
                     r'已经很好了|挺好用|实际很强|被低估|不会用而已|吃拐很强|'
                     r'相信鹰角|相信yj|认可|设计得很好|做得不错|好评|用心了|'
                     r'理性看待|别带节奏|别跟风|不要瞎冲|没必要冲|'
                     r'感谢鹰角|谢谢鹰角|辛苦了|很满意|真香')
IRONY = re.compile(r'也够|太有面子|美美|汤圆|喜极而泣|😅|🙄|😂|🤣|'
                   r'典|赢麻|神了|笑死|呵呵|致敬|恭喜|断手|断臂|小皇帝|陪跑')
ANTI = re.compile(r'百万塔厨|百万.{0,4}厨|只有.{0,8}个人|就这么点人|闹麻|'
                  r'节奏狗|魔怔|看戏|吃瓜|你们继续|吵起来|打起来|'
                  r'不就一个游戏|游戏而已|至于吗|多大点事|别冲了|消停点吧|'
                  r'魔怔厨|不理智冲|名声')
SILVER = re.compile(r'复刻银灰|银灰.{0,6}复刻|银灰.{0,4}剧本|又是一个银灰|'
                    r'银灰那时候|银灰那次|银灰节奏|去年银灰|银灰事件|'
                    r'百万银灰|银灰厨|老剧本|历史重演|又来一遍|和银灰一样|跟银灰一样')
SILVER_CRITIC = re.compile(r'为什么都在说|一说弱就是|按头爱恨|扣.{0,4}帽|'
                           r'有理有据.{0,8}不看|反驳.{0,10}银灰|说不出来|被说成|岁成银灰')

NOISE = re.compile(r'^许愿|许愿|出必还愿|保底|十连|抽到|抽中|欧气|'
                   r'群号|进群|加群|关注我|主页|直播间|频道|'
                   r'请问|求教|萌新|新手|大佬推荐|该不该抽|要不要抽|'
                   r'阿一古|马头|类魂|武松|格斯')


def main():
    d = json.load(open('full_pv.json', encoding='utf-8'))
    msgs = defaultdict(list)
    for r in d['rows']:
        msgs[r[1]].append(r[3])
    for r in d['subs']:
        msgs[r[2]].append(r[4])

    TOTAL = len(msgs)
    spam = {m for m, v in msgs.items() if len(v) > 100}

    stance = {}
    for mid, arr in msgs.items():
        if mid in spam:
            stance[mid] = '冲官方'          # >100 条：全部计冲官方
            continue
        is_crit = is_sup = False
        has_sub = False
        for msg in arr:
            x = c(msg)
            if not x.strip() or x.isdigit():
                continue
            has_sub = True
            if ANTI.search(x):
                continue
            if SILVER.search(x) and not SILVER_CRITIC.search(x):
                is_sup = True
                continue
            if SUPPORT.search(x) and not IRONY.search(x):
                is_sup = True
                continue
            if CRIT.search(x):
                is_crit = True
        if is_crit:
            stance[mid] = '冲官方'
        elif is_sup:
            stance[mid] = '支持官方'
        elif not has_sub:
            stance[mid] = '无实质'
        else:
            stance[mid] = '中立'

    cnt = Counter(stance.values())
    print("=" * 76)
    print(f"全量用户: {TOTAL:,} 人（>100 条的 {len(spam)} 个账号全部计入冲官方，不剔除）")
    print("=" * 76)
    for k in ['冲官方', '支持官方', '中立', '无实质']:
        print(f"  {k:<8}: {cnt[k]:>6,} 人   {cnt[k]/TOTAL:>6.1%}")
    print(f"  {'合计':<8}: {sum(cnt.values()):>6,} 人")

    print("\n" + "=" * 76)
    print("【关键比例】")
    print(f"  冲官方 : 支持官方 = {cnt['冲官方']/max(cnt['支持官方'],1):.1f} : 1")
    print(f"  冲官方占全量     = {cnt['冲官方']/TOTAL:.1%}")
    print(f"  支持官方占全量   = {cnt['支持官方']/TOTAL:.1%}")
    print("=" * 76)

    # 含/不含刷屏号的对比
    nospam = {m: s for m, s in stance.items() if m not in spam}
    c2 = Counter(nospam.values())
    print("\n【若剔除 >100 条账号（对照）】")
    print(f"  冲官方   : {c2['冲官方']:>6,} 人  {c2['冲官方']/len(nospam):>6.1%}")
    print(f"  支持官方 : {c2['支持官方']:>6,} 人  {c2['支持官方']/len(nospam):>6.1%}")
    print(f"  分母     : {len(nospam):,} 人")

    with open('final_stance.csv', 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['mid', 'stance', 'comment_count', 'is_spam'])
        for mid, s in stance.items():
            w.writerow([mid, s, len(msgs[mid]), 'Y' if mid in spam else ''])
    print(f"\n导出 final_stance.csv（{TOTAL:,} 行）")


if __name__ == '__main__':
    main()
