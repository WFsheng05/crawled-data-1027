#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""frames5.py — 最终视频（8,132 / 767 / 7,342 + 中立分类）"""
import json
import os
import sys

from PIL import Image, ImageDraw

from engine2 import (W, H, PAPER, INK, INK2, GRAY, LGRAY, RED, ORANGE, BLUE,
                     GREEN, seg, fade, ease_out, tx, tw, num, header, footer,
                     folio, h1, bullet, rule, mix, font)

VIDEO = "BV1fjHP6eECY · 《明日方舟》2026 感谢庆典 PV"
SUB = "数据：B 站公开评论接口 · 2026-10-28 全量抓取"

TOTAL = 18971
CRIT = 9716
SUP = 854
NEU = 8132
NONE = 269
MAINC = 166571
SUBC = 24408
ALLC = 190979
SPAMN = 364
SPAMC = 120116

# 中立分类
NEU_CATS = [
    ("其它零散短评", 3608, 44.4, (158, 158, 158)),
    ("剧情考据/讨论", 1420, 17.5, BLUE),
    ("纯表情/短句", 883, 10.9, (176, 168, 156)),
    ("玩梗/接龙", 504, 6.2, (140, 170, 160)),
    ("纯提问", 451, 5.5, GREEN),
    ("角色喜爱", 385, 4.7, (200, 120, 140)),
    ("许愿/抽卡", 383, 4.7, ORANGE),
    ("夸PV/画面", 345, 4.2, (214, 150, 90)),
    ("排期抱怨", 67, 0.8, (150, 130, 180)),
    ("旁观/吃瓜", 60, 0.7, (120, 144, 156)),
    ("宣群/引流", 26, 0.3, (190, 186, 179)),
]

SHOTS = [
    (0.0,  4.5,  'p01'),
    (4.5,  11.5, 'p02'),
    (11.5, 18.5, 'p03'),
    (18.5, 25.0, 'p04'),
    (25.0, 32.0, 'p05'),
    (32.0, 41.0, 'p06'),
    (41.0, 52.5, 'p06b'),
    (52.5, 59.5, 'p07'),
    (59.5, 67.5, 'p08'),
    (67.5, 74.5, 'p09'),
    (74.5, 82.5, 'p10'),
]
DUR = 82.5


def prog(t):
    return min(1.0, t / DUR)


def s_p01(d, t):
    a = fade(t, 0.0, 4.5, 0.7, 0.5)
    header(d, VIDEO, 1, "开场", a)
    tx(d, (120, 285), "一场十九万条评论的节奏", 82, INK, alpha=a)
    tx(d, (120, 415), "有多少人，真的在表达不满？", 82, RED, alpha=a)
    d.rectangle([120, 545, 198, 553], fill=RED)
    tx(d, (120, 615), "我用 19.1 万条全量评论，重新算了一遍", 42, INK2,
       bold=False, alpha=a)
    tx(d, (120, 695), "一级评论 + 楼中楼 · 覆盖完整度 98.0%", 34, GRAY,
       bold=False, alpha=a)
    footer(d, SUB, "PART 01 / 11", a)
    folio(d, a, prog(t))


def s_p02(d, t):
    a = fade(t, 4.5, 11.5, 0.5, 0.5)
    header(d, VIDEO, 2, "评论数不是关键", a)
    y = h1(d, "评论数，从来不是关键指标", y=170, alpha=a, size=72)

    lx, rx = 120, 1020
    ty = y + 20
    tx(d, (lx, ty), "遇到节奏时，真实发生的是：", 34, INK2, bold=False, alpha=a)
    for i, s in enumerate([
        "同一个人反复刷同一句",
        "少数账号贡献绝大多数评论",
        "评论总量被单点放大",
    ]):
        bullet(d, lx + 8, ty + 70 + i * 70, s, 36, INK, a, ORANGE)

    tx(d, (rx, ty), "于是更严谨的问法是：", 34, INK2, bold=False, alpha=a)
    for i, s in enumerate([
        "有多少「人」参与了表达",
        "他们各自说了几条",
        "剔除刷屏后，还剩多少",
    ]):
        bullet(d, rx + 8, ty + 70 + i * 70, s, 36, INK, a, BLUE)

    rule(d, 700, a)
    tx(d, (120, 740), "评论数衡量的是「声量」", 44, INK, alpha=a)
    tx(d, (760, 752), "→", 44, LGRAY, alpha=a)
    tx(d, (860, 740), "用户数衡量的才是「人」", 44, RED, alpha=a)

    footer(d, SUB, "按用户统计，更严谨", a)
    folio(d, a, prog(t))


