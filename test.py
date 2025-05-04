import numpy as np
import pandas as pd

def calc_signals(ma: pd.Series, slope_period: int = 5, thresh: float = 0.0) -> pd.Series:
    """
    依照『向量化 OLS β 斜率』邏輯，輸入移動平均 ma，回傳 -1 / 0 / 1 訊號。

    Parameters
    ----------
    ma : pd.Series
        已經算好的移動平均線。
    slope_period : int
        滑動視窗長度，用來計算 β 斜率。
    thresh : float
        閥值；|β| > thresh 才視為趨勢成立。

    Returns
    -------
    pd.Series
        與 ma 同長度的訊號序列（前 slope_period 筆會是 NaN，再來是 -1 / 0 / 1）。
    """
    # === 預先固定 t 序列，可向量化重複利用 ===
    t = np.arange(slope_period)
    t_mean = t.mean()
    denom = ((t - t_mean) ** 2).sum()

    def beta(window: np.ndarray) -> float:
        y_mean = window.mean()
        return ((t - t_mean) * (window - y_mean)).sum() / denom

    # β 序列（向量化 OLS）
    beta_series = (
        ma.rolling(slope_period, min_periods=slope_period)
          .apply(beta, raw=True)
    )

    # 前一根 β（避免使用未來資訊）
    beta_shift = beta_series.shift(1)

    # 轉成訊號
    signals = pd.Series(0, index=ma.index, dtype=int)
    signals[beta_shift >  thresh] =  1
    signals[beta_shift < -thresh] = -1
    return signals


# ---------------------------------------------------------------------------
# ↓↓↓ 示範用法：執行 python calc_signal_demo.py 時就會印出結果 ↓↓↓
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # 假設手上已經有「收盤價」price，這裡先隨機合成一段資料示範
    rng    = pd.date_range("2025-01-01", periods=30, freq="D")
    price  = pd.Series(np.linspace(10, 20, 30) + np.random.normal(0, 0.2, 30), index=rng)

    # 1. 先算 3 日移動平均線 (這步驟可換成你自己的 ma)
    ma = price.rolling(3).mean()

    # 2. 丟進 calc_signals 取得 -1／0／1
    sig = calc_signals(ma, slope_period=5, thresh=0.0)

    print("=== MA ===")
    print(ma.tail(10).round(2))
    print("\n=== Signals ===")
    print(sig.tail(10))
