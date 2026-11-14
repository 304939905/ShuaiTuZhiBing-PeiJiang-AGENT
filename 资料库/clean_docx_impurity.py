# -*- coding: utf-8 -*-
"""
直接清理 1秒版 docx 的杂质（不重渲染，避免把陈旧 frame_json 错误带回）。
- 纯片头/片尾/过渡/关注/订阅类零信息帧：连图带说明一起删
- 粉丝投稿类视频：caption/标题中的粉丝名/头像改为「投稿N」，删除纯粉丝ID/头像的 visual_only/correction/frame_only_value 条目
仅对 fan_mode=True 的文件执行粉丝相关清理；45 份轻量文件只跑 PURE_DROP。
"""
import os, re, sys, json, shutil
from docx import Document

BASE = r"D:\Desktop\shandou"
OLD56 = os.path.join(BASE, "报告库", "旧56项目", "逐帧1秒版")
KAIHUANG = os.path.join(BASE, "报告库", "开荒", "逐帧1秒版")
FRAME_JSON_DIR = os.path.join(BASE, "资料库", "frame_json")

# 6 份高杂质（粉丝投稿/答疑）文件，fan_mode=True（用稳定子串匹配实际 docx 名）
FAN_FILES = {
    "攻其篇—粉丝投稿解析",
    "神赏体系粉丝投稿解析",
    "垒实篇投稿讲解",
    "战磐篇粉丝答疑",
    "垒实体系克制关系",
    "粉丝赞不绝口的队伍",
}

PURE_DROP = re.compile(
    r'(片尾画面|片尾：|片头画面|UP主.{0,15}片头|'
    r'点个关注|关注我贴纸|下期干货不迷路|纯过渡动画|'
    r'交叉刀剑特写镜头|手机拍摄屏幕风格|UP主.{0,12}头像与名称出现|'
    r'开篇画面.{0,24}头像|武将立绘.*关注|火兽精灵表情包)'
)
# 纯品牌/片头片尾类 bullet（visual_only / frame_only_value 段），与游戏内容无关
BRANDING_BULLET = re.compile(
    r'片尾大字|片头画面|点赞动画|下期干货不迷路|点个关注|关注我贴纸|'
    r'纯过渡动画|交叉刀剑特写|手机拍摄屏幕|UP主「|武将立绘.*关注|'
    r'火兽精灵表情包|片尾：.*下期|片尾.*关注'
)
FAN_MARK = re.compile(r'粉丝「|粉丝\s*ID|头像为|（头像|头像样式|粉丝\w*投稿|粉丝真实')
CN_NUM = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}

def has_drawing(p):
    x = p._p.xml
    return ('w:drawing' in x) or ('<a:graphic' in x)

def img_before(p, paras):
    try:
        i = paras.index(p)
    except ValueError:
        return None
    for j in range(i - 1, -1, -1):
        if has_drawing(paras[j]):
            return paras[j]
    return None

def is_heading(p):
    try:
        return p.style.name.startswith("Heading")
    except Exception:
        return False

def is_bullet(p):
    try:
        return p.style.name == "List Bullet"
    except Exception:
        return False

def extract_label(title):
    m = re.search(r'投稿([一二三四五六七八九十])', title)
    if m:
        return "投稿" + m.group(1)
    return None

