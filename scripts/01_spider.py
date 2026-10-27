#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bili_ego_spider.py — 用「真实浏览器通道」抓 B 站评论区（绕过 TLS/指纹级风控）

为什么需要它：
  纯 HTTP 客户端（requests / urllib / node-https）调 /x/v2/reply/main 拿到的
  是降级结果：只有 3~4 条，且 cursor.is_end 直接为 true。这是因为 B 站对
  非浏览器 TLS/JA3 指纹 + 无 bili_ticket 的请求做了静默降级（返回 code=0 但截断）。
  在真实浏览器上下文里 fetch，接口会正常返回分页数据。

依赖：ego-browser CLI（本机已装），通过 ego_cli / ego_script 执行。

方式 A（推荐，本机自动化）：python bili_ego_spider.py <BV号> -o demo
  它会生成一份 JS，交给 ego-browser 执行，浏览器内翻页结束后回传数据。

方式 B（最省事，手工一次）：直接在本对话里让我跑 ego_script。

实测数据（BV1NjHg6ZEgm）：8 页 / 134 条；接口声明 all_count=213
（差值 = 被折叠、被删除、审核中的评论，正常现象）。
"""

import argparse
import csv
import json
import os
import subprocess
import sys
import tempfile

EGO = r"C:\Users\Admin\.dsh\profiles\desktop\node_modules\dsh-ego-browser\runtime\ego-linux\bin\ego-browser.mjs"
NODE = sys.executable.replace("python.exe", "").replace("python", "") or "node"

JS_TEMPLATE = r"""
const AID = AID_PLACEHOLDER;
const MODE = MODE_PLACEHOLDER;
const MAX_PAGES = MAXP_PLACEHOLDER;
const DELAY = DELAY_PLACEHOLDER;
const SUB_LIMIT = SUBLIMIT_PLACEHOLDER;
const WANT_SUB = SUBFLAG_PLACEHOLDER;

