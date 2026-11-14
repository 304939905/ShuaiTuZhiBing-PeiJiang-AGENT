import shutil, sys
from pathlib import Path
src = Path("D:/Desktop/shandou/报告库")
dst = Path("D:/WorkBuddyData/shandou_report_backup_20260820")
if dst.exists():
    print("ERR: dst exists, abort to avoid clobber")
    sys.exit(2)
shutil.copytree(src, dst)
print("BACKUP DONE ->", dst)
n = sum(1 for _ in dst.rglob("*") if _.is_file())
print("files copied:", n)
