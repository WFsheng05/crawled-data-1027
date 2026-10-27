#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze_full.py — 一级评论 + 楼中楼 全量分析

输入 full_pv.json:
  rows: [rpid, mid, uname, msg, ctime, like, rcount, sex, level, ip]
  subs: [rpid, root, mid, uname, msg, ctime, like, sex, level, ip, parent]
"""
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PUNCT = re.compile(
    "[\\s，。！？、；：\"\"''（）《》【】…—～·,.!?;:\"'" + chr(92) + "()" +
    "\\[\\]{}<>~`@#$%^&*+=|/" + chr(92) + chr(92) + "_-]"
)


def norm30(s, n=30):
    return PUNCT.sub('', s or '')[:n]


def load(path):
    d = json.load(open(path, encoding='utf-8'))
    main = [dict(rpid=r[0], mid=r[1], uname=r[2], msg=r[3], ctime=r[4],
                 like=r[5] or 0, rcount=r[6] or 0, sex=r[7] or '',
                 level=r[8] or 0, ip=r[9] or '', is_sub=0, root=0)
            for r in d['rows']]
    subs = [dict(rpid=r[0], root=r[1], mid=r[2], uname=r[3], msg=r[4], ctime=r[5],
                 like=r[6] or 0, rcount=0, sex=r[7] or '', level=r[8] or 0,
                 ip=r[9] or '', is_sub=1, parent=r[10] if len(r) > 10 else 0)
            for r in d.get('subs', [])]
    return d.get('meta', {}), d.get('subMeta', {}), main, subs


def main(path):
    meta, sub_meta, M, S = load(path)
    ALL = M + S
    n_main, n_sub, n_all = len(M), len(S), len(ALL)

    print("=" * 70)
    print(f"一级评论 {n_main:,}  +  楼中楼 {n_sub:,}  =  总计 {n_all:,}")
    print(f"接口 all_count = {meta.get('allCount'):,}   完整度 = {n_all/meta['allCount']:.1%}")
    print(f"主评论 {meta.get('pages'):,} 页 / {meta.get('sec')}s   "
          f"楼中楼 {sub_meta.get('rows',0):,} 条 / {sub_meta.get('sec')}s")
    print("=" * 70)

    ts_all = [r['ctime'] for r in ALL if r['ctime']]
    users = {r['mid'] for r in ALL}
    span = (max(ts_all) - min(ts_all)) / 3600

    print(f"\n[总量]")
    print(f"  评论总数   : {n_all:,}   (一级 {n_main:,} + 楼中楼 {n_sub:,})")
    print(f"  独立用户   : {len(users):,}")
    print(f"  人均       : {n_all/len(users):.1f} 条")
    print(f"  时间跨度   : {span:.1f} 小时")
    print(f"  时间范围   : {datetime.fromtimestamp(min(ts_all))} ~ {datetime.fromtimestamp(max(ts_all))}")

    # 每天
    print(f"\n[按天]")
    day = Counter(datetime.fromtimestamp(t).strftime('%m-%d') for t in ts_all)
    for d, c in sorted(day.items()):
        print(f"  {d}  {c:>7,}  {c/n_all:>6.1%}")

    # 每小时
    hour = Counter(datetime.fromtimestamp(t).strftime('%m-%d %H') for t in ts_all)
    peak = hour.most_common(1)[0]
    print(f"\n[按小时]")
    print(f"  峰值 {peak[0]}  {peak[1]:,} 条/小时")
    print(f"  平均 {n_all/span:,.0f} 条/小时")

    # 前26h vs 后26h
    base = min(ts_all)
    f26 = sum(1 for t in ts_all if t <= base + 26 * 3600)
    print(f"\n[前26h vs 后26h]  前 {f26:,} ({f26/n_all:.1%})  |  后 {n_all-f26:,} ({1-f26/n_all:.1%})")

    # 楼层深度
    print(f"\n[楼中楼结构]")
    print(f"  有回复的根评论 : {sum(1 for r in M if r['rcount'])} 个")
    depth = Counter()
    for r in M:
        if r['rcount']:
            depth[r['rcount']] += 1
    top_roots = sorted([r for r in M if r['rcount']], key=lambda x: -x['rcount'])[:5]
    print(f"  楼中楼最多 Top5:")
    sub_by_root = Counter(r['root'] for r in S)
    for r in top_roots:
        got = sub_by_root.get(r['rpid'], 0)
        print(f"    {r['uname'][:14]:<16} 标称 {r['rcount']:>4} 抓得 {got:>4}  「{r['msg'][:22]}」")

    # 单账号排行（一级+楼中楼合计）
    per_user = Counter(r['mid'] for r in ALL)
    name = {}
    for r in ALL:
        name.setdefault(r['mid'], r['uname'])
    print(f"\n[刷屏榜 Top15（一级+楼中楼合计）]")
    print(f"  {'排名':<4}{'账号':<18}{'总数':>7}{'一级':>7}{'楼中楼':>7}")
    pm = Counter(r['mid'] for r in M)
    ps = Counter(r['mid'] for r in S)
    for i, (m, c) in enumerate(per_user.most_common(15), 1):
        print(f"  {i:<4}{name.get(m,'')[:16]:<18}{c:>7,}{pm.get(m,0):>7,}{ps.get(m,0):>7,}")

    # 集中度
    print(f"\n[高频账号集中度]")
    for th in (10, 30, 50, 100, 200):
        hi = [m for m, c in per_user.items() if c >= th]
        cm = sum(per_user[m] for m in hi)
        print(f"  >={th:>3} 条 : {len(hi):>5,} 人 ({len(hi)/len(users):>5.1%})"
              f"  贡献 {cm:>7,} 条 ({cm/n_all:>5.1%})")

    # 复读（全量）
    print(f"\n[复读率（去标点前30字归并，一级+楼中楼）]")
    grp = defaultdict(list)
    for r in ALL:
        grp[norm30(r['msg'])].append(r)
    dup = {k: v for k, v in grp.items() if len(v) > 1}
    dup_n = sum(len(v) for v in dup.values())
    print(f"  文本簇 {len(grp):,}   重复簇 {len(dup):,}   落在重复簇 {dup_n:,} = {dup_n/n_all:.1%}")

    print(f"\n[复读 Top10]")
    for i, (k, v) in enumerate(sorted(dup.items(), key=lambda x: -len(x[1]))[:10], 1):
        who = len({x['mid'] for x in v})
        print(f"  {i:>2}. {len(v):>6,} 条 / {who:>5,} 人  「{k[:30]}」")

    # 关键词
    KW = {'加强': ['加强'], '贬值/强度': ['贬值', '强度', '倍率', '膨胀'],
          '私服': ['私服'], '冲塔': ['傻逼', '弱智', '恶心', '垃圾', '退钱', '吃相', '脑残']}
    print(f"\n[关键词命中（全量）]")
    for k, kws in KW.items():
        c = sum(1 for r in ALL if any(w in r['msg'] for w in kws))
        print(f"  {k:<10} {c:>7,}  {c/n_all:>6.1%}")

    # IP
    print(f"\n[IP 属地 Top12（楼中楼也有）]")
    for ip, c in Counter(r['ip'] for r in ALL if r['ip']).most_common(12):
        print(f"  {ip:<8} {c:>7,}  {c/n_all:>5.1%}")

    # 高赞
    print(f"\n[全量高赞 Top10]")
    for r in sorted(ALL, key=lambda x: -x['like'])[:10]:
        tag = '楼中楼' if r['is_sub'] else '一级'
        print(f"  {r['like']:>6,} 赞 [{tag}] {r['uname'][:12]:<14} {r['msg'][:30]}")

    # 峰值小时里谁在发
    ph = peak[0]
    inpeak = [r for r in ALL if datetime.fromtimestamp(r['ctime']).strftime('%m-%d %H') == ph]
    print(f"\n[峰值小时 {ph} 内 Top10 账号]  共 {len(inpeak):,} 条 / {len({r['mid'] for r in inpeak})} 人")
    for m, c in Counter(r['mid'] for r in inpeak).most_common(10):
        print(f"  {name.get(m,'')[:16]:<18}{c:>5} 条")

    # 导出 CSV
    out = 'full_comments.csv'
    with open(out, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['type', 'rpid', 'root', 'mid', 'uname', 'message',
                    'ctime', 'datetime', 'like', 'sex', 'level', 'ip'])
        for r in ALL:
            w.writerow(['楼中楼' if r['is_sub'] else '一级', r['rpid'], r['root'],
                        r['mid'], r['uname'], r['msg'], r['ctime'],
                        datetime.fromtimestamp(r['ctime']).strftime('%Y-%m-%d %H:%M:%S'),
                        r['like'], r['sex'], r['level'], r['ip']])
    print(f"\nCSV 已导出: {out}  ({n_all:,} 行)")


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'full_pv.json')