(async () => {
  const seen = new Set();
  const rows = [];
  const log = [];
  let offset = '', pages = 0, allCount = null;

  while (pages < MAX_PAGES) {
    const url = 'https://api.bilibili.com/x/v2/reply/main?type=1&oid=' + AID +
      '&next=0&mode=' + MODE + '&plat=1&pagination_str=' +
      encodeURIComponent(JSON.stringify({ offset }));
    let j;
    try { j = await fetch(url, { credentials: 'include' }).then(r => r.json()); }
    catch (e) { log.push({ page: pages + 1, error: String(e) }); break; }
    if (j.code !== 0) { log.push({ page: pages + 1, code: j.code, msg: j.message }); break; }

    const d = j.data || {}, c = d.cursor || {};
    if (c.all_count != null) allCount = c.all_count;
    const batch = (d.replies || []).concat(d.top_replies || []);
    let add = 0;
    for (const r of batch) {
      if (seen.has(r.rpid)) continue;
      seen.add(r.rpid);
      rows.push({
        rpid: r.rpid, uname: (r.member || {}).uname, mid: (r.member || {}).mid,
        sex: (r.member || {}).sex,
        level: ((r.member || {}).level_info || {}).current_level,
        sign: ((r.member || {}).sign || '').replace(/\s+/g, ' '),
        message: ((r.content || {}).message || '').replace(/\s+/g, ' '),
        ctime: r.ctime, like: r.like, rcount: r.rcount,
        ip: ((r.reply_control || {}).location || '').replace('IP属地：', ''),
        is_sub: 0,
      });
      add++;
    }
    pages++;
    const pr = c.pagination_reply || {};
    log.push({ page: pages, got: batch.length, add, total: rows.length, allCount,
               is_end: c.is_end, next: !!pr.next_offset });
    if (!pr.next_offset || c.is_end) break;
    offset = pr.next_offset;
    await new Promise(r => setTimeout(r, DELAY));
  }

  // ---- 楼中楼 ----
  if (WANT_SUB) {
    const roots = rows.filter(r => (r.rcount || 0) > 0);
    for (const root of roots) {
      let pn = 1, got = 0;
      while (got < SUB_LIMIT) {
        const u = 'https://api.bilibili.com/x/v2/reply/reply?type=1&oid=' + AID +
          '&root=' + root.rpid + '&pn=' + pn + '&ps=20';
        let j;
        try { j = await fetch(u, { credentials: 'include' }).then(r => r.json()); }
        catch (e) { break; }
        if (j.code !== 0) break;
        const d = j.data || {}, reps = d.replies || [], pg = d.page || {};
        if (!reps.length) break;
        for (const r of reps) {
          if (seen.has(r.rpid)) continue;
          seen.add(r.rpid);
          rows.push({
            rpid: r.rpid, parent: root.rpid,
            uname: (r.member || {}).uname, mid: (r.member || {}).mid,
            sex: (r.member || {}).sex,
            level: ((r.member || {}).level_info || {}).current_level,
            sign: ((r.member || {}).sign || '').replace(/\s+/g, ' '),
            message: ((r.content || {}).message || '').replace(/\s+/g, ' '),
            ctime: r.ctime, like: r.like, rcount: r.rcount,
            ip: ((r.reply_control || {}).location || '').replace('IP属地：', ''),
            is_sub: 1,
          });
          got++;
        }
        if (pn * 20 >= (pg.count || 0)) break;
        pn++;
        await new Promise(r => setTimeout(r, DELAY * 0.6));
      }
      await new Promise(r => setTimeout(r, DELAY * 0.5));
    }
  }

  console.log('@@DSH_RESULT@@' + JSON.stringify({ aid: AID, pages, allCount,
    fetched: rows.length, log, rows }));
})();
"""


def build_js(aid, mode, max_pages, delay, sub, sub_limit):
    return (JS_TEMPLATE
            .replace("AID_PLACEHOLDER", str(aid))
            .replace("MODE_PLACEHOLDER", str(mode))
            .replace("MAXP_PLACEHOLDER", str(max_pages))
            .replace("DELAY_PLACEHOLDER", str(delay))
            .replace("SUBLIMIT_PLACEHOLDER", str(sub_limit))
            .replace("SUBFLAG_PLACEHOLDER", "true" if sub else "false"))


def main():
    ap = argparse.ArgumentParser(description="B站评论区爬虫（浏览器通道版）")
    ap.add_argument("bvid")
    ap.add_argument("-o", "--out", default="bili_comments")
    ap.add_argument("--mode", type=int, default=2, help="2=热度 3=时间")
    ap.add_argument("--max-pages", type=int, default=200)
    ap.add_argument("--delay", type=int, default=400, help="毫秒")
    ap.add_argument("--sub", action="store_true")
    ap.add_argument("--sub-limit", type=int, default=100)
    ap.add_argument("--js-only", action="store_true", help="只输出 JS，不执行")
    args = ap.parse_args()

    raw = args.bvid.strip()
    if raw.lower().startswith("bv"):
        aid = raw
    elif raw.lower().startswith("av"):
        aid = int(raw[2:])
    else:
        aid = "BV" + raw

    js = build_js(aid, args.mode, args.max_pages, args.delay, args.sub, args.sub_limit)
    js_path = os.path.abspath(f"{args.out}.auto.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(js)

    if args.js_only:
        print(js_path)
        return

    # 交给 ego-browser 执行
    cmd = [NODE, EGO, "--file", js_path]
    print("执行:", " ".join(cmd))
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    except FileNotFoundError:
        print(f"未找到 ego-browser（{EGO}），请用 --js-only 生成脚本后在会话内执行。",
              file=sys.stderr)
        return
    out = p.stdout
    payload = None
    for line in out.splitlines():
        if line.startswith("@@DSH_RESULT@@"):
            payload = json.loads(line[len("@@DSH_RESULT@@"):])
    if not payload:
        print(out[-2000:], p.stderr[-2000:], sep="\n", file=sys.stderr)
        return

    rows = payload["rows"]
    with open(f"{args.out}.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    if rows:
        keys = ["rpid", "parent", "uname", "mid", "sex", "level", "sign",
                "message", "ctime", "like", "rcount", "ip", "is_sub"]
        with open(f"{args.out}.csv", "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
    print(f"页数={payload['pages']} 抓取={payload['fetched']} "
          f"接口声明={payload.get('allCount')}")
    print(f"已保存: {args.out}.json / {args.out}.csv")


if __name__ == "__main__":
    main()
