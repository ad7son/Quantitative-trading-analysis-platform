import re
import pandas as pd

# 先以字串形式組合，保留原始值
combined = df["date"].astype(str) + " " + df["Time"].astype(str)

# 使用正則式：yyyy-mm-dd hh:mm:ss.毫秒
good_pattern = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+$")

bad_mask = ~combined.str.match(good_pattern)
bad_rows = df.loc[bad_mask]

print(f"偵測到 {bad_rows.shape[0]} 列格式異常")
print(bad_rows.head())
