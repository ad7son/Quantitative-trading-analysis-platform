import os
from tqdm import tqdm
from utils.data_loader import DataLoader
from backtest import BacktestEngine, BacktestParams
from utils.result_exporter import ResultExporter
from utils.kline_generator import KLineGenerator
from utils.excel_processor import process_excel_file
# 引入策略類別
from strategies.SMAS import SMASStrategy, SMASParams  

STOCK = ["1101", "1216", "1301", "1303", "2002", "2207", "2301", "2303", "2308", "2317", 
         "2327", "2330", "2345", "2357", "2379", "2382", "2395", "2412", "2454", "2603", 
         "2609", "2615", "2880", "2881", "2882", "2883", "2884", "2885", "2886", "2887",
         "2890", "2891", "2892", "2912", "3008", "3017", "3034", "3037", "3045", "3231",
         "3661", "3711", "4904", "4938", "5871", "5876", "5880", "6446", "6505", "6669"
]

MA_TYPE = ["EMA"]
STRATEGY = "SMAS"
SETTING = ["EMA_01"]
MA_PERIOD = {
    "EMA_01": [150, 200],
    "EMA_02": [50, 100],
    "EMA_03": [20, 34, 50],
    "EMA_04": [10, 20, 30],
    "EMA_05": [5, 8, 13]
}
SLOPE_PERIOD = {
    "EMA_01": [20, 26],
    "EMA_02": [10, 20],
    "EMA_03": [5, 10, 14],
    "EMA_04": [5, 7, 10],
    "EMA_05": [3, 5]
}
METHOD = {
    "EMA_01": ["M1", "M2"],
    "EMA_02": ["M2"],
    "EMA_03": ["M2"],
    "EMA_04": ["M2", "M3"],
    "EMA_05": ["M1", "M2", "M4"]
}
THRESHOLD = {
    "EMA_01": {
        "M1": [0.0], 
        "M2": [0.0, 0.1, 0.25]
    },
    "EMA_02": {
        "M2": [0.0, 0.1, 0.2]
    },
    "EMA_03": {
        "M2": [0.0, 0.07, 0.15]
    },
    "EMA_04": {
        "M2": [0.0, 0.05, 0.1], 
        "M3": [0.3, 0.4, 0.5]
    },
    "EMA_05": {
        "M1": [0.0], 
        "M2": [0.001, 0.003, 0.005], 
        "M4": [0.0]
    }
}

def main():
    # MA 類型進度
    for ma_type in tqdm(MA_TYPE, desc="MA 類型進度", ncols=100):
        # 設定進度
        for setting in tqdm(SETTING, desc="策略設定進度", ncols=100):
            # 股票進度
            for stock in tqdm(STOCK, desc="股票進度", ncols=100):
                # MA 週期進度
                for ma_period in MA_PERIOD[setting]:
                    # 斜率區間進度
                    for slope_period in SLOPE_PERIOD[setting]:
                        # 方法進度
                        for method in METHOD[setting]:
                            # 門檻進度
                            for index, threshold in enumerate(THRESHOLD[setting][method]):
                                
                                tqdm.write(f"正在回測 {STRATEGY} 股票:{stock}, 週期:{ma_period} 斜率區間:{slope_period} 方法:{method} 門檻:{threshold}")

                                # 設定輸出路徑
                                mode = f"1M{str(ma_period)}M{str(slope_period)}M{str(method)}T{str(index)}"
                                single_output_path = f"output/{STRATEGY}/{setting}/{stock}/{mode}/"
                                all_output_path = f"output/{STRATEGY}/{setting}/ETF0050_{STRATEGY}_{setting}.xlsx"
                                
                                # 設定K 線參數
                                freq = "min"
                                kline = KLineGenerator(
                                    stock_id=stock, 
                                    timeframe=1,
                                    unit=freq
                                )
                                # 設定策略參數
                                strategy_params = SMASParams(
                                    method=method,
                                    ma_type=ma_type,
                                    ma_period=ma_period,
                                    slope_period=slope_period,
                                    threshold=threshold
                                )
                                strategy = SMASStrategy(strategy_params)

                                # 創建回測參數
                                backtest_params = BacktestParams(
                                    initial_capital=1000000.0,
                                    fees=0.001425,
                                    slippage=0.0001,
                                )
                                
                                # 創建、搜尋及加載K線檔案路徑
                                data_path = kline.get_k_line()
                                data_loader = DataLoader(data_path)
                                data = data_loader.load_data()
                                data = data_loader.preprocess_data(fill_method='ffill', add_returns=True)
                                
                                # 創建回測引擎、交易訊號
                                engine = BacktestEngine(backtest_params)
                                engine.set_data(data)
                                signals = strategy.calculate_signals(data)
                                
                                # 執行回測
                                results = engine.run(signals, freq)
                                        
                                # 獲取所有統計數據、創建結果匯出器並匯出所有結果
                                all_stats = engine.get_all_statistics()
                                exporter = ResultExporter(single_output_path)
                                result = exporter.export_all(data, results, all_stats, strategy_params)
                                
                                # 將結果匯出至總表
                                exporter.write_df_to_excel(all_output_path, mode, result)

            # 處理總表
            process_excel_file(all_output_path)


if __name__ == "__main__":
    main()
