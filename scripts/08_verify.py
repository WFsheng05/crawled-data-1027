import sys
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

all_src, all_out = [], []
problems = []

for i in range(1,9):
    src_p = f"rejudge/r{i}.txt"
    out_p = f"rejudge/v{i}.tsv"

    src = []
    for ln, line in enumerate(open(src_p, encoding="utf-8"), 1):
        if "\t" not in line:
            problems.append(f"{src_p}:{ln} 无tab")
            continue
        src.append(line.split("\t")[0].strip())

    out = []
    bad_fmt = 0
    for ln, line in enumerate(open(out_p, encoding="utf-8"), 1):
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 2 or parts[1].strip().upper() not in ("A","B","C"):
            bad_fmt += 1
            if bad_fmt <= 3:
                problems.append(f"{out_p}:{ln} 格式异常: {line[:60]!r}")
            continue
        out.append(parts[0].strip())

    dup_src = [k for k,v in Counter(src).items() if v>1]
    dup_out = [k for k,v in Counter(out).items() if v>1]
    miss = set(src) - set(out)
    extra = set(out) - set(src)

    print(f"v{i}: 输入{len(src)} 输出{len(out)} 格式异常{bad_fmt} "
          f"输入重复{len(dup_src)} 输出重复{len(dup_out)} "
          f"缺失{len(miss)} 多余{len(extra)}")
    if miss:
        problems.append(f"v{i} 缺失 {len(miss)} 条: {list(miss)[:3]}")
    if extra:
        problems.append(f"v{i} 多余 {len(extra)} 条: {list(extra)[:3]}")

    all_src += src
    all_out += out

print(f"\n总计: 输入{len(all_src)} 输出{len(all_out)}")
print(f"全局唯一 mid: 输入{len(set(all_src))} 输出{len(set(all_out))}")
dup_all = [k for k,v in Counter(all_src).items() if v>1]
print(f"全局重复 mid: {len(dup_all)}")

if problems:
    print("\n=== 问题 ===")
    for p in problems[:20]:
        print(" ", p)
else:
    print("\n✅ 全部完整，无缺失无重复")
