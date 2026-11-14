import json
r=json.load(open("check_numeric_report.json",encoding="utf-8"))
def show(label,key,cap):
    items=[x for x in r[label][key] if not x["cited"]]
    print("\n########## %s / %s  非引用 %d 条 ##########"%(label,key,len(items)))
    for x in items[:cap]:
        c=x["ctx"]
        idx=c.find(x["skill"])
        seg=c[max(0,idx-30):idx+50]
        print("[%s] %s"%(x["file"][:14],x["skill"]))
        print("   claim=%s off=%s"%(x.get("claim"),x.get("official")))
        print("   …%s…"%seg)
show("一秒版","prob",34)
show("一秒版","qual",30)
