import json
r=json.load(open("check_numeric_report.json",encoding="utf-8"))
for label in ("完整版","一秒版"):
    for key,cn in (("qual","品质"),("type","类型"),("dist","距离")):
        items=[x for x in r[label][key] if not x["cited"] and not x["buff"]]
        if not items: continue
        print("\n########## %s / %s  %d 条 ##########"%(label,cn,len(items)))
        for i,x in enumerate(items,1):
            print("%2d. [%s] 「%s」 报告=%s 官方=%s"%(i,x["file"][:16],x["skill"],x["claim"],x["official"]))
            print("    …%s…"%x["ctx"])
