import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional

@dataclass
class DMACParams:
    """移動平均線交叉策略參數
    
    Attributes:
        fast_period (int): 快速移動平均線週期
        slow_period (int): 慢速移動平均線週期
    """
    fast_period: int = 5
    slow_period: int = 20

class DMACStrategy:
    """移動平均線交叉策略
    
    當快速移動平均線向上穿越慢速移動平均線時買入，
    當快速移動平均線向下穿越慢速移動平均線時賣出。
    
    Attributes:
        params (DMACParams): 策略參數
    """
    
    def __init__(self, params: Optional[DMACParams] = None):
        """
        初始化策略
        
        Parameters:
        -----------
        params : DMACParams, optional
            策略參數，如果為None則使用默認參數
        """
        self.params = params or DMACParams()
    
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
        fast_ma = data['close'].rolling(window=self.params.fast_period).mean()
        slow_ma = data['close'].rolling(window=self.params.slow_period).mean()
        
        # 計算交叉信號
        signals = pd.Series(0, index=data.index)
        
        # 金叉：快線向上穿越慢線
        golden_cross = (fast_ma > slow_ma) & (fast_ma.shift(1) <= slow_ma.shift(1))
        signals[golden_cross] = 1
        
        # 死叉：快線向下穿越慢線
        death_cross = (fast_ma < slow_ma) & (fast_ma.shift(1) >= slow_ma.shift(1))
        signals[death_cross] = -1
        
        return signals 