# -*- coding: utf-8 -*-
"""生成非标 version_label 人工裁决查验单（单文件 HTML，base64 内嵌帧图）"""
import base64, os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = r'D:/Desktop/shandou/抖音_frames_dense_1s/阵容'

# (帧相对路径, 组名, 帧内问题)
FRAMES = [
    ('video_来来来兄弟们，继续配将，免费粉丝..._top_0_3/frame_000066_00h01m05s000ms.jpg', 'A', '核对本页各武将兵种/星级是否与下方推导表一致'),
    ('video_来来来兄弟们，继续配将，免费粉丝..._top_0_3/frame_000071_00h01m10s000ms.jpg', 'A', '核对本页各武将兵种/星级是否与下方推导表一致'),
    ('video_来来来兄弟们，继续配将，免费粉丝..._top_0_3/frame_000064_00h01m03s000ms.jpg', 'A', '核对本页各武将兵种/星级是否与下方推导表一致'),
    ('video_来来来兄弟们，继续配将，免费粉丝..._top_0_3/frame_000036_00h00m35s000ms.jpg', 'A', '核对队伍卡三名武将兵种/星级'),
    ('video_来来来兄弟们，继续配将，免费粉丝..._top_0_3/frame_000038_00h00m37s000ms.jpg', 'A', '核对队伍卡三名武将兵种/星级'),
    ('video_来来来兄弟们，继续配将，免费粉丝..._top_0_3/frame_000013_00h00m12s000ms.jpg', 'A', '核对队伍卡三名武将兵种/星级'),
    ('video_来来来兄弟们，继续配将，免费粉丝..._top_0_3/frame_000022_00h00m21s000ms.jpg', 'Q2', '【Q2】武将库该行（夏侯惇/郭嘉/曹彰）：卡上阵营显示「魏」还是「蜀」？'),
    ('video_来来来兄弟们，继续配将，免费粉丝..._top_0_3/frame_000027_00h00m26s000ms.jpg', 'A', '核对队伍卡/武将页兵种星级（甄洛是否在 5 星页末尾）'),
    ('video_来来来兄弟们，继续配将，免费粉丝..._top_0_3/frame_000032_00h00m31s000ms.jpg', 'Q3', '【Q3-旁证】此页甄洛若可见：她出现在几星页？兵种图标是什么？'),
    ('video_免费粉丝配将第九期，平民专业配将..._top_0_2/frame_000017_00h00m16s000ms.jpg', 'Q3', '【Q3-旁证】甄洛被列进「4星女将池」——确认该页口径'),
    ('video_免费粉丝配将第九期，平民专业配将..._top_0_2/frame_000038_00h00m37s000ms.jpg', 'Q3', '【Q3-裁决帧】小流氓队阵容卡甄洛位：几星？弓还是别的兵种？'),
    ('video_免费粉丝配将第九期，平民专业配将..._top_0_2/frame_000054_00h00m53s000ms.jpg', 'Q4', '【Q4】第四队阵容卡华雄：骑还是步？'),
    ('率土平民队伍之甘宁碰瓷队/frame_000007_00h00m06s000ms.jpg', 'Q5', '【Q5】卡面「4星极/5星极」：「极」字在标签里保留还是去掉？'),
    ('率土平民队伍之甘宁碰瓷队/frame_000016_00h00m15s000ms.jpg', 'Q5', '【Q5】同上：极标记处理方式'),
    ('配将点评/frame_000017_00h00m16s000ms.jpg', 'Q6', '【Q6】王异卡：阵营「魏」还是「群」？星级 4 还是 5？'),
    ('配将点评/frame_000097_00h01m36s000ms.jpg', 'Q7', '【Q7】第三队大营荀彧：阵营「汉」还是「魏」？（顺带卫瓘位确认）'),
]

TABLE_A = [
    ('曹彰', '魏-骑-5星', '两版本皆魏骑'), ('曹操', '魏-骑-5星', '魏武之世=魏骑版'),
    ('甘宁', '吴-步-5星', '侵掠如火=吴步版'), ('司马炎', '晋-步-5星', '官方唯一版本'),
    ('貂蝉', '群-步-5星', '白楼独舞=群步版'), ('刘备', '蜀-步-5星', '蜀版唯一步'),
    ('夏侯惇', '魏-骑-5星', '两版本皆魏骑'), ('袁术', '群-步-5星', '两版本皆群步'),
    ('典韦', '魏-步-5星', '两版本皆魏步'), ('赵云', '蜀-步-5星', '5星版皆蜀步'),
    ('张机', '汉-弓-5星', '官方唯一版本'), ('严颜', '蜀-骑-5星', '5星版=蜀骑'),
    ('孙权', '吴-弓-5星', '官方唯一5星版'), ('华雄', '群-骑-5星', '5星版=群骑'),
]

def b64(p):
    with open(p, 'rb') as f:
        return base64.b64encode(f.read()).decode()

