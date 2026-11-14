# -*- coding: utf-8 -*-
# 旧一批阶段1 修补：高置信12处名误识 + 两小一大星级/名字错误
# 双修：精准改 docx 当前交付物 + 同步改 frame_json 母本（避免未来重渲复发）
import os, json, shutil, sys
from docx import Document

BASE = r"D:\Desktop\shandou"
BKUP = r"D:\WorkBuddyData\shandou_patch_backup_20260820A"
os.makedirs(BKUP, exist_ok=True)

# ---- 简单 token 替换（docx 与母本 frame_json 通用）----
SIMPLE = {
    "血溅黄沙": "血溅黄砂",
    "鬼旅": "鬼谋",
    "王越": "王异",
    "司马沿": "司马懿",
    "急战": "急救",
    "回水": "回马",
    "法谋": "法正",
    "司马盐": "司马懿",
    "折击": "追击",
    "制策": "孙策",
    "至策": "孙策",
}

# ---- 两小一大 上下文专属替换（避免朱桓两处混淆）----
CONTEXT = [
    ("王粲（四星白袍文官）", "王业（三星白袍文官）"),
    ("王烈（四星白袍老人）", "王烈（三星白袍老人）"),
    ("朱桓（Lv.20 白袍青年，4 星）", "朱治（Lv.20 白袍青年，4 星）"),
    ("朱桓（二星材料卡形态，Lv.20）", "朱然（二星材料卡形态，Lv.20）"),
]

# 受影响的 docx（相对 BASE）与其母本 frame_json 文件（相对 资料库）
DOCS = [
    ("报告库/开荒/逐帧1秒版/开荒专题（6 视频合并）_逐帧深度学习报告_1秒版.docx",
     ["资料库/frame_json_kaihuang/video_率土开荒焚诀，【开荒的基本原理】..._top_0_2.json",
      "资料库/frame_json_kaihuang/video_萌新第一课：哪些武将是核心，哪些..._top_0_2.json",
      "资料库/frame_json_kaihuang/史上最大开荒滑铁卢 这里是地狱吗？.json"]),
    ("报告库/旧56项目/逐帧1秒版/全率土最细最全攻略合集—战磐篇粉丝答疑 战磐篇粉丝答疑来了，看看有没有你的队伍？ 跟北冥多多互动，留言下期想看主五哪个体系？_逐帧深度学习报告_1秒版.docx",
     ["资料库/frame_json/全率土最细最全攻略合集—战磐篇粉丝答疑 战磐篇粉丝答疑来了，看看有没有你的队伍？ 跟北冥多多互动，留言下期想看主五哪个体系？.json"]),
    ("报告库/旧56项目/逐帧1秒版/太后大加强，平民也有光! 太后大加强，平民也有光!_逐帧深度学习报告_1秒版.docx",
     ["资料库/frame_json/太后大加强，平民也有光! 太后大加强，平民也有光!.json"]),
    ("报告库/旧56项目/逐帧1秒版/从零开始，宝物养成焚决，来了！ 刚进征服看见宝物系统，摸不着头脑？老是乱打一堆毫不适配的残品？别着急，北冥让你一篇看懂！_逐帧深度学习报告_1秒版.docx",
     ["资料库/frame_json/从零开始，宝物养成焚决，来了！ 刚进征服看见宝物系统，摸不着头脑？老是乱打一堆毫不适配的残品？别着急，北冥让你一篇看懂！.json"]),
    ("报告库/旧56项目/逐帧1秒版/张机如何显著降低败率？ 首先要理解张机这个武将最需要的是什么。_逐帧深度学习报告_1秒版.docx",
     ["资料库/frame_json/张机如何显著降低败率？ 首先要理解张机这个武将最需要的是什么。.json"]),
    ("报告库/旧56项目/逐帧1秒版/徐庶能玩吗？ 当然可以，平民极佳的战磐选择，来了！_逐帧深度学习报告_1秒版.docx",
     ["资料库/frame_json/徐庶能玩吗？ 当然可以，平民极佳的战磐选择，来了！.json"]),
    ("报告库/旧56项目/逐帧1秒版/率土最细最全攻略合集—垒实篇 评论抢点评! 把你们的垒实配队放在评论区哦!下期抽取点评别错过!_逐帧深度学习报告_1秒版.docx",
     ["资料库/frame_json/率土最细最全攻略合集—垒实篇 评论抢点评! 把你们的垒实配队放在评论区哦!下期抽取点评别错过!.json"]),
    ("报告库/旧56项目/逐帧1秒版/距离思路究极细节 ，普攻距离和战法距离，真的是越远越好吗？_逐帧深度学习报告_1秒版.docx",
     ["资料库/frame_json/距离思路究极细节 ，普攻距离和战法距离，真的是越远越好吗？.json"]),
    ("报告库/旧56项目/逐帧1秒版/这战法概率也太夸张了！ 也没人说甘宁带及锋概率能到80啊！_逐帧深度学习报告_1秒版.docx",
     ["资料库/frame_json/这战法概率也太夸张了！ 也没人说甘宁带及锋概率能到80啊！.json"]),
    ("报告库/旧56项目/逐帧1秒版/两小一大保底说法是否属实？ 咱们一起长期进行记录验证。_逐帧深度学习报告_1秒版.docx",
     ["资料库/frame_json/两小一大保底说法是否属实？ 咱们一起长期进行记录验证。.json"]),
]

def backup(p):
    d = os.path.join(BKUP, os.path.dirname(p).replace(BASE, "").lstrip("/\\").replace("/", "_").replace("\\", "_"))
    os.makedirs(d, exist_ok=True)
    dst = os.path.join(d, os.path.basename(p))
    if not os.path.exists(dst):
        shutil.copy2(p, dst)
    return dst

def replace_docx(path):
    doc = Document(path)
    def fix_runs(container):
        # container: paragraph or cell
        for p in (container.paragraphs if hasattr(container, "paragraphs") else [container]):
            for r in p.runs:
                t = r.text
                nt = t
                for o, n in SIMPLE.items():
                    if o in nt: nt = nt.replace(o, n)
                for o, n in CONTEXT:
                    if o in nt: nt = nt.replace(o, n)
                if nt != t:
                    r.text = nt
    for para in doc.paragraphs:
        fix_runs(para)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                fix_runs(cell)
    doc.save(path)

def replace_json(path):
    def walk(o):
        if isinstance(o, dict):
            return {k: walk(v) for k, v in o.items()}
        if isinstance(o, list):
            return [walk(v) for v in o]
        if isinstance(o, str):
            s = o
            for a, b in SIMPLE.items():
                if a in s: s = s.replace(a, b)
            for a, b in CONTEXT:
                if a in s: s = s.replace(a, b)
            return s
        return o
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    data = walk(data)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

log = []
for doc_rel, fj_rel_list in DOCS:
    doc_path = os.path.join(BASE, doc_rel)
    backup(doc_path)
    replace_docx(doc_path)
    for fj_rel in fj_rel_list:
        fj_path = os.path.join(BASE, fj_rel)
        if os.path.exists(fj_path):
            backup(fj_path)
            replace_json(fj_path)
    log.append("patched docx: " + os.path.basename(doc_path))

print("\n".join(log))
print("BACKUP ROOT:", BKUP)
print("DONE")
