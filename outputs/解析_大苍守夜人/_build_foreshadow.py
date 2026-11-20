# -*- coding: utf-8 -*-
"""从 00_承接链.md 重建 02_伏笔台账.md（派生台账，可随时重跑）。

解析口径：
  1. 每章「新伏笔」字段按 ①②③ 切分为伏笔条目，ID = 章号-序号。
  2. 每章「回收」字段按 ；切分为子句，每个子句提取被引用的伏笔 ID 与其状态标记：
     （回收）/（回收落地）      -> 已回收
     （部分回收）              -> 部分回收（仍记为在办，标注部分回收章）
     （推进）/（呼应…）        -> 在办，记录最近推进章
     （未回收）/（未提）        -> 在办
  3. 从未被任何后续章引用者 -> 在办（标注"未再提及"）。
"""
import json
import re
from pathlib import Path

BASE = Path(r"D:/Agent/Antigravity/demo19/outputs/解析_大苍守夜人")
SRC = BASE / "00_承接链.md"
OUT_MD = BASE / "02_伏笔台账.md"
OUT_JSON = BASE / "_tmp_foreshadow_all.json"

text = SRC.read_text(encoding="utf-8")
blocks = []
for rb in re.split(r"(?m)^### ", text):
    m = re.match(r"第(\d{4})章\s*(.*)", rb.split("\n", 1)[0].strip())
    if m:
        blocks.append((int(m.group(1)), m.group(2).strip(), rb))
blocks.sort(key=lambda x: x[0])

MARK = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"
MI = {c: i + 1 for i, c in enumerate(MARK)}


def field(bt, name):
    m = re.search(r"(?m)^-\s*" + name + r"[：:](.*)$", bt)
    return m.group(1).strip() if m else ""


# ---------- 1. 抽新伏笔 ----------
items = {}
for ch, title, rb in blocks:
    raw = field(rb, "新伏笔")
    if not raw or raw in ("无", "無"):
        continue
    parts = re.split(r"([①-⑳])", raw)
    seq, i = [], 1
    while i < len(parts) - 1:
        body = parts[i + 1].strip().strip("；;，, ")
        if body:
            seq.append((MI.get(parts[i], len(seq) + 1), body))
        i += 2
    if not seq:
        seq = [(1, raw)]
    for idx, body in seq:
        fid = f"{ch:04d}-{idx}"
        items[fid] = {
            "id": fid, "ch": ch, "title": title, "text": body,
            "status": "在办", "recovered_at": "", "partial_at": "",
            "last_touch": "", "note": "未再提及",
        }

# ---------- 2. 解析回收字段 ----------
REF = re.compile(r"(?:第)?(\d{4})章?(?:伏笔)?([①-⑳])")
STAT = [
    ("部分回收", ("部分回收",)),
    ("在办", ("未回收", "未提", "未答", "未定", "未验", "未明")),
    ("已回收", ("回收落地", "呼应落地", "回收")),
    ("推进", ("推进", "呼应", "悬置")),
]

touched = set()
for ch, title, rb in blocks:
    rec = field(rb, "回收")
    if not rec:
        continue
    for clause in re.split(r"[；;]", rec):
        refs = REF.findall(clause)
        if not refs:
            continue
        # 判定该子句状态：显式标记优先；无标记时，出现在「回收」字段且不含否定词者视为已回收
        state = None
        for kw, words in STAT:
            if any(w in clause for w in words):
                state = kw
                break
        if state is None:
            # 无状态标记：不做判定（保守），避免把未回收误计为已回收
            continue
        for chap, mark in refs:
            fid = f"{chap}-{MI.get(mark, 0)}"
            if fid not in items:
                continue
            it = items[fid]
            touched.add(fid)
            if it["status"] == "已回收":
                continue
            if state == "已回收":
                it["status"] = "已回收"
                it["recovered_at"] = f"{ch:04d}"
            elif state == "部分回收":
                if it["status"] != "已回收":
                    it["status"] = "在办"
                    it["partial_at"] = f"{ch:04d}"
                    it["note"] = "部分回收"
            else:
                it["last_touch"] = f"{ch:04d}"
                if it["note"] == "未再提及":
                    it["note"] = "已推进" if state == "推进" else "已提及未收"