def s_p03(d, t):
    a = fade(t, 11.5, 18.5, 0.5, 0.5)
    header(d, VIDEO, 3, "我抓了什么", a)
    y = h1(d, "19.1 万条：一级评论 + 楼中楼", y=170, alpha=a, size=68)

    ny = y + 30
    data = [("一级评论", MAINC, INK), ("楼中楼", SUBC, INK), ("合计", ALLC, RED)]
    for i, (lb, v, col) in enumerate(data):
        x = 120 + i * 600
        tx(d, (x, ny), lb, 30, GRAY, bold=False, alpha=a)
        tx(d, (x, ny + 46), num(t, 12.3 + i * 0.3, 14.4 + i * 0.3, v),
           92, col, alpha=a)

    rule(d, ny + 200, a)
    tx(d, (120, ny + 236), "关键：楼中楼必须算进来", 40, INK, alpha=a)
    for i, s in enumerate([
        "只抓一级评论，会漏掉 6,998 个「只在楼里说话的人」",
        "独立用户数会从 18,971 被低估成 11,973",
        "覆盖率：190,979 / 195,870 = 98.0%",
    ]):
        bullet(d, 128, ny + 306 + i * 66, s, 32, INK2, a, ORANGE)

    footer(d, SUB, "楼中楼未展开 = 漏人", a)
    folio(d, a, prog(t))


def s_p04(d, t):
    a = fade(t, 18.5, 25.0, 0.5, 0.5)
    header(d, VIDEO, 4, "谁在刷屏", a)
    y = h1(d, "364 个账号，发走了 62.9%", y=170, alpha=a, size=72)

    ny = y + 20
    tx(d, (120, ny), "364", 140, ORANGE, alpha=a)
    tx(d, (450, ny + 50), "个账号（占 1.9% 的人）", 36, INK, alpha=a)
    tx(d, (450, ny + 98), "发了 120,116 条评论（62.9%）", 36, INK, alpha=a)
    tx(d, (450, ny + 146), "单人最高：1,585 条", 36, RED, alpha=a)

    bx, by, bw, bh = 120, ny + 230, 1680, 60
    d.rectangle([bx, by, bx + bw, by + bh], fill=(238, 234, 228))
    p = seg(t, 20.0, 21.8)
    w1 = int(bw * 0.558 * ease_out(p))
    if w1 > 2:
        d.rectangle([bx, by, bx + w1, by + bh], fill=mix(PAPER, ORANGE, a))
    if p > 0.3:
        tx(d, (bx + 22, by + 14), "364 个刷屏号", 28, (255, 255, 255), alpha=a)
    if p > 0.7:
        tx(d, (bx + w1 + 22, by + 14), "其余 18,607 人 · 70,863 条", 28,
           INK2, alpha=a)

    rule(d, by + 116, a)
    tx(d, (120, by + 152), "结论：讨论「评论多不多」，等于在讨论「刷得多不多」",
       38, INK, alpha=a)
    tx(d, (120, by + 214), "要看真实态度，必须先按用户去重", 38, RED, alpha=a)

    footer(d, SUB, "364 / 18,971 = 1.9%", a)
    folio(d, a, prog(t))


