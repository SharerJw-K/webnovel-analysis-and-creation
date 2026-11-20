# -*- coding: utf-8 -*-
"""把全书按 10 章一批打包成独立文本束，供拆解批次读取。"""
import glob, os, re, json

SRC = r'D:/Agent/Antigravity/demo19/自然开景玄元妙有混沌太初大天尊'
OUT = r'D:/Agent/Antigravity/demo19/outputs/拆解_大天尊/_batches'
os.makedirs(OUT, exist_ok=True)

vols = {'001': '卷一：默认', '029': '卷二：灵幻世界', '057': '卷三：武道妖魔',
        '099': '卷四：四季如春', '181': '卷五：我看到你了'}

files = sorted(glob.glob(os.path.join(SRC, '[0-9]*.txt')))
files = [f for f in files if not os.path.basename(f).startswith('000')]

chapters = []
cur_vol, cur_c = None, 0
for f in files:
    key = os.path.basename(f)[:3]
    txt = open(f, encoding='utf-8').read()
    lines = [l.strip() for l in txt.split('\n') if l.strip()]
    newvol = key in vols
    if newvol:
        cur_vol = vols[key]
        cur_c = 0
    title = lines[1] if newvol else lines[0]
    title = re.sub(r'^第\d+章\s*', '', title)
    body = lines[2:] if newvol else lines[1:]
    cur_c += 1
    chapters.append({'g': len(chapters) + 1, 'vc': cur_c, 'vol': cur_vol,
                     'title': title, 'body': body, 'chars': len(txt)})

json.dump([{k: v for k, v in c.items() if k != 'body'} for c in chapters],
          open(os.path.join(OUT, '_meta.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

# 分批：001-003 已交付，从 004 起每 10 章一批
batches = []
start = 4
i = 0
while start <= len(chapters):
    end = min(start + 9, len(chapters))
    i += 1
    batches.append((f'B{i+1:02d}', start, end))
    start = end + 1

manifest = []
for name, s, e in batches:
    buf = [f'# 拆解文本束 {name}　全局章 {s:03d}–{e:03d}', '']
    for c in chapters[s-1:e]:
        buf.append(f'\n\n===== [全局章 {c["g"]:03d}] {c["vol"]} 卷内第{c["vc"]}章　《{c["title"]}》　字数{c["chars"]} =====\n')
        buf.extend(c['body'])
    p = os.path.join(OUT, f'{name}_text.txt')
    open(p, 'w', encoding='utf-8').write('\n'.join(buf))
    manifest.append({'batch': name, 'start': s, 'end': e,
                     'path': p.replace('\\', '/'),
                     'chars': os.path.getsize(p)})

json.dump(manifest, open(os.path.join(OUT, '_manifest.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('chapters', len(chapters), 'batches', len(batches))
for m in manifest:
    print(m['batch'], m['start'], m['end'], m['chars'])
