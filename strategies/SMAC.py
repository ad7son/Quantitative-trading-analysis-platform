import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional

@dataclass
class SMACParams:
    """移動平均線交叉策略參數
    
    Attributes:
        period (int): 移動平均線週期
    """
    period: int = 5

class SMACStrategy:
    """移動平均線交叉策略
    
    當最新收盤價向上穿越移動平均線時買入，
    當最新收盤價向下穿越移動平均線時賣出。
    
    Attributes:
        params (SMACParams): 策略參數
    """
    
    def __init__(self, params: Optional[SMACParams] = None):
        """
        初始化策略
        
        Parameters:
        -----------
        params : SMACParams, optional
            策略參數，如果為None則使用默認參數
        """
        self.params = params or SMACParams()
    
    def sma(self, data: pd.DataFrame) -> pd.Series:
        return data['close'].rolling(window=self.params.period).mean()

    def ema(self, data: pd.DataFrame) -> pd.Series:
        return data['close'].ewm(span=self.params.period, adjust=False).mean()

    def wma(self, data: pd.DataFrame) -> pd.Series:
        weights = np.arange(1, self.params.period + 1)
        return data['close'].rolling(self.params.period).apply(lambda prices: np.dot(prices, weights)/weights.sum(), raw=True)

    def calculate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        計算交易信號
        
        Parameters:
        -----------
        data : pd.DataFrame
            價格數據，必須包含 'close' 列
            
        Returns:
        --------
        pd.Series
            交易信號 (1: 買入, -1: 賣出, 0: 持有)
        """
        if 'close' not in data.columns:
            raise ValueError("數據必須包含 'close' 列")
        
        # 計算移動平均線
        ma = self.wma(data)
                
        # 計算交叉信號
        signals = pd.Series(0, index=data.index)
        
        # 金叉：快線向上穿越慢線
        golden_cross = (data['close'] > ma) & (data['close'].shift(1) <= ma.shift(1))
        signals[golden_cross] = 1
        
        # 死叉：快線向下穿越慢線
        death_cross = (data['close'] < ma) & (data['close'].shift(1) >= ma.shift(1))
        signals[death_cross] = -1
        
        return signals 