def s_p05(d, t):
    a = fade(t, 25.0, 32.0, 0.5, 0.5)
    header(d, VIDEO, 5, "排除无实质内容", a)
    y = h1(d, "许愿、宣群、纯表情，先排除", y=170, alpha=a, size=66)

    tx(d, (120, y + 10), "这些发言没有表达任何立场，不能计入任何一方", 32, GRAY,
       bold=False, alpha=a)

    ny = y + 90
    rows = [
        ("许愿 / 抽卡", "「许愿塔露拉，出必还愿」", "383 人"),
        ("纯表情 / 短句", "「[汤圆]」「1」", "883 人"),
        ("宣群 / 引流", "「友好老群，欢迎各位博士来玩」", "26 人"),
        ("纯玩梗", "「阿一古」「马头」", "504 人"),
        ("排期抱怨", "「好痛苦，一定要隔一周才开活动吗」", "67 人"),
    ]
    for i, (k, v, n) in enumerate(rows):
        yy = ny + i * 76
        tx(d, (120, yy), k, 31, RED, alpha=a)
        tx(d, (400, yy), v, 29, INK2, bold=False, alpha=a)
        tx(d, (1560, yy), n, 31, GRAY, alpha=a)

    rule(d, ny + 412, a)
    tx(d, (120, ny + 448), "排除后：18,971 人里，18,702 人有实质表达", 40, INK,
       alpha=a)

    footer(d, SUB, "无立场 ≠ 支持", a)
    folio(d, a, prog(t))


def s_p06(d, t):
    a = fade(t, 32.0, 41.0, 0.5, 0.5)
    header(d, VIDEO, 6, "核心结果", a)
    y = h1(d, "至少接近 1 万人，在表达不满", y=150, alpha=a, size=68)

    ny = y + 40
    tx(d, (120, ny), "冲官方（可核实下限）", 28, GRAY, bold=False, alpha=a)
    tx(d, (120, ny + 44), num(t, 33.0, 35.4, CRIT), 128, RED, alpha=a)
    tx(d, (120, ny + 196), "51.2%", 44, RED, alpha=a)

    tx(d, (900, ny), "支持官方", 32, GRAY, bold=False, alpha=a)
    tx(d, (900, ny + 44), num(t, 33.4, 35.8, SUP), 128, GREEN, alpha=a)
    tx(d, (900, ny + 196), "4.5%", 44, GREEN, alpha=a)

    by = ny + 290
    bx, bw, bh = 120, 1680, 64
    d.rectangle([bx, by, bx + bw, by + bh], fill=(238, 234, 228))
    p = seg(t, 35.0, 37.0)
    w1 = int(bw * (CRIT / TOTAL) * ease_out(p))
    if w1 > 2:
        d.rectangle([bx, by, bx + w1, by + bh], fill=mix(PAPER, RED, a))
    if p > 0.3:
        tx(d, (bx + 22, by + 16), "冲官方 9,716 人", 30, (255, 255, 255), alpha=a)
    w2 = int(bw * (SUP / TOTAL) * ease_out(p))
    if w2 > 2:
        d.rectangle([bx + w1, by, bx + w1 + w2, by + bh],
                    fill=mix(PAPER, GREEN, a))
    if p > 0.6:
        tx(d, (bx + w1 + w2 + 20, by + 16), "支持 854 人", 30, INK2, alpha=a)

    rule(d, by + 120, a)
    tx(d, (120, by + 156), "冲官方 : 支持官方 = 11.4 : 1", 52, RED, alpha=a)
    tx(d, (120, by + 232), "实际人数只会更多 —— 中立里还有未识别的", 34, INK, alpha=a)
    tx(d, (120, by + 292), "中立 8,132 人 · 无实质 269 人", 30, GRAY,
       bold=False, alpha=a)

    footer(d, SUB, "分母 18,971 人", a)
    folio(d, a, prog(t))


