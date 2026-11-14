# -*- coding: utf-8 -*-
"""v3：校准结构(1秒版7段) + 区分「纠错语境引用」vs「正文误用」的变体扫描。"""
import os, re, glob, json
from docx import Document

REPORT_DIR = r"D:/Desktop/shandou/学习汇报"
PATTERN = "*逐帧深度学习报告_1秒版.docx"

VARIANTS = ["重谋","全军","薄浪","鼎足","避其锐气","巨黍","三部上线","魂水","战盘",
            "同素","当洋桥","油飘","极锋而适","衡热","巨熟","远宫密策","星汉继世"]

# 1秒版 7 段结构关键词
STRUCT_KW = ["逐帧学习的核心结论","逐帧分析方法","逐帧时间轴","对照","新增价值",
             "局限与查不到","术语与证据索引"]

# 纠错语境标记（变体出现在其附近说明是被引用为「旧错词」）
CORR_MARKERS = ["既有报告","音频转写","转写","误写","误听","存疑","无法确认","逐帧确认",
                "逐帧核对","校正","修正","画面确认","画面显示为","确认为","实为",
                "系语音","音近","读音","记作","写作","称为","称","查不到","猜测",
                "而非","纠正","改写作","标注"]

def get_text(doc):
    parts=[]
    for p in doc.paragraphs:
        if p.text.strip(): parts.append(p.text)
    for t in doc.tables:
        for row in t.rows:
            for c in row.cells:
                if c.text.strip(): parts.append(c.text)
    return "\n".join(parts)

def main():
    files=sorted(glob.glob(os.path.join(REPORT_DIR, PATTERN)))
    struct_bad=[]; real_residuals=[]
    per_var_correction=0; per_var_other={}
    for f in files:
        name=os.path.basename(f); doc=Document(f); text=get_text(doc)
        # 结构
        miss=[k for k in STRUCT_KW if k not in text]
        if miss: struct_bad.append((name, miss))
        # 变体：逐处分类
        for v in VARIANTS:
            for m in re.finditer(re.escape(v), text):
                s=max(0,m.start()-45); e=min(len(text),m.end()+45)
                ctx=text[s:e]
                near_corr=any(mk in ctx for mk in CORR_MARKERS)
                if near_corr:
                    per_var_correction+=1
                else:
                    per_var_other.setdefault(v,0); per_var_other[v]+=1
                    real_residuals.append((name, v, ctx.replace("\n"," ")))
    print(f"报告总数: {len(files)}")
    print(f"\n=== 结构(1秒版7段)缺失报告数: {len(struct_bad)} ===")
    for n,ms in struct_bad[:10]:
        print(f"  {n[:30]}: 缺 {ms}")
    print(f"\n=== 变体总出现中属「纠错语境引用」: {per_var_correction} 处 ===")
    print(f"=== 变体出现在「非纠错语境」(疑似正文误用) 共 {sum(per_var_other.values())} 处 ===")
    if per_var_other:
        for v,c in sorted(per_var_other.items(), key=lambda x:-x[1]):
            print(f"  {v}: {c} 处")
    print("\n--- 疑似正文误用明细 ---")
    for n,v,ctx in real_residuals:
        print(f"[{n[:20]}] {v} :: …{ctx}…")
    out={"total":len(files),"struct_bad":struct_bad,
         "correction_ctx":per_var_correction,"other":per_var_other,
         "residuals":real_residuals}
    with open(os.path.join(REPORT_DIR,"..","资料库","audit_reports_v3.json"),"w",encoding="utf-8") as fp:
        json.dump(out,fp,ensure_ascii=False,indent=2)
    print("\n已写 资料库/audit_reports_v3.json")

if __name__=="__main__":
    main()
