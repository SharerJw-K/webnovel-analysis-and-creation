# -*- coding: utf-8 -*-
"""合并分批产出 → 卷级索引 → 技法统计 → 全书章级总表"""
import re, glob, json, os, collections

BASE = r'D:/Agent/Antigravity/demo19/outputs/拆解_大天尊'
META = json.load(open(os.path.join(BASE, '_batches', '_meta.json'), encoding='utf-8'))
MAN = json.load(open(os.path.join(BASE, '_batches', '_manifest.json'), encoding='utf-8'))
volof = {m['g']: m['vol'] for m in META}
titof = {m['g']: m['title'] for m in META}
chars = {m['g']: m['chars'] for m in META}

VOLS = [('卷一', '默认', 1, 28), ('卷二', '灵幻世界', 29, 56), ('卷三', '武道妖魔', 57, 98),
        ('卷四', '四季如春', 99, 180), ('卷五', '我看到你了', 181, 243)]

# ---------- 1. 合并分批正文 ----------
merged = []
for i, m in enumerate(MAN):
    b = m['batch']
    p1 = os.path.join(BASE, '_parts', f'{b}_p1.md')
    p2 = os.path.join(BASE, '_parts', f'{b}_p2.md')
    txt = open(p1, encoding='utf-8').read().rstrip()
    if os.path.exists(p2):
        t2 = open(p2, encoding='utf-8').read().rstrip()
        # p2 若有自己的 H1 标题则去掉，保持单一文首
        t2 = re.sub(r'^# 《自然开景[^\n]*\n+(>[^\n]*\n+)*---\n+', '', t2)
        txt = txt + '\n\n---\n\n' + t2
    no = 3 + i
    fn = f'{no:02d}_{b}_第{m["start"]:03d}-{m["end"]:03d}章_段级拆解与索引.md'
    open(os.path.join(BASE, fn), 'w', encoding='utf-8').write(txt + '\n')
    merged.append((no, b, m['start'], m['end'], fn, len(txt)))
print('merged', len(merged))

# ---------- 2. 读入全部索引行 ----------
rows = []
for p in sorted(glob.glob(os.path.join(BASE, '_idx', '*.psv'))):
    for line in open(p, encoding='utf-8'):
        line = line.strip()
        if not line:
            continue
        c = [x.strip() for x in line.split('｜')]
        if len(c) != 14:
            print('SKIP bad col', p, len(c)); continue
        rows.append(c)
rows.sort(key=lambda r: (int(r[0][:3]), int(r[0][4:6])))
print('index rows', len(rows))

HDR = ('| ID | 摘要 | 剧情功能 | 人物行为/动机 | 冲突/悬念 | 信息差 | 文笔技法 | 节奏/视角/修辞 '
       '| 情绪基调 | 适用场景 | 避免场景 | 可迁移模板 | 关键词 | 关联段 |')
SEP = '|' + '---|' * 14

def table(rs):
    out = [HDR, SEP]
    for r in rs:
        out.append('| ' + ' | '.join(x.replace('|', '｜') for x in r) + ' |')
    return '\n'.join(out)

