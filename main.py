import os
import multiprocessing
import logging
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm
import matplotlib
matplotlib.use('Agg')  # 設定 matplotlib 使用非互動式後端
import matplotlib.pyplot as plt
from utils.data_loader import DataLoader
from backtest import BacktestEngine, BacktestParams
from utils.result_exporter import ResultExporter
from utils.kline_generator import KLineGenerator
from utils.excel_processor import process_excel_file
# 引入策略類別
from strategies.SMAS import SMASStrategy, SMASParams  
from datetime import datetime

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading.log'),
        logging.StreamHandler()
    ]
)

# 股票代碼列表
STOCK = [
    "1101", "1216", "1301", "1303", "2002", "2207", "2301", "2303", "2308", "2317", 
    "2327", "2330", "2345", "2357", "2379", "2382", "2395", "2412", "2454", "2603", 
    "2609", "2615", "2880", "2881", "2882", "2883", "2884", "2885", "2886", "2887",
    "2890", "2891", "2892", "2912", "3008", "3017", "3034", "3037", "3045", "3231",
    "3661", "3711", "4904", "4938", "5871", "5876", "5880", "6446", "6505", "6669"
]

# 策略設定
STRATEGY = "SMAS"

# 移動平均線類型
MA_TYPES = {
    "SMA": {"settings": ["SMA_05"]},
    # "EMA": {"settings": ["EMA_01", "EMA_02", "EMA_03", "EMA_04", "EMA_05"]},
    # "WMA": {"settings": ["WMA_01", "WMA_02", "WMA_03", "WMA_04", "WMA_05"]}
}

# 策略參數設定
STRATEGY_PARAMS = {
    "01": {
        "Kline": ["D", "D"],
        "ma_period": [150, 200],
        "slope_period": [20, 26],
        "method": ["M1", "M2"],
        "threshold": {
            "M1": [0.0],
            "M2": [0.0, 0.1, 0.25]
        }
    },
    "02": {
        "Kline": ["D", "D"],
        "ma_period": [50, 100],
        "slope_period": [10, 20],
        "method": ["M2"],
        "threshold": {
            "M2": [0.0, 0.1, 0.2]
        }
    },
    "03": {
        "Kline": ["D", "D"],
        "ma_period": [20, 34, 50],
        "slope_period": [5, 10, 14],
        "method": ["M2"],
        "threshold": {
            "M2": [0.0, 0.07, 0.15]
        }
    },
    "04": {
        "Kline": ["min", "M"],
        "ma_period": [10, 20, 30],
        "slope_period": [5, 7, 10],
        "method": ["M2", "M3"],
        "threshold": {
            "M2": [0.0, 0.05, 0.1],
            "M3": [0.3, 0.4, 0.5]
        }
    },
    "05": {
        "Kline": ["min", "M"],
        "ma_period": [5, 8, 13],
        "slope_period": [3, 5],
        "method": ["M1", "M2", "M4"],
        "threshold": {
            "M1": [0.0],
            "M2": [0.001, 0.003, 0.005],
            "M4": [0.0]
        }
    }
}

# 執行緒池大小
MAX_WORKERS = multiprocessing.cpu_count()  # 使用 CPU 核心數

# 進程計數器
process_counter = 0
process_counter_lock = multiprocessing.Lock()

def get_process_number():
    global process_counter
    with process_counter_lock:
        process_counter = (process_counter % MAX_WORKERS) + 1
        return process_counter

def process_single_backtest(kline, stock, ma_type, setting, ma_period, slope_period, method, threshold, index):
    try:
        current_time = datetime.now().strftime("%H:%M:%S")
        process_id = get_process_number()
        tqdm.write(f"[{current_time}] 進程 {process_id:02d} | 開始回測 {STRATEGY} | 股票:{stock} | MA類型:{ma_type} | 設定:{setting} | 週期:{ma_period} | 斜率區間:{slope_period} | 方法:{method} | 門檻:{threshold}")

        # 設定輸出路徑
        mode = f"1{str(kline[1])}{str(ma_period)}{str(kline[1])}{str(slope_period)}M{str(method)}T{str(index)}"
        single_output_path = f"output/{STRATEGY}/{setting}/{stock}/{mode}/"
        all_output_path = f"output/{STRATEGY}/{setting}/ETF0050_{STRATEGY}_{setting}.xlsx"
        
        # 確保輸出目錄存在
        os.makedirs(single_output_path, exist_ok=True)
        
        # 設定K 線參數
        freq = kline[0]
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
        start_time = datetime.now()
        all_stats = engine.get_all_statistics()
        exporter = ResultExporter(single_output_path)
        result = exporter.export_all(data, results, all_stats, strategy_params)
        end_time = datetime.now()
        duration = end_time - start_time
        tqdm.write(f"測試完成時間: {duration}")
        
        # 將結果匯出至總表
        exporter.write_df_to_excel(all_output_path, mode, result)
        
        # 清理 matplotlib 圖形
        plt.close('all')
        
    except Exception as e:
        current_time = datetime.now().strftime("%H:%M:%S")
        process_id = get_process_number()
        tqdm.write(f"[{current_time}] 進程 {process_id:02d} | 錯誤: {str(e)}")
        logging.error(f"回測過程發生錯誤: {str(e)}", exc_info=True)
        plt.close('all')

def main(ma_type, setting):
    setting_key = setting[4:]  # 取得設定編號
    params = STRATEGY_PARAMS[setting_key]
    
    # 計算當前設定的總任務數
    total_tasks = len(STOCK) * len(params["ma_period"]) * len(params["slope_period"]) * len(params["method"]) * len(params["threshold"][params["method"][0]])
    
    # 使用 tqdm 顯示當前設定的進度
    with tqdm(total=total_tasks, desc=f"回測進度 ({ma_type} - {setting})", ncols=100, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]') as pbar:
        for stock in STOCK:
            for ma_period in params["ma_period"]:
                for slope_period in params["slope_period"]:
                    for method in params["method"]:
                        for index, threshold in enumerate(params["threshold"][method]):
                            process_single_backtest(params["Kline"], stock, ma_type, setting, ma_period, slope_period, method, threshold, index)
                            pbar.update(1)
    
    # 處理總表
    all_output_path = f"output/{STRATEGY}/{setting}/ETF0050_{STRATEGY}_{setting}.xlsx"
    process_excel_file(all_output_path)

if __name__ == "__main__":
    try:
        start_time = datetime.now()
        tqdm.write(f"開始回測時間: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        tqdm.write(f"總共 {len(MA_TYPES)} 種 MA 類型，{sum(len(ma_type['settings']) for ma_type in MA_TYPES.values())} 種設定組合")
        tqdm.write(f"使用 {MAX_WORKERS} 個進程進行並行處理\n")
        
        # 計算總任務數（MA類型 * 設定數）
        total_settings = sum(len(ma_type['settings']) for ma_type in MA_TYPES.values())
        
        # 先創建整體進度條
        with tqdm(total=total_settings, desc="整體進度", position=0, ncols=100, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]') as pbar:
            with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = []
                
                # 提交所有任務
                for ma_type, ma_info in MA_TYPES.items():
                    for setting in ma_info["settings"]:
                        future = executor.submit(main, ma_type, setting)
                        futures.append(future)
                
                # 等待所有任務完成並更新進度
                for future in futures:
                    future.result()
                    pbar.update(1)
        
        end_time = datetime.now()
        duration = end_time - start_time
        tqdm.write(f"回測完成時間: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        tqdm.write(f"總執行時間: {duration}")
        
    except Exception as e:
        logging.error(f"程式執行發生錯誤: {str(e)}", exc_info=True)
