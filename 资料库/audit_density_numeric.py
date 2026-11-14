import sys,os,glob,re,json
sys.path.insert(0,"D:/WorkBuddyData/python-env/shandou/Lib/site-packages")
from docx import Document
REP="D:/Desktop/shandou/学习汇报"
meta=json.load(open("video_meta.json",encoding="utf-8"))
vids=meta.get("videos") or meta.get("items") or []
print("videos key:", [k for k in meta], "n=",len(vids))
dur={}
for v in (vids if isinstance(vids,list) else []):
    n=os.path.splitext(os.path.basename(v.get("path") or v.get("file") or v.get("name","")))[0]
    d=v.get("duration_s") or v.get("duration") or 0
    dur[n]=d
print("dur entries:",len(dur))

NUM=re.compile(r"\d+(?:\.\d+)?\s*(?:%|％|回合|点|万|兵|级|次|倍|秒)")
files=sorted(glob.glob(REP+"/*_逐帧深度学习报告_1秒版.docx"))
rows=[];tot_num=0
for f in files:
    doc=Document(f)
    t="\n".join(p.text for p in doc.paragraphs)
    for tb in doc.tables:
        for r in tb.rows:
            for c in r.cells: t+="\n"+c.text
    w=len(re.sub(r"\s","",t))
    nums=NUM.findall(t); tot_num+=len(nums)
    base=os.path.basename(f).replace("_逐帧深度学习报告_1秒版.docx","")
    rows.append((base,w,len(nums),dur.get(base,0)))
print("\n1秒版份数:",len(rows),"总字(去空白):",sum(r[1] for r in rows),"数值断言总数:",tot_num)
have=[r for r in rows if r[3]>0]
print("能匹配时长的:",len(have))
if have:
    dens=sorted(((r[1]/r[3],)+r for r in have))
    print("\n--- 字/秒 最低 8 份（遗漏风险最高）---")
    for d,b,w,n,s in dens[:8]: print(f"  {d:6.1f} 字/秒 | {w:6d}字 | {int(s):4d}s | {b[:34]}")
    print("\n--- 字/秒 最高 3 份 ---")
    for d,b,w,n,s in dens[-3:]: print(f"  {d:6.1f} 字/秒 | {w:6d}字 | {int(s):4d}s | {b[:34]}")
    import statistics as st
    print("\n中位密度 %.1f 字/秒"%st.median([d for d,*_ in dens]))
print("\n--- 数值断言最多 6 份 ---")
for b,w,n,s in sorted(rows,key=lambda r:-r[2])[:6]: print(f"  {n:4d} 处 | {b[:40]}")
