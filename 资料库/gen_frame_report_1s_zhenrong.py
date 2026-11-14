# -*- coding: utf-8 -*-
"""
阵容新批 逐帧 1 秒版渲染器（插图型，17 键新 schema）
输入：资料库/zhenrong_frame_json/*.json （子智能体逐帧真看产出）
输出：报告库/阵容新批/逐帧1秒版/<视频名>_逐帧深度学习报告_1秒版.docx
特点：与精编版（文本型无插图）互补——逐帧时间线每一帧都嵌入实际静帧原图 + 描述。
辅助函数复用 gen_refined_report_zhenrong（import 不触发其 __main__）。
"""
import json, os, sys, glob
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn

BASE = r'D:/Desktop/shandou'
LIB  = os.path.join(BASE, '资料库')
SRC  = os.path.join(LIB, 'zhenrong_frame_json')
OUT  = os.path.join(BASE, '报告库', '阵容新批', '逐帧1秒版')
os.makedirs(OUT, exist_ok=True)

sys.path.insert(0, LIB)
import gen_refined_report_zhenrong as G   # 复用 set_cjk/H/P/bullets/bracket_pos/strip_provenance 等

# 帧根路由：frames_dir 可能带或不带 阵容/ 前缀
_FRAME_ROOTS = [
    os.path.join(BASE, '抖音_frames_dense_1s', '阵容'),
    os.path.join(BASE, '抖音_frames_dense_1s'),
]
def frame_root(d):
    fd = (d.get('frames_dir') or '').strip()
    for rt in _FRAME_ROOTS:
        p = os.path.join(rt, fd)
        if os.path.isdir(p):
            return p
    return os.path.join(_FRAME_ROOTS[0], fd)

def add_image(doc, path, caption, width=4.8):
    if not path or not os.path.exists(path):
        G.P(doc, '[图缺失: {}]'.format(caption), bold=True)
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(path, width=Inches(width))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = cap.add_run(caption)
    r.font.name = 'Microsoft YaHei'
    r._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')
    r.font.size = Pt(9)
    r.font.color.rgb = RGBColor(0x5F, 0x5E, 0x5A)
    cap.paragraph_format.space_after = Pt(10)

