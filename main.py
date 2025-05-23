import os
from tqdm import tqdm
from utils.data_loader import DataLoader
from backtest import BacktestEngine, BacktestParams
from utils.result_exporter import ResultExporter
from utils.kline_generator import KLineGenerator
# 引入 GMMA 策略類別
from strategies.GMMA import GMMAStrategy, GMMAParams

MA_TYPE = ["SMA", "EMA", "WMA"]

STOCK = ["1101", "1216", "1301", "1303", "2002", "2207", "2301", "2303", "2308", "2317", 
         "2327", "2330", "2345", "2357", "2379", "2382", "2395", "2412", "2454", "2603", 
         "2609", "2615", "2880", "2881", "2882", "2883", "2884", "2885", "2886", "2887",
         "2890", "2891", "2892", "2912", "3008", "3017", "3034", "3037", "3045", "3231",
         "3661", "3711", "4904", "4938", "5871", "5876", "5880", "6446", "6505", "6669"]

SHORT_GROUPS = {
    "S1": [3, 5, 8, 10, 12, 15],
    "S2": [5, 7, 9, 11, 13, 15],
    "S3": [1, 2, 3, 5, 7, 9]
}

LONG_GROUPS = {
    "L1": [30, 35, 40, 45, 50, 60],
    "L2": [21, 24, 27, 30, 33, 36],
    "L3": [60, 65, 70, 75, 80, 85]
}


def main():
    for ma_type in tqdm(MA_TYPE, desc="MA進度", ncols=100):
        tqdm.write(f"正在回測 {ma_type}")
        STRATEGY = f"GMMA_{ma_type}_DDD"  
        for stock in tqdm(STOCK, desc="總股票進度", ncols=100):
            for s_label, short_periods in SHORT_GROUPS.items():
                for l_label, long_periods in LONG_GROUPS.items():
                    mode = f"1D{s_label}{l_label}"
                    tqdm.write(f"回測 {STRATEGY} 股票:{stock} 模式:{mode}")

                    single_output_path = f"output/{STRATEGY}/{stock}/{mode}/"
                    all_output_path = f"output/{STRATEGY}/ETF0050_{STRATEGY}.xlsx"

                    freq = "D"
                    kline = KLineGenerator(
                        stock_id=stock, 
                        timeframe=1,
                        unit=freq
                    )

                    strategy_params = GMMAParams(
                        ma_type=ma_type,
                        short_periods=short_periods,
                        long_periods=long_periods
                    )
                    strategy = GMMAStrategy(strategy_params)

                    backtest_params = BacktestParams(
                        initial_capital=1000000.0,
                        fees=0.001425,
                        slippage=0.0001,
                    )

                    data_path = kline.get_k_line()
                    data_loader = DataLoader(data_path)
                    data = data_loader.load_data()
                    data = data_loader.preprocess_data(fill_method='ffill', add_returns=True)

                    engine = BacktestEngine(backtest_params)
                    engine.set_data(data)
                    signals = strategy.calculate_signals(data)

                    results = engine.run(signals, freq)

                    all_stats = engine.get_all_statistics()
                    exporter = ResultExporter(single_output_path)
                    result = exporter.export_all(data, results, all_stats, strategy_params)

                    exporter.write_df_to_excel(all_output_path, mode, result)
                    tqdm.write(f"完成 {stock} 模式:{mode}")
        tqdm.write(f"完成 {stock} {ma_type}")

if __name__ == "__main__":
    main()
