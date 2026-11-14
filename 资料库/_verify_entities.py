import os, glob, json, re
base = r"D:\Desktop\shandou"
zb = os.path.join(base,"资料库")
def lj(p): return json.load(open(os.path.join(zb,p),encoding="utf-8"))

# ---- correct whitelist parsing ----
hero_set = set(lj("official_hero_names.json")["names"]) | set(h["name"] for h in lj("hero.json"))
ext = lj("official_jineng_names_ext.json")
skill_set = set(ext["names"]) | set(lj("official_jineng_names.json")["names"]) | set(s.get("name","") for s in lj("jineng_list.json"))
gear_d = lj("gear_id.json")
gear_set = set(g["name"] for g in gear_d if isinstance(g,dict) and "name" in g) | set(lj("official_gear_names.json")["names"])
affix_set = set(g.get("skillName","") for g in gear_d if isinstance(g,dict) and g.get("skillName"))

print("白名单规模: 武将 %d | 战法 %d | 宝物 %d" % (len(hero_set), len(skill_set), len(gear_set)))
for s in ["击势","先驱突击","始计","反计之策","神兵天降","桃园结义","母仪浮梦","温酒斩将","轻侠妄为","单骑救主"]:
    print("  skill ok?", s, s in skill_set)

CN = r"[\u4e00-\u9fff＆&]"
pos_pat = re.compile(r"(?:大营|中军|前锋|主将|副将)\s*("+CN+"{2,5})")
team_pat = re.compile(r"("+CN+"{2,5})[＋+]\s*("+CN+"{2,5})(?:[＋+]\s*("+CN+"{2,5}))?")
hero_paren = re.compile(r"(?<![\u4e00-\u9fff])("+CN+"{2,5})[（(]")
gear_pat = re.compile(r"宝物[：:\s]*("+CN+"{2,4})")
POSP = {"大营","中军","前锋","主将","副将"}
TEAM_NICK = {"宁元刀","螃蟹队","网红队","钢板队","核弹弓","马妹连","神赏法刀","盖刀",
 "斩龙队","菜刀队","肉队","肉步","螃蟹变种","法刀","法刀变体","重步队","盾刀","流氓队",
 "网红","钢板","核弹","螃蟹","菜刀","马妹","张辽队","甘宁队","曹操队","灵帝队","庞统队",
 "张绣队","曹纯队","文鸯队","赵云队","王异刀","木鹿队","斯巴达","送死流","碰瓷","铺路",
 "拆迁","混拆迁","白板","满红","高红","多穿","核心的螃蟹","马妹连起来","小晋弓","魏武白莱"}

NOISE_PREFIX = set(list("与和即仍主亦人队方全两三四一上下中大小胜败负将兵战攻守显读确经终及以从由对被敌我他其该此如若另同后前新旧原次首尾每各多单双群星"))
NOISE_PREFIX |= {"为信息","主题","伤害","位置","原因","风险","补充","石头","确认","数值","坚毅","关口","阵容","南阳","同盟","邪恶","皇家","盛气","荔枝","表情","过渡","空白","降临","迸发","明媚","辅助","输出"}
NOISE_SUFFIX = set(list("队中战为的等详出开胜败平系型变种特页帧录存误纠组成为替换调率图克制类兵营要塞城区榜盟团军官员玩选卡限置格标签态段接夫弓刀步骑墙"))

def norm(n): return n.replace("&","＆").strip("＆& ")
def strip_pos(n):
    while n[:2] in POSP and len(n)>2: n=n[2:]
    return n
def hero_clean(n):
    n=norm(strip_pos(n))
    if len(n)<2 or len(n)>4: return None
    if n[0] in NOISE_PREFIX: return None
    if n[-1] in NOISE_SUFFIX: return None
    return n

hero_unknown=set(); skill_unknown=set(); gear_unknown=set()
ctx={}
def flag(store,key,where):
    key=norm(key)
    if not key or len(key)<2: return
    if key in store:
        if where not in ctx.get(key,""): ctx[key]=ctx.get(key,"")+"; "+where
        return
    store.add(key); ctx[key]=where

jsons = sorted(glob.glob(os.path.join(zb,"hzh_frame_json","*.json"))) + \
        sorted(glob.glob(os.path.join(zb,"saiji_frame_json","*.json")))

for j in jsons:
    fn=os.path.basename(j)
    d=json.load(open(j,encoding="utf-8"))
    texts=[json.dumps(d.get("summary",{}),ensure_ascii=False)]
    for s in d.get("timeline",[]):
        texts.append(s.get("title",""))
        for f in s.get("frames",[]): texts.append(f.get("desc",""))
    texts.append(json.dumps(d.get("comparison",{}),ensure_ascii=False))
    texts.append(json.dumps(d.get("limitations",[]),ensure_ascii=False))
    texts.append(json.dumps(d.get("glossary",[]),ensure_ascii=False))
    full="\n".join(texts)
    for m in pos_pat.findall(full):
        nm=hero_clean(m)
        if nm and nm not in hero_set and nm not in TEAM_NICK: flag(hero_unknown,nm,"%s:位置[%s]"%(fn,m))
    for t in team_pat.findall(full):
        mems=[norm(x) for x in t if x]
        if not any(x in hero_set for x in mems): continue
        for nm in mems:
            c=hero_clean(nm)
            if c and c not in hero_set and c not in TEAM_NICK: flag(hero_unknown,c,"%s:队伍[%s]"%(fn,"+".join(mems)))
    for m in hero_paren.findall(full):
        nm=hero_clean(m)
        if nm and nm not in hero_set and nm not in TEAM_NICK and nm not in skill_set: flag(hero_unknown,nm,"%s:name(%s]"%(fn,m))
    for hp in re.finditer(r"("+CN+"{2,5})[（(]([^（）]*)[）)]", full):
        content=hp.group(2)
        for tk in re.split(r"[/、,，]", content):
            tk=tk.strip()
            if not tk or re.search(r"[A-Za-z0-9]", tk): continue
            if len(tk)<2 or len(tk)>7: continue
            if tk in skill_set or tk in gear_set or tk in affix_set: continue
            if tk in ("宝物","战法","自带"): continue
            flag(skill_unknown,tk,"%s:skillslot[%s]"%(fn,tk))
    for m in gear_pat.findall(full):
        nm=norm(m)
        if nm in gear_set: continue
        flag(gear_unknown,nm,"%s:宝物[%s]"%(fn,m))

out=[]
out.append("=== 武将 不在白名单 (需核查) ===")
for x in sorted(hero_unknown): out.append("  %s   <- %s"%(x,ctx[x][:100]))
out.append("\n[共 %d 个]\n"%len(hero_unknown))
out.append("=== 战法/宝物槽 不在白名单 (需核查) ===")
for x in sorted(skill_unknown): out.append("  %s   <- %s"%(x,ctx[x][:100]))
out.append("\n[共 %d 个]\n"%len(skill_unknown))
out.append("=== 宝物 不在白名单 (需核查) ===")
for x in sorted(gear_unknown): out.append("  %s   <- %s"%(x,ctx[x][:100]))
out.append("\n[共 %d 个]"%len(gear_unknown))
open(os.path.join(zb,"_verify_entities_out.txt"),"w",encoding="utf-8").write("\n".join(out))
print("\n".join(out))