rows = []
for i, (rel, grp, q) in enumerate(FRAMES, 1):
    p = os.path.join(ROOT, rel.replace('/', os.sep))
    if not os.path.isfile(p):
        rows.append(f'<div class="card err">帧缺失：{rel}</div>'); continue
    data = b64(p)
    fn = os.path.basename(rel)
    vid = os.path.dirname(rel)
    rows.append(f'''<div class="card g{grp}">
<div class="head"><span class="no">帧 {i}</span><span class="grp">组 {grp}</span><span class="fn">{vid[:22]}… / {fn}</span></div>
<div class="q">{q}</div>
<img src="data:image/jpeg;base64,{data}" alt="{fn}">
</div>''')

tbl = ''.join(f'<tr><td>{h}</td><td class="lab">{v}</td><td>{r}</td></tr>' for h, v, r in TABLE_A)

html = f'''<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8">
<title>非标 version_label 人工裁决查验单（2026-08-23）</title>
<style>
body{{font-family:"Microsoft YaHei",sans-serif;margin:0;background:#f5f6f8;color:#222;}}
header{{background:#1f3a5f;color:#fff;padding:18px 28px;}}
header h1{{margin:0;font-size:20px;}} header p{{margin:6px 0 0;font-size:13px;opacity:.85;}}
.wrap{{max-width:1080px;margin:0 auto;padding:20px;}}
.qlist{{background:#fff;border:1px solid #dde;border-radius:10px;padding:16px 22px;margin-bottom:24px;}}
.qlist h2{{font-size:16px;margin:0 0 10px;color:#1f3a5f;}}
.qlist ol{{margin:0;padding-left:22px;font-size:14px;line-height:1.9;}}
table{{border-collapse:collapse;width:100%;font-size:13px;margin:8px 0 16px;}}
th,td{{border:1px solid #ccd;padding:5px 10px;}}
th{{background:#eef2f8;}} .lab{{color:#b30;font-weight:600;white-space:nowrap;}}
.card{{background:#fff;border-radius:10px;padding:14px;margin:18px 0;box-shadow:0 1px 4px rgba(0,0,0,.08);}}
.card.err{{color:#c00;}}
.head{{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:8px;}}
.no{{background:#1f3a5f;color:#fff;border-radius:6px;padding:2px 10px;font-size:13px;font-weight:700;}}
.grp{{background:#e8f0e8;border:1px solid #9c9;border-radius:6px;padding:2px 8px;font-size:12px;color:#272;}}
.card.gQ2 .grp,.card.gQ3 .grp,.card.gQ4 .grp,.card.gQ5 .grp,.card.gQ6 .grp,.card.gQ7 .grp{{background:#fdf0e0;border-color:#e8a04a;color:#a50;}}
.fn{{font-size:11px;color:#888;font-family:Consolas,monospace;}}
.q{{font-size:15px;font-weight:600;color:#b30;margin-bottom:10px;}}
img{{max-width:100%;border:1px solid #ddd;border-radius:6px;display:block;}}
footer{{padding:14px 28px;color:#888;font-size:12px;}}
</style></head><body>
<header><h1>非标 version_label 裁决查验单</h1>
<p>4 个视频 · 16 帧 · 8 个问题（Q1 大表 + Q2–Q7 + Q8 确认项）——答完我统一改 JSON 并重渲报告</p></header>
<div class="wrap">
<div class="qlist"><h2>待回答问题清单</h2>
<ol>
<li><b>Q1（组A 帧1-6/8）</b>：下表 14 将兵种推导是否与画面一致？答「全对」或指出错的行。</li>
<li><b>Q2（帧7 武将库）</b>：夏侯惇/郭嘉/曹彰行，卡上阵营显示「魏」还是「蜀」？</li>
<li><b>Q3（帧9/10/11）</b>：甄洛星级几星？兵种？官方库=4星群弓，但两视频证据打架。</li>
<li><b>Q4（帧12）</b>：华雄兵种骑还是步？</li>
<li><b>Q5（帧13/14）</b>：卡面「4星极/5星极」——标签里「极」保留还是去掉？</li>
<li><b>Q6（帧15）</b>：王异阵营「魏」还是「群」？星级 4 还是 5？</li>
<li><b>Q7（帧16）</b>：第三队荀彧阵营「汉」还是「魏」？</li>
<li><b>Q8（无帧，直接答）</b>：卫瓘旧标签「官方库无此名」有误，按「晋-步-5星」修复，是否同意？</li>
</ol>
<table><tr><th>武将</th><th>推导标签</th><th>依据</th></tr>{tbl}</table>
<p style="font-size:12px;color:#666">依据=hero_extra.json 阵营/兵种/星级 + 自带战法（methodName）锁定唯一版本。</p>
</div>
{''.join(rows)}
</div>
<footer>原件路径：D:\\Desktop\\shandou\\资料库\\非标标签裁决_20260823.html · 帧源：抖音_frames_dense_1s/阵容/</footer>
</body></html>'''

out = r'D:/Desktop/shandou/资料库/非标标签裁决_20260823.html'
open(out, 'w', encoding='utf-8').write(html)
print('写出:', out, '%.2f MB' % (os.path.getsize(out) / 1048576), '帧卡:', len(rows))
