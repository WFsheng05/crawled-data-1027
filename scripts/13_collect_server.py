#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
collect_server.py — 本地接收器
浏览器页面 POST 数据到这里，落盘为文件。
Chrome 视 127.0.0.1 为可信来源，https 页面可直连，不受 mixed content 限制。
"""
import http.server
import json
import os
import socketserver
import sys

OUT = r"C:\total workspace\Deepseek harness\one\bili_crawl\parts"
PORT = 8899

os.makedirs(OUT, exist_ok=True)


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stdout.write(f"[{self.address_string()}] {fmt % args}\n")
        sys.stdout.flush()

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Private-Network", "true")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n)
        name = self.path.strip("/").replace("/", "_") or "unknown"
        if not name.endswith(".txt"):
            name += ".txt"
        path = os.path.join(OUT, name)
        with open(path, "wb") as f:
            f.write(body)
        print(f"  saved {name}  {len(body)/1024:.1f} KB")
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok")

    def do_GET(self):
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"collector alive")


class TS(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    print(f"接收器启动: http://127.0.0.1:{PORT}")
    print(f"落盘目录: {OUT}")
    with TS(("127.0.0.1", PORT), H) as srv:
        srv.serve_forever()
