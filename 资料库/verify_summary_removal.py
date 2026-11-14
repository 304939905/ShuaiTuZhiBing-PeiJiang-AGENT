# -*- coding: utf-8 -*-
import sys, glob, os
from docx import Document
CANON = r'D:/Desktop/shandou/报告库/阵容新批/精编'
TMP = r'D:/tmp/zh_rerender'
locked = {
  'video_月卡配将不一定配的就好，但是免费..._top_0_3_精编学习报告.docx',
  '率土平民队伍之甘宁碰瓷队_精编学习报告.docx',
}
files = sorted(glob.glob(os.path.join(CANON, '*.docx')))
files = [f for f in files if not os.path.basename(f).startswith('~$')]
all_ok = True
for fp in files:
    base = os.path.basename(fp)
    path = os.path.join(TMP, base) if base in locked else fp
    d = Document(path)
    paras = [(p.style.name, p.text.strip()) for p in d.paragraphs]
    h1 = [t for s, t in paras if s == 'Heading 1']
    has_old = any('内容摘要' in t for s, t in paras)
    has_new = any(t == '一、核心结论与画面要点' for s, t in paras)
    has_kp = any(t == '一·核心结论' for s, t in paras)
    has_vp = any(t == '一·画面要点' for s, t in paras)
    idx = next((i for i, (s, t) in enumerate(paras) if t == '一、核心结论与画面要点'), -1)
    leftover = False
    if idx >= 0:
        for i in range(idx + 1, len(paras)):
            s, t = paras[i]
            if t == '一·核心结论': break
            if s == 'Normal' and t: leftover = True; break
            if s.startswith('Heading'): break
    nine = len(h1) == 9
    ok = (not has_old) and has_new and has_kp and has_vp and (not leftover) and nine
    all_ok = all_ok and ok
    src = 'TMP' if base in locked else 'CAN'
    extra = ('  H1列表=' + ' | '.join(h1)) if not nine else ''
    print(f"{'OK  ' if ok else 'FAIL'} [{src}] {base[:40]:40} | H1={len(h1)} 旧摘要={has_old} 新章={has_new} 结论={has_kp} 画面={has_vp} 残留={leftover}{extra}")
print('ALL_OK=', all_ok)
