import sys, os, json, glob, traceback
sys.path.insert(0, os.path.dirname(__file__))
import gen_report

REPORTS = "D:/Desktop/shandou/资料库/reports_json"
OUT = "D:/Desktop/shandou/学习汇报"
os.makedirs(OUT, exist_ok=True)

def main():
    paths = sorted(glob.glob(os.path.join(REPORTS, "*.json")))
    print("FOUND_JSON", len(paths))
    ok = 0; fail = 0; fails = []
    for jp in paths:
        try:
            with open(jp, encoding='utf-8') as f:
                data = json.load(f)
            title = data.get('video_title') or os.path.splitext(os.path.basename(jp))[0]
            out = os.path.join(OUT, title + "_完整学习报告.docx")
            gen_report.build(out, data)
            ok += 1
        except Exception as e:
            fail += 1
            fails.append((jp, repr(e)))
            traceback.print_exc()
    print(f"DONE ok={ok} fail={fail}")
    for jp, e in fails:
        print("FAIL", os.path.basename(jp), e)

if __name__ == '__main__':
    main()
