import codecs
from pathlib import Path

csv_file_path = Path(r"input/price_tick/2882/2020.csv")  # 換成你的檔案

def locate_broken_byte(path, encoding="utf-8", chunk_size=4096):
    """
    逐塊嘗試用指定 encoding 解碼，抓到第一個解碼失敗的位元組。
    回傳 (錯誤絕對位址, 壞位元組 bytes, 錯誤物件)
    """
    decoder = codecs.getincrementaldecoder(encoding)("strict")
    pos = 0
    with path.open("rb") as f:
        for raw in iter(lambda: f.read(chunk_size), b""):
            try:
                decoder.decode(raw)
                pos += len(raw)
            except UnicodeDecodeError as e:
                absolute = pos + e.start        # 檔案中的實際位址
                bad_byte = raw[e.start:e.start+1]
                return absolute, bad_byte, e
    return None, None, None  # 完全沒問題

idx, bad, err = locate_broken_byte(csv_file_path)

if idx is not None:
    # 把周圍幾個位元組列印出來方便觀察
    context = 10
    with csv_file_path.open("rb") as f:
        f.seek(max(idx - context, 0))
        snippet = f.read(context + 1 + context)
    print(f"🚨 壞字位址：{idx}")
    print(f"🚨 壞位元組：0x{bad.hex()}")
    print("周邊 20 bytes：", snippet.hex(" "))
else:
    print("檔案用 UTF-8 讀取完全正常！")
