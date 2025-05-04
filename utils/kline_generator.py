import os
import pandas as pd
from datetime import datetime, timedelta

class KLineGenerator:
    """
    此類別負責讀取逐筆交易檔，並依照需求輸出對應時間區間的 K 線圖。
    每次呼叫 get_k_line() 都會計算一根新的 K 棒。
    """
    def __init__(self, stock_id: str, timeframe: int, unit: str = "min"):
        """
        :param stock_id: str, 股票代碼 (e.g. "2330")
        :param timeframe: int, K線單位 (e.g. 5 表示 5 分鐘)
        """
        # 初始化分析股票及其資料路徑
        self.stock_id = stock_id
        self.tick_data_path = f"input/price_tick/{stock_id}"
        self.k_line_data_path = f"input/K_line/{stock_id}"
        
        # 初始化K線單位
        self.timeframe = timeframe
        self.unit = unit
        
        # 確保輸出目錄存在
        os.makedirs(self.k_line_data_path, exist_ok=True)

    def get_k_line(self):
        """
        計算所有 K 棒資料並存成 CSV 檔案
        """
        # 檢查是否已經存在 K 線檔案
        output_path = os.path.join(self.k_line_data_path, f"{self.timeframe}_{self.unit}.csv")
        if os.path.exists(output_path):
            # print(f"找到已存在的 K 線檔案: {output_path}")
            return output_path
            
        # print("未找到K線檔案，開始生成K線檔案...")

        # 取得資料夾下所有的 CSV 檔案
        csv_files = [f for f in os.listdir(self.tick_data_path) if f.endswith('.csv')]
        
        if not csv_files:
            raise FileNotFoundError(f"找不到逐筆交易資料檔案在: {self.tick_data_path}")
        
        # 讀取並合併所有 CSV 檔案
        dfs = []
        for csv_file in csv_files:
            csv_file_path = os.path.join(self.tick_data_path, csv_file)
            # print(f"\n讀取逐筆交易資料檔案: {csv_file_path}")
            df = pd.read_csv(csv_file_path)
            dfs.append(df)
        
        # 合併所有資料
        df = pd.concat(dfs, ignore_index=True)
        
        # 將日期和時間合併成 datetime
        df["datetime"] = pd.to_datetime(df["date"] + " " + df["Time"], format='mixed')
        
        # 設定 datetime 為索引
        df.set_index("datetime", inplace=True)
        
        # 篩選交易時間
        df = df.between_time("09:00", "13:30")
        
        # 將所有 13:30:00 的時間改為 13:29:59（使用向量化操作）
        mask = df.index.time == pd.Timestamp('13:30:00').time()
        df.index = df.index.where(~mask, df.index - pd.Timedelta(seconds=1))
        
        # 依照 timeframe 分組計算 K 棒
        ohlc_dict = {
            "deal_price": ["first", "max", "min", "last"],
            "volume": "sum"
        }
        df_resampled = df.resample(f"{self.timeframe}{self.unit}", closed='left', label='left').agg(ohlc_dict)
        
        # 重新命名欄位
        df_resampled.columns = ["open", "high", "low", "close", "volume"]
        
        # 移除沒有交易的時間區間
        df_resampled.dropna(subset=["open"], inplace=True)
        
        # 重置索引，讓 datetime 變成一般欄位
        df_resampled.reset_index(inplace=True)
        
        # 處理最後一根 K 棒的時間
        if not df_resampled.empty:
            last_time = df_resampled.iloc[-1]["datetime"]
            if last_time.hour == 13 and last_time.minute == 35:
                # 將最後一根 K 棒的時間改為 13:30
                df_resampled.iloc[-1, df_resampled.columns.get_loc("datetime")] = last_time.replace(minute=30)
        
        # 儲存 K 線資料
        df_resampled.to_csv(output_path, index=False, encoding="utf-8-sig")
        
        return output_path