import os
from tqdm import tqdm
from utils.data_loader import DataLoader
from backtest import BacktestEngine, BacktestParams
from utils.result_exporter import ResultExporter
from utils.kline_generator import KLineGenerator
# 引入策略類別
from strategies.SMAS import SMASStrategy, SMASParams  


STRATEGY = "SMAS_SMA_DDD"
STOCK = ["1101", "1216", "1301", "1303", "2002", "2207", "2301", "2303", "2308", "2317", 
         "2327", "2330", "2345", "2357", "2379", "2382", "2395", "2412", "2454", "2603", 
         "2609", "2615", "2880", "2881", "2882", "2883", "2884", "2885", "2886", "2887",
         "2890", "2891", "2892", "2912", "3008", "3017", "3034", "3037", "3045", "3231",
         "3661", "3711", "4904", "4938", "5871", "5876", "5880", "6446", "6505", "6669"]
MA_PERIOD = [5, 10, 20, 30, 45, 60, 120, 160, 200]
SLOPE_PERIOD = [5, 10]
THRESH = 0.0


def main():
    for stock in tqdm(STOCK, desc="總股票進度", ncols=100):
        for ma_period in tqdm(MA_PERIOD, desc=" MA 週期進度", ncols=100):
            for slope_period in tqdm(SLOPE_PERIOD, desc=" 斜率區間進度", ncols=100):
                
                tqdm.write(f"回測 {STRATEGY} 股票:{stock}, 週期:{ma_period} ")

                # 設定輸出路徑
                mode = f"1D{str(ma_period)}D{str(slope_period)}D"
                single_output_path = f"output/{STRATEGY}/{stock}/{mode}/"
                all_output_path = f"output/{STRATEGY}/ETF0050_{STRATEGY}.xlsx"
                
                # 設定K 線參數
                freq = "D"
                kline = KLineGenerator(
                    stock_id=stock, 
                    timeframe=1,
                    unit=freq
                )
                # 設定策略參數
                strategy_params = SMASParams(
                    ma_type="SMA",
                    ma_period=ma_period,
                    slope_period=slope_period,
                    thresh=THRESH
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

                tqdm.write(f"已經完成")



if __name__ == "__main__":
    main()
