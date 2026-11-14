# -*- coding: utf-8 -*-
"""非标 version_label 定案修复（2026-08-23）：
来来来兄弟们 14 将 / 第九期华雄 / 配将点评 王异荀彧卫瓘程昱。
待用户裁决项（甄洛星级、碰瓷队「极」格式）不动。
"""
import json, io, sys, shutil, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = 'zhenrong_frame_json/'
# (文件, {武将: (旧标签, 新标签, 依据)})
FIX = {
    'video_来来来兄弟们，继续配将，免费粉丝..._top_0_3.json': {
        '曹彰': ('魏-? -5星', '魏-骑-5星', '用户画面确认'),
        '曹操': ('魏-? -5星', '魏-骑-5星', '用户画面确认+魏武之世'),
        '甘宁': ('吴-? -5星', '吴-步-5星', '用户画面确认+侵掠如火'),
        '司马炎': ('晋-? -5星', '晋-步-5星', '用户画面确认+官方唯一'),
        '貂蝉': ('群-? -5星', '群-步-5星', '用户画面确认+白楼独舞'),
        '刘备': ('蜀-? -5星', '蜀-步-5星', 'frame13武将库「蜀刘备」+5星蜀步唯一'),
        '袁术': ('群-? -5星', '群-步-5星', '官方唯一版本'),
        '典韦': ('魏-? -5星', '魏-步-5星', '官方唯一版本'),
        '赵云': ('蜀-? -5星', '蜀-步-5星', 'frame13武将库「蜀赵云」+5星蜀步唯一'),
        '张机': ('汉-? -5星', '汉-弓-5星', '官方唯一版本'),
        '严颜': ('蜀-? -5星', '蜀-骑-5星', '5星版唯一蜀骑'),
        '夏侯惇': ('魏-? -5星', '魏-骑-5星', '官方唯一版本'),
        '孙权': ('吴-? -5星', '吴-弓-5星', '官方唯一版本'),
        '华雄': ('群-? -5星', '群-骑-5星', 'frame13武将库「群华雄」5星页+5星群骑唯一'),
    },
    'video_免费粉丝配将第九期，平民专业配将..._top_0_2.json': {
        '华雄': ('群-步/骑-5星', '群-骑-5星', 'frame54自带将出关西=5星版(4星版为重斩)'),
    },
    '配将点评.json': {
        '王异': ('群-弓-5星', '魏-弓-5星', '官方唯一版本(世仇)'),
        '荀彧': ('魏-骑-5星 & 魏-步-5星', '魏-骑-5星 & 汉-步-5星', '三队举贤决机=汉-步版+作者口播「汉荀彧」'),
        '卫瓘': ('无法识别（OCR存疑，官方库无此名）', '晋-步-5星', '官方库「卫瓘-晋-步·持节镇西」唯一+画面持节镇西'),
        '程昱': ('魏-弓-5星 & 魏-步-3星', '魏-弓-5星', '标准魏智程昱=审时定计魏弓(被顶替未上场)'),
    },
}

for fn, fixes in FIX.items():
    p = BASE + fn
    d = json.load(open(p, encoding='utf-8'))
    n_ok = 0
    changed = []
    for h in d['entities']['heroes']:
        if h['name'] in fixes:
            old, new, why = fixes[h['name']]
            changed.append((h['name'], h['version_label'], new, why))
            h['version_label'] = new
            n_ok += 1
    # desc 层同步修正（画面判读记录中的旧标签表述）
    txt = json.dumps(d, ensure_ascii=False, indent=2)
    rep = [
        ('（群-步/骑 4红点 Lv.40 ，将出关西', '（群-骑 4红点 Lv.40 ，将出关西'),
        ('大营王异（群-弓 4 星 SR', '大营王异（魏-弓 5 星'),
        ('大营荀彧（魏-步 4 星 SR', '大营荀彧（汉-步 5 星'),
        ('（魏-步 4 星 SR，Lv.40，，2 红）带举贤决机', '（汉-步 5 星，Lv.40，，2 红）带举贤决机'),
    ]
    for a, b in rep:
        txt = txt.replace(a, b)
    # 卫瓘 desc 表述修正：官方库误判句
    txt = txt.replace('中军「卫瓘」（画面字面，官方库 names 无此武将，疑为「卫瓘」/「张卫」等同形误读，Lv.40，，3 红）',
                      '中军卫瓘（晋-步 5 星，Lv.40，，3 红）')
    shutil.copyfile(p, p + '.bak_vlabel')
    open(p, 'w', encoding='utf-8').write(txt)
    print('%s: 改 %d 将标签, 备份 .bak_vlabel' % (fn[:36], n_ok))
    for name, o, n, why in changed:
        print('   %s: %r -> %r (%s)' % (name, o, n, why))

# ---- 复核 ----
import re
pat = re.compile(r'^(汉|魏|蜀|吴|群|晋)-(骑|步|弓|弓/步|步/弓|骑-5星 & 汉-步|魏-骑-5星 & 汉-步)-[45]星$')
ok_dual = re.compile(r'^(魏-骑-5星 & 汉-步-5星)$')
print('\n== 复核 ==')
for fn, fixes in FIX.items():
    p = BASE + fn
    d = json.load(open(p, encoding='utf-8'))
    bad = [(h['name'], h['version_label']) for h in d['entities']['heroes']
           if h.get('version_label') and not (pat.match(h['version_label']) or ok_dual.match(h['version_label']))]
    print(fn[:36], '非标残留:', bad if bad else '0')
    # 旧标签字样全文残留
    txt = open(p, encoding='utf-8').read()
    for w in ['-? -5星', '群-步/骑', '官方库无此名', '魏-步 4 星 SR']:
        c = txt.count(w)
        if c: print('   残留字样:', w, c)
print('\n语法: 全部 json.load 通过')