def s_p06b(d, t):
    """横向对比：明日方舟 vs 三角洲"""
    a = fade(t, 41.0, 52.5, 0.5, 0.5)
    header(d, VIDEO, 7, "横向对比", a)
    y = h1(d, "这个数字，其实不算小", y=125, alpha=a, size=60)

    tx(d, (120, y - 8), "拿 2025 年 10 月三角洲行动的节奏做标尺", 30, GRAY,
       bold=False, alpha=a)

    ny = y + 66
    c0, c1, c2 = 120, 660, 1080
    tx(d, (c1, ny), "明日方舟", 32, RED, alpha=a)
    tx(d, (c2, ny), "三角洲行动", 32, BLUE, alpha=a)
    rule(d, ny + 50, a)

    rows = [
        ("B站爬虫用户", "18,971 人", "146,648 人"),
        ("其中冲官方", "9,716 人", "未判定（按全部计）"),
        ("日活 DAU", "约 240 万（估算）", "3,000 万"),
        ("冲的人占日活", "0.41%", "0.49%"),
    ]
    for i, (k, v1, v2) in enumerate(rows):
        yy = ny + 78 + i * 74
        p = seg(t, 42.4 + i * 0.2, 43.6 + i * 0.2)
        if p <= 0.05:
            continue
        tx(d, (c0, yy), k, 28, INK2, bold=False, alpha=a)
        tx(d, (c1, yy), v1, 34, RED, alpha=a)
        tx(d, (c2, yy), v2, 34, BLUE, alpha=a)

    rule(d, ny + 396, a)
    tx(d, (120, ny + 430), "同样占日活 0.4% 上下 —— 这不是小众抱怨", 42, INK, alpha=a)

    # 角落数据来源
    s1 = "三角洲 DAU：腾讯 2025Q2 财报 / 官方 2025-09 一周年官宣"
    s2 = "明日方舟 DAU：无官方披露，据 BV1TwHS6rENx 评论区估算"
    tx(d, (W - 120, H - 122), s1, 17, LGRAY, anchor="ra", bold=False, alpha=a * 0.8)
    tx(d, (W - 120, H - 98), s2, 17, LGRAY, anchor="ra", bold=False, alpha=a * 0.8)

    footer(d, SUB, "压力相当", a)
    folio(d, a, prog(t))

def s_p07(d, t):
    """中立分类"""
    a = fade(t, 52.5, 59.5, 0.5, 0.5)
    header(d, VIDEO, 8, "中立都在说什么", a)
    y = h1(d, "8,132 个中立，其实是这些", y=130, alpha=a, size=58)

    ny = y + 10
    for i, (lb, v, pc, col) in enumerate(NEU_CATS):
        yy = ny + i * 54
        p = seg(t, 41.6 + i * 0.07, 43.0 + i * 0.07)
        tx(d, (120, yy), lb, 27, INK2, bold=False, alpha=a)
        bw = 620
        d.rectangle([700, yy + 8, 700 + bw, yy + 32], fill=(238, 234, 228))
        w = int(bw * (v / 3700) * ease_out(p))
        if w > 2:
            d.rectangle([700, yy + 8, 700 + w, yy + 32], fill=mix(PAPER, col, a))
        if p > 0.4:
            tx(d, (1360, yy), f"{v:,}", 27, col, alpha=a)
            tx(d, (1480, yy), f"{pc}%", 27, GRAY, alpha=a)

    ty = ny + 11 * 54 + 10
    tx(d, (120, ty), "中立不是「支持」，是没说话", 34, RED, alpha=a)

    footer(d, SUB, "剧情/玩梗/许愿为主", a)
    folio(d, a, prog(t))


def s_p08(d, t):
    a = fade(t, 59.5, 67.5, 0.5, 0.5)
    header(d, VIDEO, 9, "一点批评", a)
    y = h1(d, "只谈刷屏，会漏掉真正的问题", y=160, alpha=a, size=66)

    ny = y + 10
    tx(d, (120, ny), "已经给出的数据，足以模拟干员强度", 38, INK, alpha=a)
    for i, s in enumerate([
        "技能倍率、攻击间隔、天赋描述，官方都写了",
        "用公开数值做 DPS / 总伤 / 回转计算，是社区常规操作",
        "不需要私服，不需要解包，纯算术就能复现",
    ]):
        bullet(d, 128, ny + 66 + i * 58, s, 31, INK2, a, ORANGE)

    rule(d, ny + 258, a)
    tx(d, (120, ny + 292), "所以就出现了很讽刺的一幕：", 38, INK, alpha=a)
    tx(d, (120, ny + 348), "评论区几万人吵强度，视频里却在数刷屏", 42, RED, alpha=a)

    tx(d, (120, ny + 428), "刷屏要讲，但不能只讲刷屏。", 34, INK2, bold=False, alpha=a)
    tx(d, (120, ny + 478), "把「讨论的人」全当成「刷屏的人」，", 34, INK2,
       bold=False, alpha=a)
    tx(d, (120, ny + 528), "才是最省事也最失真的做法。", 34, INK2, bold=False, alpha=a)

    footer(d, SUB, "刷屏是真问题，但不是唯一问题", a)
    folio(d, a, prog(t))


