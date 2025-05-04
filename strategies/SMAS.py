import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional

@dataclass
class SMASParams:
    """移動平均線交叉策略參數
    
    Attributes:
        period (int): 移動平均線週期
    """
    ma_type: str = "SMA" 
    ma_period: int = 20
    slope_period: int = 5
    thresh: float = 0.0

class SMASStrategy:
    """移動平均線交叉策略
    
    當最新收盤價向上穿越移動平均線時買入，
    當最新收盤價向下穿越移動平均線時賣出。
    
    Attributes:
        params (SMACParams): 策略參數
    """
    
    def __init__(self, params: Optional[SMASParams] = None):
        """
        初始化策略
        
        Parameters:
        -----------
        params : SMACParams, optional
            策略參數，如果為None則使用默認參數
        """
        self.params = params or SMASParams()
    
    def create_ma(self, data: pd.DataFrame) -> pd.Series:
        # 建立 SMA 線
        if self.params.ma_type == "SMA":
            return data['close'].rolling(window=self.params.period).mean()
        # 建立 EMA 線
        elif self.params.ma_type == "EMA":
            return data['close'].ewm(span=self.params.period, adjust=False).mean()
        # 建立 WMA 線
        elif self.params.ma_type == "WMA":
            weights = np.arange(1, self.params.period + 1)
            return data['close'].rolling(self.params.period).apply(lambda prices: np.dot(prices, weights)/weights.sum(), raw=True)

    def calculate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        計算交易信號
        
        Parameters:
        -----------
        data : pd.DataFrame, 價格數據，必須包含 'close' 列
            
        Returns:
        --------
        signals : pd.Series, 交易信號 (1: 買入, -1: 賣出, 0: 持有)
        """
        if 'close' not in data.columns:
            raise ValueError("數據必須包含 'close' 列")
        
        # 計算移動平均線（ 週期為 self.params.ma_period ）
        ma = self.create_ma(data)
                
        # β 斜率 (向量化 OLS)
        t = np.arange(self.params.slope_period)
        t_mean = t.mean()
        denom = ((t - t_mean) ** 2).sum()
    
        def beta(window: np.ndarray) -> float:
            y_mean = window.mean()
            return ((t - t_mean) * (window - y_mean)).sum() / denom
        
        beta_series = (ma.rolling(self.params.slope_period, min_periods=self.params.slope_period).apply(beta, raw=True))
        beta_shift = beta_series.shift(1)
        
        # 訊號（使用前一根 β 避免未來資訊）
        signals = pd.Series(0, index=data.index)
        signals[beta_shift >  self.params.thresh] =  1
        signals[beta_shift < -self.params.thresh] = -1
        
        return signals 