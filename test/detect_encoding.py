#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
detect_encoding.py
------------------
判斷指定檔案的文字編碼。

用法：
    python detect_encoding.py <檔案路徑> [--sample 200000]

參數說明：
    <檔案路徑>   必填，要檢測的檔案。
    --sample     選填，讀取檔案前多少位元組來判斷（預設 100000 = 100 KB）。
"""

import argparse
import importlib
import sys
from pathlib import Path

# －－－嘗試載入偵測函式（優先 chardet，次選 charset_normalizer）－－－
_detector = None
for lib, func in (
    ("chardet", lambda b: importlib.import_module("chardet").detect(b)),
    ("charset_normalizer", lambda b: importlib.import_module("charset_normalizer").from_bytes(b).best()),
):
    try:
        _detector = func
        importlib.import_module(lib)          # 成功載入即跳出迴圈
        break
    except ModuleNotFoundError:
        continue

if _detector is None:
    sys.exit("✖ 無法匯入 chardet 或 charset_normalizer，請先安裝其中一個：\n   pip install chardet   # 或 pip install charset_normalizer")

# －－－命令列參數－－－
parser = argparse.ArgumentParser(description="偵測檔案編碼")
parser.add_argument("file", type=Path, help="要檢測的檔案")
parser.add_argument("--sample", type=int, default=100_000, help="取樣大小（位元組），預設 100 KB")
args = parser.parse_args()

file_path: Path = args.file
if not file_path.is_file():
    sys.exit("✖ 找不到檔案：" + str(file_path.resolve()))

# －－－讀取檔案並判斷－－－
with file_path.open("rb") as f:
    raw = f.read(args.sample)

result = _detector(raw)

# chardet 回傳 dict；charset_normalizer 回傳 CharsetMatch 物件
if isinstance(result, dict):
    encoding = result.get("encoding")
    confidence = result.get("confidence", 0.0)
else:
    encoding = result.encoding
    confidence = result.chaos  # charset_normalizer 的 chaos 越低越好
    confidence = 1.0 - confidence   # 轉成「越高越好」的信心度

# －－－輸出結果－－－
if encoding:
    print(f"✔ 推測編碼：{encoding}   (信心度 {confidence:.2%})")
else:
    print("⚠ 無法確定檔案編碼，請手動檢查。")
