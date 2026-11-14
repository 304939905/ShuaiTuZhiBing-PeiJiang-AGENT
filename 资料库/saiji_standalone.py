"""兼容入口：赛季独立学习报告母本已升级为当前标杆结构。"""
from saiji_standalone_v2 import *  # noqa: F401,F403


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 3 and sys.argv[1] == "--all":
        build_all(sys.argv[2])
    elif len(sys.argv) == 2:
        build_shuzhi(sys.argv[1])
    else:
        raise SystemExit("usage: saiji_standalone.py --all OUTPUT_DIR | OUTPUT_DOCX")
