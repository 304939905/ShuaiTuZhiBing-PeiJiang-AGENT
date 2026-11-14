#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""为每个 1秒/帧 视频目录生成 contact sheets（缩略图拼图）。"""
import os
import re
import math
import argparse
from PIL import Image, ImageDraw, ImageFont


THUMB_W, THUMB_H = 240, 135
COLS, ROWS = 5, 8
FRAMES_PER_SHEET = COLS * ROWS
LABEL_H = 20
SHEET_W = COLS * THUMB_W
SHEET_H = ROWS * (THUMB_H + LABEL_H)


def natural_sort_key(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]


def find_video_dirs(base):
    """返回所有含 .jpg 的视频目录（含开荒子目录）。"""
    dirs = []
    for root, _, files in os.walk(base):
        if any(f.endswith('.jpg') for f in files):
            # skip contact_sheets dirs themselves
            if os.path.basename(root) == 'contact_sheets':
                continue
            dirs.append(root)
    return sorted(dirs, key=lambda x: natural_sort_key(os.path.basename(x)))


def make_sheet_for_dir(video_dir, font=None, force=False):
    out_dir = os.path.join(video_dir, 'contact_sheets')
    os.makedirs(out_dir, exist_ok=True)
    existing = sorted(glob_like(out_dir, 'sheet_*.jpg'))
    if existing and not force:
        print(f"SKIP {os.path.basename(video_dir)}")
        return out_dir, len(existing)

    frames = sorted(
        [os.path.join(video_dir, f) for f in os.listdir(video_dir) if f.endswith('.jpg')],
        key=lambda x: natural_sort_key(os.path.basename(x))
    )
    if not frames:
        return out_dir, 0

    # clear old sheets
    for f in existing:
        os.remove(f)

    total_sheets = math.ceil(len(frames) / FRAMES_PER_SHEET)
    for sidx in range(total_sheets):
        sheet = Image.new('RGB', (SHEET_W, SHEET_H), (32, 32, 32))
        draw = ImageDraw.Draw(sheet)
        for i in range(FRAMES_PER_SHEET):
            fidx = sidx * FRAMES_PER_SHEET + i
            if fidx >= len(frames):
                break
            col = i % COLS
            row = i // COLS
            x = col * THUMB_W
            y = row * (THUMB_H + LABEL_H)
            img = Image.open(frames[fidx])
            img = img.resize((THUMB_W, THUMB_H), Image.Resampling.LANCZOS)
            sheet.paste(img, (x, y))
            label = f"F{fidx:04d}"
            m = re.search(r'frame_(\d+)_(\d{2})-(\d{2})', os.path.basename(frames[fidx]))
            if m:
                label = f"{int(m.group(1)):04d} @{m.group(2)}:{m.group(3)}"
            draw.rectangle([x, y + THUMB_H, x + THUMB_W, y + THUMB_H + LABEL_H], fill=(0, 0, 0))
            draw.text((x + 4, y + THUMB_H + 2), label, fill=(255, 255, 255), font=font)
        out_path = os.path.join(out_dir, f"sheet_{sidx+1:02d}.jpg")
        sheet.save(out_path, quality=88)
    print(f"DONE {os.path.basename(video_dir)} -> {total_sheets} sheets")
    return out_dir, total_sheets


def glob_like(d, pat):
    import fnmatch
    return [os.path.join(d, f) for f in os.listdir(d) if fnmatch.fnmatch(f, pat)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', default=r'D:\Desktop\shandou\抖音_frames_dense_1s')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()

    font = None
    try:
        font = ImageFont.truetype(r'C:\Windows\Fonts\msyh.ttc', 12)
    except Exception:
        pass

    dirs = find_video_dirs(args.base)
    print(f"found {len(dirs)} video dirs")
    total = 0
    for d in dirs:
        _, n = make_sheet_for_dir(d, font=font, force=args.force)
        total += n
    print(f"TOTAL SHEETS: {total}")


if __name__ == '__main__':
    main()
