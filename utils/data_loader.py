import pandas as pd
import numpy as np
from typing import Union, Optional
from pathlib import Path

class DataLoader:
    """數據加載和預處理類
    
    用於加載和處理金融市場數據，支持CSV和Excel格式。
    
    Attributes:
        data_path (Union[str, Path]): 數據文件路徑
        data (Optional[pd.DataFrame]): 加載的數據
    """
    
    def __init__(self, data_path: Union[str, Path]):
        """
        初始化數據加載器
        
        Parameters:
        -----------
        data_path : Union[str, Path]
            數據文件路徑
        """
        self.data_path = Path(data_path)
        self.data = None
    
    def load_data(self, **kwargs) -> pd.DataFrame:
        """
        加載數據文件
        
        Parameters:
        -----------
        **kwargs : dict
            傳遞給pandas讀取函數的額外參數
            
        Returns:
        --------
        pd.DataFrame
            處理後的數據框
            
        Raises:
        -------
        ValueError
            當文件格式不支持或缺少必要列時
        """
        if not self.data_path.exists():
            raise FileNotFoundError(f"找不到文件: {self.data_path}")
            
        # 根據文件類型選擇適當的加載方法
        if self.data_path.suffix.lower() == '.csv':
            self.data = pd.read_csv(self.data_path, **kwargs)
        elif self.data_path.suffix.lower() in ['.xlsx', '.xls']:
            self.data = pd.read_excel(self.data_path, **kwargs)
        else:
            raise ValueError(f"不支持的文件格式: {self.data_path.suffix}")
        
        # 確保數據包含必要的列
        required_columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in self.data.columns]
        if missing_columns:
            raise ValueError(f"數據缺少必要的列: {missing_columns}")
        
        # 設置日期索引
        self.data['datetime'] = pd.to_datetime(self.data['datetime'])
        self.data.set_index('datetime', inplace=True)
        
        # 確保數據按時間排序
        self.data.sort_index(inplace=True)
        
        return self.data
    
    def preprocess_data(self, fill_method: str = 'ffill', add_returns: bool = True) -> pd.DataFrame:
        """
        數據預處理
        
        Parameters:
        -----------
        fill_method : str, optional
            填充缺失值的方法，默認為'ffill'
        add_returns : bool, optional
            是否添加收益率列，默認為True
            
        Returns:
        --------
        pd.DataFrame
            處理後的數據框
        """
        if self.data is None:
            self.load_data()
        
        # 處理缺失值
        self._fill_missing_values(fill_method)
        
        # 添加技術指標
        if add_returns:
            self.data['returns'] = self.data['close'].pct_change()
        
        return self.data
    
    def get_data(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """
        獲取指定時間範圍的數據
        
        Parameters:
        -----------
        start_date : str, optional
            開始日期，格式：'YYYY-MM-DD'
        end_date : str, optional
            結束日期，格式：'YYYY-MM-DD'
            
        Returns:
        --------
        pd.DataFrame
            指定時間範圍的數據
        """
        if self.data is None:
            self.load_data()
            
        if start_date is not None:
            start_date = pd.to_datetime(start_date)
            self.data = self.data[self.data.index >= start_date]
            
        if end_date is not None:
            end_date = pd.to_datetime(end_date)
            self.data = self.data[self.data.index <= end_date]
            
        return self.data
    
    def reset(self) -> None:
        """重置數據加載器狀態"""
        self.data = None 
    
    def _fill_missing_values(self, fill_method: str = 'ffill') -> None:
        """
        填充缺失值
        
        Parameters:
        -----------
        fill_method : str
            填充方法，可選 'ffill'（向前填充）或 'bfill'（向後填充）
        """
        if fill_method == 'ffill':
            self.data = self.data.ffill()
        elif fill_method == 'bfill':
            self.data = self.data.bfill()
        else:
            raise ValueError("fill_method 必須是 'ffill' 或 'bfill'") 