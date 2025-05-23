import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class GMMAParams:
    """Guppy 多重移動平均線策略參數

    Attributes:
        ma_type (str): 平均線類型 (SMA, EMA, WMA)
        short_periods (List[int]): 短期MA線群組週期列表
        long_periods (List[int]): 長期MA線群組週期列表
    """
    ma_type: str = "EMA"
    short_periods: List[int] = field(default_factory=lambda: [3, 5, 8, 10, 12, 15])
    long_periods: List[int] = field(default_factory=lambda: [30, 35, 40, 45, 50, 60])

class GMMAStrategy:
    """Guppy 多重移動平均線策略

    當每條短期MA線群組中的MA線 > 每條長期MA線群組中的MA線時買入
    當每條短期MA線群組中的MA線 < 每條長期MA線群組中的MA線時賣出

    Attributes:
        params (GMMAParams): 策略參數
    """

    def __init__(self, params: Optional[GMMAParams] = None):
        """
        初始化策略
        
        Parameters:
        -----------
        params : GMMAParams, optional
            策略參數，如果為None則使用默認參數
        """  
        self.params = params or GMMAParams()

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

        short_mas = [ma(data['close'], p) for p in self.params.short_periods]
        long_mas = [ma(data['close'], p) for p in self.params.long_periods]

        signals = pd.Series(0, index=data.index)

        for i in range(len(data)):
            if all(short[i] > long[i] for short in short_mas for long in long_mas): # 確保每條短線都 > 每條長線
                if any(short[i-1] <= long[i-1] for short in short_mas for long in long_mas): # 確保是剛突破所產生的買入訊號
                    signals.iloc[i] = 1
            elif all(short[i] < long[i] for short in short_mas for long in long_mas): # 確保每條短線都 < 每條長線
                if any(short[i-1] >= long[i-1] for short in short_mas for long in long_mas): # 確保是剛突破所產生的賣出訊號
                    signals.iloc[i] = -1

        return signals
