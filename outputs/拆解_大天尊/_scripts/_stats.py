# -*- coding: utf-8 -*-
"""从 1288 条索引行生成技法/功能/场景/关键词索引数据，输出到 _stats.txt"""
import glob, os, re, collections, json

BASE = r'D:/Agent/Antigravity/demo19/outputs/拆解_大天尊'
rows = []
for p in sorted(glob.glob(os.path.join(BASE, '_idx', '*.psv'))):
    for line in open(p, encoding='utf-8'):
        line = line.strip()
        if not line: continue
        c = [x.strip() for x in line.split('｜')]
        if len(c) == 14: rows.append(c)
rows.sort(key=lambda r: (int(r[0][:3]), int(r[0][4:6])))
N = len(rows)

out = []
def w(s=''): out.append(s)

# 技法
tech = collections.Counter(); techid = collections.defaultdict(list)
for r in rows:
    seen = set()
    for t in re.split(r'[、，,＋+/；;]', r[6]):
        t = re.sub(r'[（(].*?[）)]', '', t).strip().strip('。.、 ')
        if 2 <= len(t) <= 10 and t not in seen:
            seen.add(t); tech[t] += 1; techid[t].append(r[0])
w('## 技法频次 TOP50')
for k, v in tech.most_common(50):
    w(f'- {k}｜{v}｜{"、".join(techid[k][:6])}')

# 功能标签
FUNC = ['铺垫','伏笔','信息释放','冲突升级','转折','人物揭示','节奏缓冲','喜剧换气','战力校准',
        '世界观补完','收束','钩子','悬念','群像','日常','战斗','情感','升级','规则交付','余波']
fw = collections.Counter(); fid = collections.defaultdict(list)
for r in rows:
    hit = [f for f in FUNC if f in r[2]]
    for f in hit: fw[f] += 1; fid[f].append(r[0])
w('\n## 功能频次')
for k, v in fw.most_common():
    w(f'- {k}｜{v}｜{"、".join(fid[k][:8])}')

# 场景
SC = ['开篇','转场','冲突前','高潮','收束','人物出场','设定交付','战斗','对话','日常','感情',
      '悬疑','恐怖','群像','回忆','章末','卷首','打脸','装逼','突破','告别','死亡']
sw = collections.Counter(); sid = collections.defaultdict(list)
for r in rows:
    hit = [s for s in SC if s in r[9]]
    for s in hit: sw[s] += 1; sid[s].append(r[0])
w('\n## 适用场景频次')
for k, v in sw.most_common():
    w(f'- {k}｜{v}｜{"、".join(sid[k][:8])}')

# 避免
AV = ['战斗','高潮','群像','多线','感情','死亡','悲伤','紧张','快节奏','战斗章','悬念']
aw = collections.Counter(); aid = collections.defaultdict(list)
for r in rows:
    hit = [a for a in AV if a in r[10]]
    for a in hit: aw[a] += 1; aid[a].append(r[0])
w('\n## 避免条件频次')
for k, v in aw.most_common():
    w(f'- {k}｜{v}｜{"、".join(aid[k][:6])}')

# 关键词
kw = collections.Counter(); kid = collections.defaultdict(list)
for r in rows:
    for k in re.split(r'[、，,;；]', r[12]):
        k = k.strip()
        if 1 < len(k) <= 12:
            kw[k] += 1; kid[k].append(r[0])
w('\n## 关键词 TOP80')
for k, v in kw.most_common(80):
    w(f'- {k}｜{v}｜{"、".join(kid[k][:5])}')

# 情绪
emo = collections.Counter()
for r in rows:
    for e in re.split(r'[、，,;；]', r[8]):
        e = e.strip()
        if 1 < len(e) <= 8: emo[e] += 1
w('\n## 情绪基调 TOP30')
w('、'.join(f'{k}({v})' for k, v in emo.most_common(30)))

# 章长/段数
meta = json.load(open(os.path.join(BASE, '_batches', '_meta.json'), encoding='utf-8'))
segs = collections.Counter(r[0][:3] for r in rows)
w('\n## 体量')
w(f'总段 {N}，章 {len(segs)}，平均段/章 {N/len(segs):.2f}')
lens = sorted(meta, key=lambda m: m['chars'])
w('最短章 ' + '；'.join(f'{m["g"]:03d}({m["chars"]})' for m in lens[:5]))
w('最长章 ' + '；'.join(f'{m["g"]:03d}({m["chars"]})' for m in lens[-5:]))

open(os.path.join(BASE, '_stats.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out)[:6000])