# ---------- 3. 卷级索引 ----------
idx_files = []
for i, (vname, vsub, a, b) in enumerate(VOLS):
    rs = [r for r in rows if a <= int(r[0][:3]) <= b]
    no = 27 + i
    fn = f'{no:02d}_总索引_{vname}{a:03d}-{b:03d}.md'
    head = [f'# 快速查询索引 · {vname}：{vsub}（全局章 {a:03d}–{b:03d}）', '',
            f'> 段数：{len(rs)}　覆盖章：{a:03d}–{b:03d}　回链方式：ID 前三位为全局章号，'
            f'在 `{3+ (a-4)//10 if a>=4 else 2:02d}_*` 批次文件中检索 `### {a:03d}-` 即可定位原段。', '',
            '> 字段说明：信息差 = 读者与角色掌握信息的落差；节奏/视角/修辞 为三合一压缩列；'
            '适用场景 / 避免场景 属"调用建议"，与前面的"文本描述"分栏。', '', '---', '']
    body = table(rs)
    # 本卷技法频次
    cnt = collections.Counter()
    for r in rs:
        for t in re.split(r'[、，,＋+/]', r[6]):
            t = t.strip()
            if 2 <= len(t) <= 10:
                cnt[t] += 1
    top = '、'.join(f'{k}({v})' for k, v in cnt.most_common(18))
    tail = ['', '---', '', f'## 本卷技法频次（前 18）', '', top, '']
    open(os.path.join(BASE, fn), 'w', encoding='utf-8').write('\n'.join(head) + '\n' + body + '\n' + '\n'.join(tail))
    idx_files.append((no, fn, len(rs)))
print('volume idx', idx_files)

# ---------- 4. 全书章级总表 ----------
chap_rows = []
for f in sorted(glob.glob(os.path.join(BASE, '0[2-9]_*.md')) + glob.glob(os.path.join(BASE, '[12][0-9]_*.md'))):
    s = open(f, encoding='utf-8').read()
    parts = re.split(r'^# 第 (\d{3}) 章[　 ]*(.*)$', s, flags=re.M)
    for j in range(1, len(parts), 3):
        g = int(parts[j]); title = parts[j+1].strip()
        seg = parts[j+2]
        def grab(label):
            m = re.search(r'\| ' + label + r' \| (.+?) \|', seg)
            return m.group(1).strip() if m else ''
        chap_rows.append((g, title, grab('体量'), grab('本章功能'), grab('节奏曲线'), grab('章末钩子'), len(re.findall(r'^### \d{3}-\d{2}', seg, re.M))))
chap_rows.sort()
seen = set(); uniq = []
for r in chap_rows:
    if r[0] in seen: continue
    seen.add(r[0]); uniq.append(r)
print('chapter rows', len(uniq), 'missing', [n for n in range(1, 244) if n not in seen][:10])

no = 33
fn = f'{no:02d}_全书243章_功能与节奏总表.md'
out = ['# 全书 243 章 · 功能与节奏总表', '',
       '> 每章一行：章号 / 卷 / 标题 / 字数 / 段数 / 本章功能（压缩）/ 节奏曲线 / 章末钩子。',
       '> 用途：写作时按"节奏曲线"检索可复用的章节骨架，按"章末钩子"检索钩子类型。', '',
       '| 章 | 卷 | 标题 | 字数 | 段数 | 本章功能（压缩） | 节奏曲线 | 章末钩子 |', '|---|---|---|---|---|---|---|---|']
for g, t, tl, func, rhythm, hook, ns in uniq:
    out.append(f'| {g:03d} | {volof.get(g,"")[:2]} | {t} | {chars.get(g,0)} | {ns} | {func[:150]} | {rhythm[:60]} | {hook[:60]} |')
open(os.path.join(BASE, fn), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print('wrote', fn)

# ---------- 5. 交付清单 ----------
files = sorted([f for f in os.listdir(BASE) if f.endswith('.md')])
man = ['# 交付清单 · 《自然开景玄元妙有混沌太初大天尊》全书段级拆解', '',
       f'- 段总数：**{len(rows)}**　章总数：**243**　卷：5',
       f'- 索引行：{len(rows)} 条（14 列，可回链到原段）', '',
       '| 文件 | 内容 | 字节 |', '|---|---|---|']
for f in files:
    sz = os.path.getsize(os.path.join(BASE, f))
    man.append(f'| `{f}` | {"总纲/目录" if f.startswith("01") else "索引" if "总索引" in f or "总表" in f else "段级拆解"} | {sz:,} |')
open(os.path.join(BASE, '00_交付清单.md'), 'w', encoding='utf-8').write('\n'.join(man) + '\n')
print('done')
