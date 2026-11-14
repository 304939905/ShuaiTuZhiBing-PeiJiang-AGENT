# -*- coding: utf-8 -*-
import json,io,sys,os,re
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
p='zhenrong_frame_json/video_对自己队伍不确定的，发评论区大家..._top_0_3.json'
d=json.load(open(p,encoding='utf-8'))
print('17键:',sorted(d.keys())==sorted(['video_title','video_id','frames_dir','duration_s','frame_count','sheet_count','resolution','report_date','summary','timeline','comparison','frame_only_value','limitations','glossary','sources','entities','ai_inference']))
print('timeline段数:',len(d['timeline']),'插图数:',sum(len(s.get('frames',[]))for s in d['timeline']))
print('corrections:',len(d['summary'].get('corrections',[])),'limitations:',len(d['limitations']))
wl=json.load(open('official_merged_whitelist.json',encoding='utf-8'))
hero_set=set(wl['heroes']); skill_set=set(wl['skills']); gear_set=set(wl['gears'])
gd=json.load(open('gear_id.json',encoding='utf-8'))
aff=set()
for g in gd:
    if isinstance(g,dict):
        for part in (g.get('skillName') or '').split('；'):
            aff.add(part.strip())
UT={'出奇','列阵','利刃','勇毅','地利','守备','扰后','挫锐','文韬','疾行','迂回','难测','齐射','散射','灵动','强击','坚守','协力'}
probs=[]
for t in d['entities']['teams']:
    for p in t['positions']:
        h=p['hero']
        if h not in hero_set:
            probs.append(('武将',h))
        for s in p['skills']:
            if s not in skill_set:
                probs.append(('战法',s,t['name'],h))
        g=p.get('gear')
        if g and g not in gear_set:
            probs.append(('宝物',g,t['name'],h))
        for tr in p.get('traits') or []:
            if tr not in aff:
                probs.append(('宝物词条',tr,t['name'],h))
        for ut in p.get('unit_traits') or []:
            if ut not in UT:
                probs.append(('兵种词条',ut,t['name'],h))
print('实体问题:',len(probs))
for x in probs[:8]:
    print('-',x)
fd=os.path.join(r'D:/Desktop/shandou/抖音_frames_dense_1s/阵容',d['frames_dir'])
files=set(os.listdir(fd)); miss=[]
for seg in d['timeline']:
    for f in seg.get('frames',[]):
        if f['file'] not in files:
            miss.append(f['file'])
print('缺帧:',len(miss))
txt=json.dumps(d,ensure_ascii=False)
for pat in ['UP主','UP 主','北冥','止戈丨青仙','长史','画面读作','转写误作','定向判读确认','早期帧读作']:
    c=txt.count(pat)
    if c:
        print('残留:',pat,c)
for h in d['entities']['heroes']:
    vl=h.get('version_label','')
    if '?' in vl or '极' in vl:
        print('标签问题:',h['name'],vl)
print('teams:',len(d['entities']['teams']))
for t in d['entities']['teams']:
    print(t['name'],'|','/'.join(p['hero'] for p in t['positions']))