def clean_heading(title):
    t = re.sub(r'粉丝「[^」]*」', '', title)
    t = re.sub(r'：——+', '：', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def clean_desc(desc, label):
    d = desc
    if label:
        d = re.sub(r'粉丝「[^」]*」\s*投稿', label, d)   # 粉丝「X」投稿 -> 投稿一
        d = re.sub(r'粉丝「[^」]*」', label, d)          # 残留 粉丝「X」 -> 投稿一
        d = re.sub(r'粉丝\w*投稿', label, d)            # 粉丝投稿(无引号) -> 投稿一
    else:
        d = re.sub(r'粉丝「[^」]*」', '投稿者', d)
    # 删除头像/粉丝ID 相关杂质
    d = re.sub(r'（头像为[^）]*）', '', d)
    d = re.sub(r'[（(][^）)]*头像[^）)]*[)）]', '', d)
    d = re.sub(r'[\u4e00-\u9fffA-Za-z·]*头像', '', d)
    d = re.sub(r'非转写中的「[^」]*」', '', d)
    d = re.sub(r'粉丝\s*ID\s*为「[^」]*」', '', d)
    d = re.sub(r'\s+', ' ', d).strip(' ，,')
    return d

def decide(desc, label, fan_mode):
    if PURE_DROP.search(desc):
        return 'drop'
    if fan_mode and FAN_MARK.search(desc):
        return 'rewrite'
    return 'keep'

def process_tables(doc, fan_mode, log):
    dropped = 0
    for t in doc.tables:
        for r in list(t.rows):
            cells = [c.text for c in r.cells]
            item = cells[0] if cells else ""
            if fan_mode and re.search(r'粉丝\s*ID|头像|粉丝确认|粉丝「', item):
                r._element.getparent().remove(r._element)
                dropped += 1
                log.append(("table_row_drop", "", item))
    return dropped


def process(docx_path, fan_mode, log):
    doc = Document(docx_path)
    paras = doc.paragraphs
    to_delete = set()
    to_edit = {}  # para -> new_text
    section_label = None
    cur_heading = None

    for p in paras:
        txt = p.text
        hm = re.match(r'^(\d{2}:\d{2})[–-](\d{2}:\d{2})\s+(.*)$', txt)
        if hm and is_heading(p):
            title = hm.group(3)
            nt = clean_heading(title)
            if nt != title:
                to_edit[p] = nt
                log.append(("heading", os.path.basename(docx_path), title + "  ->  " + nt))
            section_label = extract_label(title)
            cur_heading = title
            continue
        if is_heading(p):
            cur_heading = txt
            continue
        cm = re.match(r'^(\d{2}:\d{2})\s*\|\s*(.*)$', txt)
        if cm:
            ts, desc = cm.group(1), cm.group(2)
            act = decide(desc, section_label, fan_mode)
            if act == 'drop':
                img = img_before(p, paras)
                to_delete.add(p)
                if img:
                    to_delete.add(img)
                log.append(("frame_drop", os.path.basename(docx_path), ts + " | " + desc))
            elif act == 'rewrite':
                nd = clean_desc(desc, section_label)
                if nd != desc:
                    to_edit[p] = ts + " | " + nd
                    log.append(("frame_rewrite", os.path.basename(docx_path),
                                ts + " | " + desc + "  ->  " + ts + " | " + nd))
            continue
        if is_bullet(p):
            if fan_mode and re.search(r'粉丝\s*ID|头像为|头像样式|粉丝真实', txt):
                to_delete.add(p)
                log.append(("bullet_drop", os.path.basename(docx_path), txt))
            elif re.search(BRANDING_BULLET, txt):
                to_delete.add(p)
                log.append(("bullet_drop_brand", os.path.basename(docx_path), txt))
            continue
        if fan_mode and cur_heading and ('修正' in cur_heading) and re.search(r'粉丝\s*ID|头像|粉丝真实', txt):
            to_delete.add(p)
            log.append(("correction_drop", os.path.basename(docx_path), txt))

    # 空段落清理：无保留帧的 level-2 小节标题删掉
    paras2 = doc.paragraphs
    for p in list(paras2):
        if p in to_delete or p in to_edit:
            continue
        if is_heading(p) and re.match(r'^\d{2}:\d{2}[–-]\d{2}:\d{2}\s', p.text):
            idx = paras2.index(p)
            nxt = None
            for q in paras2[idx+1:]:
                if is_heading(q) and re.match(r'^\d{2}:\d{2}[–-]\d{2}:\d{2}\s', q.text):
                    nxt = q
                    break
            seg = paras2[idx+1: paras2.index(nxt)] if nxt else paras2[idx+1:]
            has_content = any((s not in to_delete) and re.match(r'^\d{2}:\d{2}\s*\|', s.text or '')
                              for s in seg)
            if not has_content:
                to_delete.add(p)
                log.append(("empty_heading_drop", os.path.basename(docx_path), p.text))

    # 执行
    for p, nt in to_edit.items():
        if p not in to_delete:
            p.text = nt
    for p in to_delete:
        try:
            p._element.getparent().remove(p._element)
        except Exception:
            pass
    tbl_drop = process_tables(doc, fan_mode, log)
    doc.save(docx_path)
    return len(to_delete) + tbl_drop, len(to_edit)

def main():
    targets = []
    for f in os.listdir(OLD56):
        if not f.endswith(".docx"):
            continue
        name = f[:-len("_逐帧深度学习报告_1秒版.docx")]
        fan = any(name.startswith(x) or x in name for x in FAN_FILES)
        targets.append((os.path.join(OLD56, f), fan, name))
    log = []
    summary = []
    for path, fan, name in targets:
        n_del, n_ed = process(path, fan, log)
        summary.append((name[:30], "fan" if fan else "light", n_del, n_ed))
    # 写日志
    lg = os.path.join(BASE, "资料库", "clean_impurity_log.txt")
    with open(lg, "w", encoding="utf-8") as fh:
        for row in log:
            fh.write(" | ".join(str(x) for x in row) + "\n")
        fh.write("\n=== SUMMARY ===\n")
        for s in summary:
            fh.write(" | ".join(str(x) for x in s) + "\n")
    print("log ->", lg)
    print("files processed:", len(targets))
    for s in summary:
        print(s)

if __name__ == "__main__":
    main()
