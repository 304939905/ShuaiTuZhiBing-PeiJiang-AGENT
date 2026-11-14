#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""赛季专属：把每视频 1秒/帧抽帧拼成 contact sheet（5x8=40帧/张，带序号@MM:SS 标签）。"""
import os, glob, re
from PIL import Image, ImageDraw, ImageFont

FRAMES = r"D:/Desktop/shandou/赛季_frames_dense_1s"
COLS, ROWS = 5, 8
PER = COLS * ROWS
THUMB = 320
GAP = 6
LABEL_H = 20


def try_font(size):
    for p in [
        r"C:/Windows/Fonts/msyh.ttc",
        r"C:/Windows/Fonts/simhei.ttf",
        r"C:/Windows/Fonts/arial.ttf",
    ]:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def main():
    font = try_font(15)
    total_sheets = 0
    for d in sorted(os.listdir(FRAMES)):
        dd = os.path.join(FRAMES, d)
        if not os.path.isdir(dd):
            continue
        frames = sorted(glob.glob(os.path.join(dd, "frame_*.jpg")))
        if not frames:
            continue
        cs_dir = os.path.join(dd, "contact_sheets")
        os.makedirs(cs_dir, exist_ok=True)
        for old in glob.glob(os.path.join(cs_dir, "sheet_*.jpg")):
            os.remove(old)
        n_sheets = (len(frames) + PER - 1) // PER
        for s in range(n_sheets):
            chunk = frames[s * PER:(s + 1) * PER]
            sheet = Image.new("RGB", (COLS * (THUMB + GAP) + GAP,
                                       ROWS * (THUMB + LABEL_H + GAP) + GAP), (255, 255, 255))
            for k, fp in enumerate(chunk):
                r, c = divmod(k, COLS)
                x = GAP + c * (THUMB + GAP)
                y = GAP + r * (THUMB + LABEL_H + GAP)
                im = Image.open(fp).convert("RGB")
                im = im.resize((THUMB, THUMB))
                sheet.paste(im, (x, y))
                m = re.search(r"frame_(\d+)_(\d+)-(\d+)\.jpg", os.path.basename(fp))
                if m:
                    seq = int(m.group(1))
                    mm, ss = int(m.group(2)), int(m.group(3))
                    label = f"{seq:04d} @{mm:02d}:{ss:02d}"
                else:
                    label = os.path.basename(fp)
                dr = ImageDraw.Draw(sheet)
                dr.text((x + 2, y + THUMB + 2), label, fill=(200, 0, 0), font=font)
            out = os.path.join(cs_dir, f"sheet_{s+1:02d}.jpg")
            sheet.save(out, quality=82)
            total_sheets += 1
        print(f"{d}: {len(frames)} 帧 -> {n_sheets} 张 sheet", flush=True)
    print(f"TOTAL_SHEETS={total_sheets}")


if __name__ == "__main__":
    main()
