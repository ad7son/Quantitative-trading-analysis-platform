import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional

@dataclass
class TMACParams:
    """移動平均線交叉策略參數
    
    Attributes:
        ma_type (str): 平均線類型
        short_period (int): 短期移動平均線週期
        mid_period (int): 中期移動平均線週期
        long_period (int): 長期移動平均線週期
    """
    ma_type: str = "EMA"
    short_period: int = 5
    mid_period: int = 20
    long_period: int = 60

class TMACStrategy:
    """移動平均線交叉策略
    
    當短期移動平均線 > 中中期移動平均線 > 長期移動平均線時買入，
    當短期移動平均線 < 中期移動平均線 < 長期移動平均線時賣出。
    
    Attributes:
        params (TMACParams): 策略參數
    """

    def __init__(self, params: Optional[TMACParams] = None):
        """
        初始化策略
        
        Parameters:
        -----------
        params : DMACParams, optional
            策略參數，如果為None則使用默認參數
        """  
        self.params = params or TMACParams()

    def calculate_signals(self, data: pd.DataFrame) -> pd.Series:
        if 'close' not in data.columns:
            raise ValueError("數據必須包含 'close' 列")

        def ma(series, period):
            if self.params.ma_type == "SMA":
                return series.rolling(window=period).mean()
            elif self.params.ma_type == "EMA":
                return series.ewm(span=period, adjust=False).mean()
            elif self.params.ma_type == "WMA":
                weights = np.arange(1, period + 1)
                return series.rolling(period).apply(lambda prices: np.dot(prices, weights)/weights.sum(), raw=True)
            else:
                raise ValueError("不支援的 MA 類型")

        short_ma = ma(data['close'], self.params.short_period)
        mid_ma = ma(data['close'], self.params.mid_period)
        long_ma = ma(data['close'], self.params.long_period)

        signals = pd.Series(0, index=data.index)
        golden_cross = (short_ma > mid_ma) & (mid_ma > long_ma) & (
            (short_ma.shift(1) <= mid_ma.shift(1)) | (mid_ma.shift(1) <= long_ma.shift(1))
        )
        death_cross = (short_ma < mid_ma) & (mid_ma < long_ma) & (
            (short_ma.shift(1) >= mid_ma.shift(1)) | (mid_ma.shift(1) >= long_ma.shift(1))
        )

        signals[golden_cross] = 1
        signals[death_cross] = -1
        return signals