def render(jpath):
    d = G.load_json(jpath)
    title = d.get('video_title') or os.path.splitext(os.path.basename(jpath))[0]
    doc = Document(); G.set_cjk(doc)
    doc.add_heading(title, level=0)

    # ---- 2026-08-24 复检同步：hero_builtin 跨队补全（与精编同源，空 skills 位置回退同 JSON 其他队伍同名武将）----
    import re as _re
    _teams_all = (d.get('entities') or {}).get('teams') or []
    hero_builtin = {h.get('name'): h.get('built_in_skill') for h in (d.get('entities') or {}).get('heroes') or [] if isinstance(h, dict)}
    for _t in _teams_all:
        for _pos in (_t.get('positions') or []):
            _h = (_pos.get('hero') or '').strip()
            _sk = _pos.get('skills') or []
            if _h and _sk and _h not in hero_builtin:
                hero_builtin[_h] = _sk[0]

    # ---- 报告元信息 ----
    G.P(doc, '【逐帧深度学习报告 · 1 秒版】', bold=True)
    G.P(doc, '视频时长：{} 秒 ｜ 帧数：{} ｜ 帧密度：1 秒/帧 ｜ 报告生成日期：{}'.format(
        d.get('duration_s'), d.get('frame_count'), G.GEN_DATE))
    G.P(doc, '帧目录：{}（{}）'.format(d.get('frames_dir'), d.get('resolution') or '?'))

    # ---- 一、核心结论与画面要点 ----
    G.H(doc, '一、核心结论与画面要点', 1)
    sm = d.get('summary') or {}
    if isinstance(sm, dict):
        kp = sm.get('key_points') or []
        if kp:
            G.H(doc, '一·核心结论', 2)
            for k in kp:
                _k = _re.sub(r'（[^）]*\bid=\d+[^）]*）', '', str(k))
                _k = G._clean_light(G._trim_dangle(_k))
                if _k:
                    doc.add_paragraph(G.bracket_pos(_k), style='List Bullet')
        vo = sm.get('visual_only') or []
        if vo:
            G.H(doc, '一·画面要点', 2)
            for v in vo:
                _v = G._clean_light(G._clean_hook(G._trim_dangle(G.strip_provenance(str(v)))))
                if _v:
                    doc.add_paragraph(G.bracket_pos(_v), style='List Bullet')
    else:
        G.P(doc, G.bracket_pos(str(sm)))

    # ---- 二、阵容详解（表格）----
    G.H(doc, '二、阵容详解（逐帧核实）', 1)
    teams = (d.get('entities') or {}).get('teams') or []
    if teams:
        star_ovr = G._star_override_map(d)
        vovr = G._vlabel_map(d)
        tbl = doc.add_table(rows=1, cols=5)
        tbl.style = 'Light Grid Accent 1'
        hdr = tbl.rows[0].cells
        hdr[0].text = '队伍 / 定位'
        hdr[1].text = '武将（阵营-兵种-星级）'
        hdr[2].text = '战法配置（已核对画面）'
        hdr[3].text = '宝物 / 词条'
        hdr[4].text = '备注'
        for t in teams:
            name = t.get('name') or '未命名'
            slot = t.get('slot') or ''
            mark = '推荐' if '推荐' in name else ('舍弃' if '舍弃' in name else '—')
            clean_name = __import__('re').sub(r'[（(]UP[^）)]*[）)]|[（(][^）)]*队[^）)]*[）)]', '', name).strip()
            row = tbl.add_row().cells
            row[0].text = '第{}队\n{}\n{}'.format(slot, clean_name, mark)
            heroes, skills_lines, gear_lines = [], [], []
            for pos in (t.get('positions') or []):
                hero = pos.get('hero') or '?'
                sk = (pos.get('skills') or [])
                # 2026-08-24 复检同步：空 skills 回退 hero_builtin（跨队补全），避免取错同名多版本
                innate = sk[0] if sk else (hero_builtin.get(hero) or '')
                lab = G._apply_star_override(vovr.get(hero) or G.hero_label_by_skill(innate, hero), hero, star_ovr)
                heroes.append('{} {}（{}）'.format(pos.get('pos'), hero, lab))
                skills_lines.append('{}：{}'.format(hero, ' / '.join(sk) if sk else '—'))
                g = pos.get('gear')
                tr = (pos.get('traits') or [])
                ut = (pos.get('unit_traits') or [])
                parts = []
                if g: parts.append('宝物 ' + str(g))
                if tr: parts.append('词条 ' + ' / '.join(tr))
                if ut: parts.append('兵种 ' + ' / '.join(ut))
                gear_lines.append('{}：{}'.format(hero, '；'.join(parts) if parts else '—'))
            row[1].text = '\n'.join(heroes)
            row[2].text = '\n'.join(skills_lines)
            row[3].text = '\n'.join(gear_lines)
            row[4].text = mark
        for i, w in enumerate([Inches(1.2), Inches(1.6), Inches(1.9), Inches(1.7), Inches(0.7)]):
            tbl.columns[i].width = w
    else:
        G.P(doc, '（本视频未结构化提取阵容，详见下方逐帧要点。）')

    # ---- 三、逐帧时间线（核心：每帧插图 + 描述）----
    G.H(doc, '三、逐帧时间线（画面实证）', 1)
    tl = d.get('timeline') or []
    if tl:
        root = frame_root(d)
        n_img = 0
        for seg in tl:
            if not isinstance(seg, dict):
                doc.add_paragraph(str(seg), style='List Bullet')
                continue
            rg = seg.get('range', ''); tt = seg.get('title', '')
            G.H(doc, '{} {}'.format(rg, tt), 2)
            for fr in (seg.get('frames') or []):
                ts = fr.get('ts', '')
                fn = fr.get('file', '')
                ds = G.bracket_pos(G._clean_hook(G._clean_ai(G._trim_dangle(G.strip_provenance(fr.get('desc', ''))))))
                fpath = os.path.join(root, fn) if fn else ''
                cap = '{} | {}'.format(ts, fn) if fn else ts
                add_image(doc, fpath, cap)
                if ds:
                    p = doc.add_paragraph(ds)
                    p.paragraph_format.space_after = Pt(8)
                n_img += 1
        G.P(doc, '共嵌入 {} 帧静帧原图。'.format(n_img))
    else:
        G.P(doc, '（无逐帧时间线。）')

    # ---- 四、逐帧独有价值 ----
    fv = d.get('frame_only_value') or []
    if fv:
        G.H(doc, '四、逐帧独有价值（只听音频得不出的结论）', 1)
        fv_items = []
        for v in fv:
            _v = G._clean_hook(G._clean_ai(G._trim_dangle(G.strip_provenance(str(v)))))
            if _v:
                fv_items.append(_v)
        G.bullets(doc, fv_items)

    # ---- 五、术语与黑话 ----
    glossary = d.get('glossary') or []
    if glossary:
        G.H(doc, '五、术语与黑话', 1)
        G.P(doc, '、'.join(str(g) for g in glossary))

    # ---- 六、来源与证据索引 ----
    src = d.get('sources') or []
    if src:
        G.H(doc, '六、来源与证据索引', 1)
        src_items = []
        for s in src:
            v = G._clean_hook(G._redact_path(G._clean_ai(G.strip_provenance(str(s)))))
            if v:
                src_items.append(v)
        G.bullets(doc, src_items)

    # ---- 七、局限与无法确认 ----
    lim = d.get('limitations') or []
    if lim:
        G.H(doc, '七、局限与无法确认（查不到/存疑）', 1)
        lim_items = []
        for x in lim:
            v = G._clean_hook(G.strip_provenance(str(x)))
            if v:
                lim_items.append(v)
        G.bullets(doc, lim_items)

    # ---- 八、AI 智能体主动推断内容 ----
    ai = d.get('ai_inference') or []
    if ai:
        G.H(doc, '八、AI 智能体主动推断内容（非视频原话，供参考）', 1)
        G.P(doc, '以下为 AI 基于本地官方资料库 + 网易大神核验后对游戏机制的主动推断与延伸建议，非视频原话、不代表作者观点。')
        for it in ai:
            if isinstance(it, dict):
                txt = G.bracket_pos(G._clean_hook(G.strip_provenance(G._clean_ai(it.get('point') or ''))))
                ev = G.bracket_pos(G._clean_hook(G.strip_provenance(G._clean_ai(it.get('evidence') or ''))))
                cf = it.get('confidence') or ''
                line = '· ' + str(txt)
                if ev: line += '（依据：' + str(ev) + '）'
                if cf: line += ' [置信度：' + str(cf) + ']'
                doc.add_paragraph(line, style='List Bullet')
            else:
                doc.add_paragraph('· ' + G.bracket_pos(str(it)), style='List Bullet')

    G.P(doc, '报告生成日期：' + G.GEN_DATE)
    out_path = os.path.join(OUT, title + '_逐帧深度学习报告_1秒版.docx')
    doc.save(out_path)
    return out_path

if __name__ == '__main__':
    targets = sys.argv[1:] or sorted(glob.glob(os.path.join(SRC, '*.json')))
    for p in targets:
        try:
            op = render(p)
            print('OK ->', op)
        except Exception as e:
            print('FAIL', os.path.basename(p)[:30], e)
