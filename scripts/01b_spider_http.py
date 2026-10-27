#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bili_comment_spider.py — B 站评论区爬虫（无需登录，自动处理分页/楼中楼/游标）

实测可用的接口：
  主评论   GET https://api.bilibili.com/x/v2/reply/main
           ?type=1&oid=<aid>&next=0&mode=2&plat=1&pagination_str={"offset":"<游标>"}
           -> data.replies / data.top_replies
           -> data.cursor.all_count       评论总数
           -> data.cursor.pagination_reply.next_offset  下一页游标
           -> data.cursor.is_end          是否到底
  楼中楼   GET https://api.bilibili.com/x/v2/reply/reply
           ?type=1&oid=<aid>&root=<rpid>&pn=<页码>&ps=20
           -> data.replies / data.page.count

必须带：User-Agent + Referer + Cookie(buvid3)。
Cookie 可用 /x/frontend/finger/spi 免费换，无需登录。

用法：
  python bili_comment_spider.py BV1NjHg6ZEgm
  python bili_comment_spider.py BV1NjHg6ZEgm -o out.csv --sub --sub-limit 500
  python bili_comment_spider.py BV1NjHg6ZEgm --sort 2 --max-pages 50

产物：out.json（全字段）+ out.csv（扁平表）
"""

import argparse
import csv
import gzip
import json
import random
import sys
import time
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

API_REPLY_MAIN = "https://api.bilibili.com/x/v2/reply/main"
API_REPLY_SUB = "https://api.bilibili.com/x/v2/reply/reply"
API_VIEW = "https://api.bilibili.com/x/web-interface/view"
API_SPI = "https://api.bilibili.com/x/frontend/finger/spi"


class Bili:
    def __init__(self, cookie=None, delay=0.6):
        self.delay = delay
        self.cookie = cookie or self._fresh_cookie()

    # ---------- 基础请求 ----------
    def _headers(self, referer="https://www.bilibili.com/"):
        return {
            "User-Agent": UA,
            "Referer": referer,
            "Origin": "https://www.bilibili.com",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cookie": self.cookie,
            "Connection": "keep-alive",
        }

    def _get(self, url, referer="https://www.bilibili.com/", retry=3):
        last = None
        for i in range(retry):
            try:
                req = urllib.request.Request(url, headers=self._headers(referer))
                with urllib.request.urlopen(req, timeout=25) as r:
                    raw = r.read()
                    if r.headers.get("Content-Encoding") == "gzip":
                        raw = gzip.decompress(raw)
                    j = json.loads(raw.decode("utf-8"))
                code = j.get("code", 0)
                if code == 0:
                    return j
                # -412 风控 / -509 限流 / -799 请求过频
                if code in (-412, -509, -799, -352):
                    time.sleep(2 + i * 3)
                    last = j
                    continue
                return j
            except Exception as e:               # noqa: BLE001
                last = {"code": -1, "message": str(e)}
                time.sleep(1.5 + i * 2)
        return last or {"code": -1, "message": "unknown"}

    # ---------- 匿名 Cookie ----------
    @staticmethod
    def _fresh_cookie():
        req = urllib.request.Request(API_SPI, headers={
            "User-Agent": UA, "Referer": "https://www.bilibili.com/"})
        with urllib.request.urlopen(req, timeout=20) as r:
            j = json.loads(r.read().decode())
        d = j.get("data") or {}
        return f"buvid3={d.get('b_3','')}; buvid4={d.get('b_4','')}"

    # ---------- BV -> aid ----------
    def bvid_to_aid(self, bvid):
        j = self._get(f"{API_VIEW}?bvid={bvid}",
                      referer=f"https://www.bilibili.com/video/{bvid}/")
        if j.get("code") != 0:
            raise RuntimeError(f"取 aid 失败: {j}")
        d = j["data"]
        return d["aid"], {
            "bvid": bvid, "aid": d["aid"], "title": d["title"],
            "owner": d["owner"]["name"], "view": d["stat"]["view"],
            "like": d["stat"]["like"], "reply": d["stat"]["reply"],
            "pubdate": d["pubdate"],
        }

    # ---------- 主评论（游标翻页） ----------
    def crawl_main(self, aid, mode=2, max_pages=200, referer=None, on_page=None):
        offset = ""
        pages = 0
        seen = set()
        rows = []
        total = None
        while pages < max_pages:
            pagi = json.dumps({"offset": offset}, separators=(",", ":"))
            url = (f"{API_REPLY_MAIN}?type=1&oid={aid}&next=0&mode={mode}"
                   f"&plat=1&pagination_str={urllib.parse.quote(pagi)}")
            j = self._get(url, referer=referer)
            if j.get("code") != 0:
                print(f"  [!] page{pages+1} code={j.get('code')} {j.get('message')}",
                      file=sys.stderr)
                break
            d = j.get("data") or {}
            cur = d.get("cursor") or {}
            total = cur.get("all_count", total)

            batch = (d.get("replies") or []) + (d.get("top_replies") or [])
            added = 0
            for r in batch:
                if r["rpid"] in seen:
                    continue
                seen.add(r["rpid"])
                rows.append(r)
                added += 1
            pages += 1
            if on_page:
                on_page(pages, added, len(rows), total)

            pr = cur.get("pagination_reply") or {}
            nxt = pr.get("next_offset")
            if not nxt or cur.get("is_end"):
                break
            offset = nxt
            time.sleep(self.delay + random.uniform(0, 0.4))
        return rows, total, pages

    # ---------- 楼中楼 ----------
    def crawl_sub(self, aid, root, ps=20, limit=200, referer=None):
        out = []
        pn = 1
        while len(out) < limit:
            url = (f"{API_REPLY_SUB}?type=1&oid={aid}&root={root}"
                   f"&pn={pn}&ps={ps}")
            j = self._get(url, referer=referer)
            if j.get("code") != 0:
                break
            d = j.get("data") or {}
            reps = d.get("replies") or []
            if not reps:
                break
            out.extend(reps)
            page = d.get("page") or {}
            if pn * ps >= page.get("count", 0):
                break
            pn += 1
            time.sleep(self.delay * 0.6 + random.uniform(0, 0.2))
        return out[:limit]

    # ---------- 用户信息兜底 ----------
    def user_info(self, mid):
        j = self._get(f"https://api.bilibili.com/x/space/acc/info?mid={mid}")
        if j.get("code") == 0:
            d = j["data"]
            return {"level": d.get("level"), "sex": d.get("sex"),
                    "sign": d.get("sign")}
        return {}


# ---------------- 扁平化 ----------------
def flatten(r, video, parent=None):
    m = r.get("member") or {}
    c = r.get("content") or {}
    return {
        "video_bvid": video.get("bvid"),
        "video_title": video.get("title"),
        "rpid": r.get("rpid"),
        "parent_rpid": parent,
        "root": r.get("root", 0),
        "is_sub": 1 if parent else 0,
        "uname": m.get("uname"),
        "mid": m.get("mid"),
        "sex": m.get("sex"),
        "sign": (m.get("sign") or "").replace("\n", " "),
        "user_level": (m.get("level_info") or {}).get("current_level"),
        "content": (c.get("message") or "").replace("\r", " ").replace("\n", " "),
        "ctime": r.get("ctime"),
        "ctime_str": time.strftime("%Y-%m-%d %H:%M:%S",
                                   time.localtime(r.get("ctime", 0))),
        "like": r.get("like"),
        "rcount": r.get("rcount"),
        "location": (r.get("reply_control") or {}).get("location", "").replace("IP属地：", ""),
        "platform": (r.get("reply_control") or {}).get("sub_reply_entry_text", ""),
    }


def main():
    ap = argparse.ArgumentParser(description="B站评论区爬虫")
    ap.add_argument("bvid", help="BV 号，如 BV1NjHg6ZEgm（也接受 av 号）")
    ap.add_argument("-o", "--out", default="bili_comments", help="输出文件名前缀")
    ap.add_argument("--sort", type=int, default=2, choices=[2, 3],
                    help="2=按热度(默认) 3=按时间")
    ap.add_argument("--sub", action="store_true", help="同时抓楼中楼")
    ap.add_argument("--sub-limit", type=int, default=100, help="每个根评论最多抓多少子评论")
    ap.add_argument("--max-pages", type=int, default=200, help="主评论最多翻多少页")
    ap.add_argument("--delay", type=float, default=0.6, help="请求间隔秒")
    ap.add_argument("--cookie", default=None, help="自定义 Cookie（登录态更稳）")
    args = ap.parse_args()

    b = Bili(cookie=args.cookie, delay=args.delay)

    raw = args.bvid.strip()
    if raw.lower().startswith("av"):
        aid = int(raw[2:])
        j = b._get(f"{API_VIEW}?aid={aid}")
        video = {"bvid": j["data"]["bvid"], "aid": aid,
                 "title": j["data"]["title"], "owner": j["data"]["owner"]["name"],
                 "view": j["data"]["stat"]["view"], "reply": j["data"]["stat"]["reply"]}
        referer = f"https://www.bilibili.com/video/{video['bvid']}/"
    else:
        bvid = raw if raw.startswith("BV") else "BV" + raw
        aid, video = b.bvid_to_aid(bvid)
        referer = f"https://www.bilibili.com/video/{bvid}/"

    print(f"视频: {video['title']}  (aid={aid}, 总评论={video.get('reply')})")

    def on_page(p, added, total_got, total_all):
        print(f"  第{p}页 +{added:<3} 累计={total_got:<4}/{total_all}")

    rows, total, pages = b.crawl_main(aid, mode=args.sort, max_pages=args.max_pages,
                                      referer=referer, on_page=on_page)
    print(f"主评论完成: {len(rows)} 条 / {pages} 页（接口声明总数 {total}）")

    # ---- 降级检测：code=0 但被静默截断 ----
    if pages <= 1 and total and len(rows) <= 5 and total > len(rows) * 2:
        print("\n[!] 疑似被指纹级风控静默降级：", file=sys.stderr)
        print(f"    声明总数 {total}，实际只拿到 {len(rows)} 条且 is_end=true。", file=sys.stderr)
        print("    纯 HTTP 客户端常见现象（TLS/JA3 指纹 + 无 bili_ticket）。", file=sys.stderr)
        print("    对策：1) 传登录 Cookie（含 SESSDATA）重试", file=sys.stderr)
        print("          2) 改用浏览器通道：python bili_ego_spider.py <BV号>", file=sys.stderr)

    flat = [flatten(r, video) for r in rows]

    if args.sub:
        roots = [r for r in rows if (r.get("rcount") or 0) > 0]
        print(f"楼中楼: {len(roots)} 个根评论有回复")
        for i, r in enumerate(roots, 1):
            subs = b.crawl_sub(aid, r["rpid"], limit=args.sub_limit, referer=referer)
            for s in subs:
                flat.append(flatten(s, video, parent=r["rpid"]))
            print(f"  [{i}/{len(roots)}] rpid={r['rpid']} 子评论 {len(subs)}"
                  f"/{r.get('rcount')}")
            time.sleep(b.delay * 0.8)
        print(f"合计（含楼中楼）: {len(flat)} 条")

    # ---------- 落盘 ----------
    with open(f"{args.out}.json", "w", encoding="utf-8") as f:
        json.dump({"video": video, "total_api": total, "fetched": len(flat),
                   "comments": flat}, f, ensure_ascii=False, indent=1)

    if flat:
        with open(f"{args.out}.csv", "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(flat[0].keys()))
            w.writeheader()
            w.writerows(flat)

    print(f"\n已保存: {args.out}.json / {args.out}.csv")


if __name__ == "__main__":
    main()