for fid, it in items.items():
    if fid not in touched and it["status"] == "在办":
        it["note"] = "未再提及"
    # 强弱分级：含明确疑问/未决措辞者为强悬念
    strong_kw = ("未明", "未解", "为何", "究竟", "是否", "待", "悬念", "不知", "谜", "隐情", "真相", "下落")
    it["strong"] = any(k in it["text"] for k in strong_kw)

lst = sorted(items.values(), key=lambda x: (x["ch"], int(x["id"].split("-")[1])))
open_items = [x for x in lst if x["status"] == "在办"]
done_items = [x for x in lst if x["status"] == "已回收"]

OUT_JSON.write_text(json.dumps(lst, ensure_ascii=False, indent=1), encoding="utf-8")


def short(s, n=42):
    s = re.sub(r"\s+", " ", s)
    return s if len(s) <= n else s[: n - 1] + "…"


L = []
L.append("# 《大苍守夜人》伏笔台账\n")
L.append(f"> **派生文件**，由 `_build_foreshadow.py` 从 `00_承接链.md` 自动重建，请勿手工编辑。")
L.append(f"> 数据截至：第 {blocks[-1][0]:04d} 章　｜　伏笔总数 {len(lst)}　｜　在办 {len(open_items)}　｜　已回收 {len(done_items)}\n")
L.append("> 重建命令：`python _build_foreshadow.py`\n")
L.append("---\n")

L.append("## 一、重点跟踪（强悬念 + 埋设超 40 章未收）\n")
L.append("| ID | 埋设章 | 内容摘要 | 最近动向 |")
L.append("|---|---|---|---|")
latest = blocks[-1][0]
key_items = [x for x in open_items if x["strong"] and x["ch"] <= latest - 40]
for it in key_items:
    mv = it["partial_at"] and f"部分回收于{it['partial_at']}" or (it["last_touch"] and f"推进于{it['last_touch']}" or it["note"])
    L.append(f"| {it['id']} | {it['ch']:04d} | {short(it['text'], 50)} | {mv} |")
L.append(f"\n> 共 {len(key_items)} 条。此表为每章 Agent 必读清单，用于判断本章是否回收。\n")

L.append("## 二、在办伏笔全量（按埋设章排序）\n")
L.append("| ID | 埋设章 | 内容摘要 | 最近动向 |")
L.append("|---|---|---|---|")
for it in open_items:
    mv = it["partial_at"] and f"部分回收于{it['partial_at']}" or (it["last_touch"] and f"推进于{it['last_touch']}" or it["note"])
    L.append(f"| {it['id']} | {it['ch']:04d} | {short(it['text'])} | {mv} |")

L.append("\n## 三、已回收伏笔（按回收章排序）\n")
L.append("| ID | 埋设章 | 内容摘要 | 回收章 |")
L.append("|---|---|---|---|")
for it in sorted(done_items, key=lambda x: (x["recovered_at"], x["id"])):
    L.append(f"| {it['id']} | {it['ch']:04d} | {short(it['text'])} | {it['recovered_at']} |")

L.append("\n## 四、统计\n")
L.append(f"- 平均每章埋设：{len(lst) / len(blocks):.1f} 条")
L.append(f"- 回收率：{len(done_items) / max(len(lst), 1) * 100:.1f}%")
old_open = [x for x in open_items if x["ch"] <= blocks[-1][0] - 60]
L.append(f"- 埋设超过 60 章仍未回收：{len(old_open)} 条（长线伏笔，需重点跟踪）")

OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")
print(f"块数 {len(blocks)}｜伏笔 {len(lst)}｜在办 {len(open_items)}｜已回收 {len(done_items)}｜回收率 {len(done_items)/len(lst)*100:.1f}%")
