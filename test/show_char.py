from pathlib import Path

file_path = Path(r"input/price_tick/2882/2020.csv")
bad_pos   = 10409988          # 剛剛抓到的 offset

def locate_row_col(path, offset, encoding_for_preview="cp1252"):
    with path.open("rb") as f:
        cumulative = 0
        for row_no, raw_line in enumerate(f, start=1):
            next_cumulative = cumulative + len(raw_line)
            if offset < next_cumulative:
                # 壞位元組就在這一行
                col_byte_index = offset - cumulative               # 0-based byte 位置
                # 若想看「字元」位置，可先用適當編碼解
                preview = raw_line.decode(encoding_for_preview, errors="replace")
                return row_no, col_byte_index, preview
            cumulative = next_cumulative
    return None, None, None   # 如果 offset 超出檔案

row, col_byte, preview = locate_row_col(file_path, bad_pos)
print(f"壞字元所在：第 {row} 行，第 {col_byte} 個『位元組』")
print("該行 (cp1252 解碼預覽)：", preview[:120] + " ...")
