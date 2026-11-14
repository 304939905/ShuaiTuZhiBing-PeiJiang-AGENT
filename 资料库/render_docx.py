import sys, os, subprocess, shutil, glob, time, uuid

# 优先用新的 pymupdf 导入（pymupdf 10.x 后 fitz 接口仍兼容，但会告警）
try:
    import pymupdf as fitz
except Exception:
    import fitz

LIBREOFFICE_PROGRAM = os.environ.get(
    "LIBREOFFICE_PROGRAM", r"D:\LibreOffice\program"
)
# 用 soffice.exe（启动器）而非 soffice.bin；前者能正确初始化用户配置，避免 exit 81
SOFFICE_EXE = os.path.join(LIBREOFFICE_PROGRAM, "soffice.exe")


def _lo_url(path):
    """把 Windows 绝对路径转成 LibreOffice 可接受的 file:// URL。"""
    # 保留冒号即可（实测通过）；传统写法也可把冒号换竖线 |
    return "file:///" + os.path.abspath(path).replace(os.sep, "/")


def _kill_stale_soffice():
    """清理残留的 soffice 进程，避免 exit 81。"""
    for name in ("soffice.bin", "soffice.exe"):
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass


def convert_docx_to_pdf(docx_path, pdf_path, profile_dir=None, max_retry=2):
    """用 LibreOffice 无界面把 docx 转成 pdf，无 aspose 水印。"""
    if not os.path.exists(SOFFICE_EXE):
        raise FileNotFoundError(f"LibreOffice 未找到: {SOFFICE_EXE}")

    docx_path = os.path.abspath(docx_path)
    pdf_path = os.path.abspath(pdf_path)
    out_dir = os.path.dirname(pdf_path)
    os.makedirs(out_dir, exist_ok=True)

    base_profile = profile_dir or os.path.join(
        os.environ.get("TEMP") or r"D:\WorkBuddyData", "lo_profile"
    )

    env = os.environ.copy()
    # 避免调用者环境里的 Python/PATH 干扰 LibreOffice 自带运行时
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)

    last_error = ""
    for attempt in range(1, max_retry + 1):
        # 每次用独立 profile，避免锁冲突
        profile = os.path.join(base_profile, f"{uuid.uuid4().hex}")
        os.makedirs(profile, exist_ok=True)

        cmd = [
            SOFFICE_EXE,
            "--headless",
            "--norestore",
            "--nofirststartwizard",
            f"-env:UserInstallation={_lo_url(profile)}",
            "--convert-to", "pdf",
            "--outdir", out_dir,
            docx_path,
        ]

        proc = subprocess.run(
            cmd,
            env=env,
            cwd=LIBREOFFICE_PROGRAM,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if proc.returncode == 0:
            break

        last_error = f"attempt {attempt} exit={proc.returncode}\n{proc.stdout}"
        # 81 = 已有实例占用 profile；其它失败也可尝试清进程重跑
        _kill_stale_soffice()
        time.sleep(1)
    else:
        raise RuntimeError(f"LibreOffice 转换失败:\n{last_error}")

    # soffice 输出的 pdf 文件名与 docx 同名
    expected = os.path.join(
        out_dir, os.path.splitext(os.path.basename(docx_path))[0] + ".pdf"
    )
    if not os.path.exists(expected):
        # 兜底：按修改时间找刚生成的 pdf
        pdfs = glob.glob(os.path.join(out_dir, "*.pdf"))
        if not pdfs:
            raise FileNotFoundError(
                f"LibreOffice 未生成 PDF。输出:\n{proc.stdout}"
            )
        expected = max(pdfs, key=os.path.getmtime)

    if os.path.abspath(expected) != pdf_path:
        shutil.move(expected, pdf_path)
    return pdf_path


def render_pdf_to_png(pdf_path, out_dir, dpi=110):
    """pymupdf 把每页 pdf 渲染成 png。"""
    os.makedirs(out_dir, exist_ok=True)
    pdf = fitz.open(pdf_path)
    for i, page in enumerate(pdf):
        pix = page.get_pixmap(dpi=dpi)
        pix.save(os.path.join(out_dir, f"page_{i+1:02d}.png"))
    page_count = pdf.page_count
    pdf.close()
    return page_count


def main():
    docx_path = sys.argv[1]
    pdf_path = sys.argv[2]
    out_dir = sys.argv[3]

    convert_docx_to_pdf(docx_path, pdf_path)
    page_count = render_pdf_to_png(pdf_path, out_dir, dpi=110)
    print("RENDER_DONE pages=", page_count, "dir=", out_dir)


if __name__ == "__main__":
    main()
