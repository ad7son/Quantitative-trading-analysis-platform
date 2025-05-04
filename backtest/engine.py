import pandas as pd
import numpy as np
import vectorbt as vbt
from typing import Dict, Any, Optional, Union, Callable
from dataclasses import dataclass

@dataclass
class BacktestParams:
    """回測參數
    
    Attributes:
        initial_capital (float): 初始資金
        fees (float): 交易費用率
        slippage (float): 滑點率
        position_size (float): 每次交易的資金比例
    """
    initial_capital: float = 100000.0
    fees: float = 0.001
    slippage: float = 0.0001

class BacktestEngine:
    """回測引擎
    
    負責執行回測計算，包括：
    - 信號處理
    - 倉位管理
    - 績效計算
    - 風險評估
    
    Attributes:
        params (BacktestParams): 回測參數
        data (pd.DataFrame): 回測數據
        portfolio (Optional[vbt.Portfolio]): 投資組合對象
    """
    
    def __init__(self, params: Optional[BacktestParams] = None):
        """
        初始化回測引擎
        
        Parameters:
        -----------
        params : BacktestParams, optional
            回測參數，如果為None則使用默認參數
        """
        self.params = params or BacktestParams()
        self.data = None
        self.portfolio = None
    
    def set_data(self, data: pd.DataFrame) -> None:
        """
        設置回測數據
        
        Parameters:
        -----------
        data : pd.DataFrame
            回測數據，必須包含 'close' 列
        """
        if 'close' not in data.columns:
            raise ValueError("數據必須包含 'close' 列")
        self.data = data
    
    def run(self, signals: pd.Series, freq: str = '1min') -> Dict[str, Any]:
        """
        執行回測
        
        Parameters:
        -----------
        signals : pd.Series
            交易信號 (1: 買入, -1: 賣出, 0: 持有)
            
        Returns:
        --------
        dict
            回測結果，包含以下鍵：
            - portfolio: vectorbt.Portfolio對象
            - total_return: 總收益率
            - sharpe_ratio: 夏普比率
            - max_drawdown: 最大回撤
            - signals: 交易信號
        """
        if self.data is None:
            raise ValueError("請先設置回測數據")
        
        # 使用vectorbt進行回測
        self.portfolio = vbt.Portfolio.from_signals(
            close=self.data['close'],
            entries=signals == 1,
            exits=signals == -1,
            init_cash=self.params.initial_capital,
            fees=self.params.fees,
            slippage=self.params.slippage,
            freq=freq
        )
        
        return {
            'portfolio': self.portfolio,
            'total_return': self.portfolio.total_return(),
            'sharpe_ratio': self.portfolio.sharpe_ratio(),
            'max_drawdown': self.portfolio.max_drawdown(),
            'signals': signals
        }
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """
        獲取績效指標
        
        Returns:
        --------
        dict
            績效指標字典
        """
        if self.portfolio is None:
            raise ValueError("請先執行回測")
        
        return {
            'total_return': self.portfolio.total_return(),
            'sharpe_ratio': self.portfolio.sharpe_ratio(),
            'max_drawdown': self.portfolio.max_drawdown(),
            'calmar_ratio': self.portfolio.calmar_ratio(),
            'sortino_ratio': self.portfolio.sortino_ratio(),
            'omega_ratio': self.portfolio.omega_ratio()
        }
    
    def get_trade_statistics(self) -> pd.DataFrame:
        """
        獲取交易統計
        
        Returns:
        --------
        pd.DataFrame
            交易統計數據框
        """
        if self.portfolio is None:
            raise ValueError("請先執行回測")
        
        return self.portfolio.stats()
    
    def plot_results(self, save_path: Optional[str] = None) -> None:
        """
        繪製回測結果圖表
        
        Parameters:
        -----------
        save_path : str, optional
            圖表保存路徑
        """
        if self.portfolio is None:
            raise ValueError("請先執行回測")
        
        # 創建圖表
        fig = self.portfolio.plot()
        
        # 保存圖表
        if save_path:
            fig.write_image(save_path)
        
        return fig 

    def get_all_statistics(self) -> pd.DataFrame:
        """
        獲取所有可用的統計數據
        
        Returns:
        --------
        pd.DataFrame
            包含所有統計數據的數據框
        """
        if self.portfolio is None:
            raise ValueError("請先執行回測")
        
        # 獲取基本統計數據
        stats = self.portfolio.stats()

        # 獲取交易記錄
        trades = self.portfolio.trades.records_readable
        
        # 獲取每日收益
        daily_returns = self.portfolio.returns()
        
        # 獲取持倉記錄
        positions = self.portfolio.positions.records_readable
        
        return {
            'stats': stats,
            'trades': trades,
            'daily_returns': daily_returns,
            'positions': positions
        } 