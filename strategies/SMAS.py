import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional

@dataclass
class SMASParams:
    """移動平均線斜率策略參數
    
    :param method: str, beta 及 theta 的計算模式
    :param ma_type: str, 移動平均線種類
    :param ma_period: int, 移動平均線週期
    :param slope_period: int, 斜率窗，即報告中的 N 值
    :param threshold: float, 閾值，即報告中的 theta 值
    """
    method: str = "M1"
    ma_type: str = "SMA" 
    ma_period: int = 20
    slope_period: int = 5
    threshold: float = 0.0

    ma: pd.Series = None
    beta: pd.Series = None

class SMASStrategy:
    """移動平均線斜率策略
   
    Attributes:
        params (SMACParams): 策略參數
    """
    
    def __init__(self, params: Optional[SMASParams] = None):
        """
        初始化策略
        
        :param params: Optional[SMASParams], 策略參數，如果為None則使用默認參數
        """
        self.params = params or SMASParams()

    def create_ma(self, data: pd.DataFrame, period: int) -> pd.Series:
        """
        依照 ma_type 建立 MA 線

        :param data: pd.DataFrame, K線資料
        :param period: int, 移動平均線週期
        :return ma: pd.Series, 移動平均線
        """
        if self.params.ma_type == "SMA":
            return data['close'].rolling(window=period).mean()
        elif self.params.ma_type == "EMA":
            return data['close'].ewm(span=period, adjust=False).mean()
        elif self.params.ma_type == "WMA":
            weights = np.arange(1, period + 1)
            return data['close'].rolling(period).apply(lambda prices: np.dot(prices, weights)/weights.sum(), raw=True)

    def calculate_beta(self, method: str, ma: pd.Series, period: int) -> pd.Series:
        """
        計算 beta 值
        
        :param method: str, 計算方式
        :param ma: pd.Series, 移動平均線
        :param period: int, 斜率窗
        :return beta: pd.Series, beta 值
        """
        # 計算移動平均線的變化
        slope = ma.diff(period) / period
        
        if method == "M1":
            # M1：絕對價差/Bar
            beta = slope
        elif method == "M2":
            # M2：%報酬/Bar
            beta = slope / ma.shift(1) * 100
        elif method == "M3":
            # M3：Z-score
            # 使用 rolling window 計算均值和標準差
            mean = slope.rolling(window=period).mean()
            std = slope.rolling(window=period).std()
            beta = (slope - mean) / std
        elif method == "M4":
            # M4：IQR
            # 計算 M2：%報酬/Bar 作為 beta
            beta = slope / ma.shift(1)
            # 使用整個歷史資料計算四分位數
            q1 = beta.expanding().quantile(0.25)  # 下四分位數
            q3 = beta.expanding().quantile(0.75)  # 上四分位數
            # 計算 IQR 並更改 threshold
            self.params.threshold = q3 - q1
        else:
            raise ValueError(f"不支援的計算方式: {method}")
            
        # 將 beta 值向後移動一個時間單位，以避免使用未來資訊
        beta = beta.shift(1)
        return beta

    def calculate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        計算交易信號
        
        :param data: pd.DataFrame, K線資料
        :return signals: pd.Series, 交易信號 (1: 買入, -1: 賣出, 0: 持有)
        """        
        # 計算移動平均線（ 週期為 self.params.ma_period ）
        self.params.ma = self.create_ma(data, self.params.ma_period)
        
        # β 值（根據 self.params.method 計算）
        self.params.beta = self.calculate_beta(self.params.method, self.params.ma, self.params.slope_period)
        
        # 訊號
        signals = pd.Series(0, index=data.index)
        signals[self.params.beta >  self.params.threshold] =  1
        signals[self.params.beta < -self.params.threshold] = -1

        return signals 