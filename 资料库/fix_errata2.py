# -*- coding: utf-8 -*-
"""勘误第 2 批：区分「宝物词条」与「兵种特性」"""
import os, shutil, sys
from docx import Document

REP = r"D:\Desktop\shandou\学习汇报"
BAK = os.path.join(REP, "_backup_before_errata")

RULES = [
    ("宝物词条体系首次在本视频暴露：〔词条OCR存疑〕(出现于甘宁/司马炎宝物)、列阵、守备、迂回、地利——这些词条的具体加成数值需结合游戏内系统进一步确认。",
     "宝物与兵种信息首次在本视频暴露：〔宝物词条OCR存疑〕(出现于甘宁/司马炎宝物)；而「列阵/守备/迂回/地利」经核实为**兵种特性**而非宝物词条（列阵=长枪兵两目标以上增伤；迂回/地利=弓兵系特性），原表述有误，具体数值以游戏内为准。"),
    ("宝物词条（〔词条OCR存疑〕/列阵/守备/迂回/地利）各自对发动率的具体加成百分比未在画面中标出，仅知「无机敏宝物」条件下九锡黄龙达49%。",
     "画面同屏显示的「〔宝物词条OCR存疑〕/列阵/守备/迂回/地利」中，后四项经核实为**兵种特性**而非宝物词条，对发动率无直接加成；宝物词条本身的加成百分比未在画面标出，仅知「无机敏宝物」条件下九锡黄龙达49%。"),
    ("甘宁-大桐琴〔OCR存疑〕(〔词条OCR存疑〕/列阵)、司马炎-两仪刀(〔词条OCR存疑〕/守备)、孙权-游飘(迂回/地利)",
     "甘宁-大桐琴〔宝物名OCR存疑〕(宝物词条〔OCR存疑〕；列阵为兵种特性)、司马炎-两仪刀(宝物词条〔OCR存疑〕；守备为兵种特性)、孙权-游飘(迂回/地利均为弓兵兵种特性)"),
    ("宝物大桐琴〔OCR存疑〕(词条：〔词条OCR存疑〕、列阵)",
     "宝物大桐琴〔名称OCR存疑〕(宝物词条〔OCR存疑〕；「列阵」为兵种特性非词条)"),
    ("宝物两仪刀(词条：〔词条OCR存疑〕、守备)",
     "宝物两仪刀(宝物词条〔OCR存疑〕；「守备」为兵种特性非词条)"),
    ("宝物游飘(词条：迂回、地利)", "宝物游飘(「迂回」「地利」为弓兵兵种特性，非宝物词条)"),
    ("汜水关(A) / 及锋而试(S)", "汜水关(典藏) / 及锋而试(S)"),
    ("宝物词条、〔词条OCR存疑〕", "宝物词条、兵种特性（列阵/迂回/地利）"),
]


def rep(par, old, new):
    if old not in par.text:
        return 0
    n = par.text.count(old)
    done = 0
    for r in par.runs:
        if old in r.text:
            done += r.text.count(old)
            r.text = r.text.replace(old, new)
    if done == n:
        return done
    full = par.text.replace(old, new)
    if par.runs:
        par.runs[0].text = full
        for r in par.runs[1:]:
            r.text = ""
    return n


apply = "--apply" in sys.argv
tgt = [f for f in os.listdir(REP) if "这战法概率" in f and "1秒版" in f and f.endswith(".docx")]
for f in tgt:
    p = os.path.join(REP, f)
    d = Document(p)
    tot = 0
    for old, new in RULES:
        c = 0
        for par in d.paragraphs:
            c += rep(par, old, new)
        if c:
            print(f"  {c} x  {old[:50]}")
            tot += c
    print(f"{f[:40]} 合计 {tot} 处")
    if apply and tot:
        if not os.path.exists(os.path.join(BAK, "p2_" + f)):
            shutil.copy2(p, os.path.join(BAK, "p2_" + f))
        d.save(p)
        print("  已保存")
if not apply:
    print("[DRY-RUN]")