def s_p09(d, t):
    a = fade(t, 67.5, 74.5, 0.5, 0.5)
    header(d, VIDEO, 10, "方法", a)
    y = h1(d, "数据与方法", y=170, alpha=a, size=68)

    ny = y + 16
    rows = [
        ("样本", "BV1fjHP6eECY 一级 + 楼中楼，共 190,979 条（98.0%）"),
        ("抓取", "B 站公开评论接口，mode=2 最新排序，5,642 页"),
        ("口径", "按 mid 去重；>100 条账号全部计入冲官方"),
        ("判定", "10 个子代理逐条重判 + 规则交叉验证"),
        ("排除", "许愿/宣群/纯表情/排期抱怨 → 无立场，单列"),
        ("工具", "DeepSeek 全程抓取与统计，脚本与数据可复现"),
    ]
    for i, (k, v) in enumerate(rows):
        yy = ny + i * 76
        tx(d, (120, yy), k, 30, RED, alpha=a)
        tx(d, (280, yy), v, 29, INK2, bold=False, alpha=a)

    rule(d, ny + 470, a)
    tx(d, (120, ny + 504), "数据不是观点，但它能说明：谁在说，说了多少遍。",
       36, RED, alpha=a)
    tx(d, (120, ny + 560), "——这句话我认同。只是还应该再加一句：说的人，到底有几个。",
       30, GRAY, bold=False, alpha=a)

    footer(d, SUB, "脚本可复现", a)
    folio(d, a, prog(t))


def s_p10(d, t):
    a = fade(t, 74.5, 82.5, 0.6, 0.7)
    header(d, VIDEO, 11, "结语", a)

    tx(d, (120, 190), "十万条评论，不等于十万人", 56, INK, alpha=a)
    tx(d, (120, 268), "但至少有接近 1 万人，在表达不满", 56, RED, alpha=a)
    d.rectangle([120, 352, 198, 360], fill=RED)

    ny = 430
    cards = [
        ("冲官方", f"{CRIT:,}", "51.2%", RED),
        ("支持官方", f"{SUP:,}", "4.5%", GREEN),
        ("中立", f"{NEU:,}", "42.9%", GRAY),
    ]
    for i, (lb, v, pc, col) in enumerate(cards):
        x = 120 + i * 570
        tx(d, (x, ny), lb, 28, GRAY, bold=False, alpha=a)
        tx(d, (x, ny + 42), v, 76, col, alpha=a)
        tx(d, (x, ny + 132), pc, 32, col, alpha=a)

    rule(d, ny + 200, a)
    tx(d, (120, ny + 236), "冲官方 : 支持官方 = 11.4 : 1", 44, RED, alpha=a)
    tx(d, (120, ny + 306), "既要看谁在刷，也要看谁在说。", 38, INK, alpha=a)

    footer(d, SUB, "感谢观看", a)
    folio(d, a, 1.0)


FN = {'p01': s_p01, 'p02': s_p02, 'p03': s_p03, 'p04': s_p04, 'p05': s_p05,
      'p06': s_p06, 'p06b': s_p06b, 'p07': s_p07, 'p08': s_p08, 'p09': s_p09, 'p10': s_p10}


def render(t):
    img = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(img)
    for t0, t1, name in SHOTS:
        if t0 - 0.55 <= t <= t1 + 0.55:
            FN[name](d, t)
    return img


if __name__ == '__main__':
    out = os.path.join(os.path.dirname(__file__), 'preview5')
    os.makedirs(out, exist_ok=True)
    for tt in [2, 9, 15, 22, 29, 37, 45, 52, 59, 68]:
        render(tt).save(os.path.join(out, f'p{tt:02d}.png'))
    print("preview5 ok")
