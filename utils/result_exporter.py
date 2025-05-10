import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import Dict, Any
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']  # 微軟正黑體
plt.rcParams['axes.unicode_minus'] = False  # 用來正常顯示負號

# 設定圖表樣式
plt.style.use('seaborn')
sns.set_palette("husl")

class ResultExporter:
    """回測結果匯出器
    
    負責將回測結果保存為CSV文件並生成視覺化圖表。
    
    Attributes:
        output_dir (str): 輸出目錄
    """
    
    def __init__(self, output_dir: str = 'output'):
        """
        初始化結果匯出器
        
        Parameters:
        -----------
        output_dir : str
            輸出目錄
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # 設定Excel樣式
        self.header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
        self.header_font = Font(name='Microsoft JhengHei', color='FFFFFF', bold=True)
        self.cell_font = Font(name='Microsoft JhengHei')
        self.border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        self.alignment = Alignment(horizontal='center', vertical='center')
    
    def _translate_column_names(self, df: pd.DataFrame, file_type: str) -> pd.DataFrame:
        """
        將DataFrame的欄位名稱翻譯為中文
        
        Parameters:
        -----------
        df : pd.DataFrame or pd.Series
            要翻譯欄位名稱的DataFrame或Series
        file_type : str
            文件類型，用於選擇對應的翻譯字典
            
        Returns:
        --------
        pd.DataFrame or pd.Series
            欄位名稱已翻譯的DataFrame或Series
        """
        # 統計數據欄位翻譯
        stats_translations = {
            'Start': '開始日期',
            'End': '結束日期',
            'Start Value': '起始資金',
            'End Value': '結束資金',
            'Period': '回測期間',
            'Total Return [%]': '總收益率 [%]',
            'Benchmark Return [%]': '基準回報率 [%]',
            'Max Gross Exposure [%]': '最高總曝險 [%]',
            'Total Fees Paid': '累計手續費',
            'Max Drawdown [%]': '最大回撤 [%]',
            'Max Drawdown Duration': '最大回撤持續時間',
            'Total Trades': '交易次數',
            'Total Closed Trades': '已結束交易次數',
            'Total Open Trades': '未平倉交易次數',
            'Open Trade PnL': '未平倉損益',
            'Buy & Hold Return [%]': '買入持有收益率 [%]',
            'Max. Drawdown [%]': '最大回撤 [%]',
            'Avg. Drawdown [%]': '平均回撤 [%]',
            'Max. Drawdown Duration': '最大回撤持續期',
            'Avg. Drawdown Duration': '平均回撤持續期',
            'Recovery Factor': '恢復因子',
            'Sharpe Ratio': '夏普比率',
            'Sortino Ratio': '索提諾比率',
            'Calmar Ratio': '卡瑪比率',
            'Omega Ratio': '歐米伽比率',
            'Value at Risk': '風險價值',
            'Expected Shortfall': '預期損失',
            'Avg. Trade [%]': '平均交易收益 [%]',
            'Avg. Win [%]': '平均盈利 [%]',
            'Avg. Loss [%]': '平均虧損 [%]',
            'Win Rate [%]': '勝率 [%]',
            'Best Trade [%]': '最佳交易 [%]',
            'Worst Trade [%]': '最差交易 [%]',
            'Avg Winning Trade [%]': '平均獲利交易 [%]',
            'Avg Losing Trade [%]': '平均虧損交易 [%]',
            'Avg Winning Trade Duration': '獲利交易平均持倉時間',
            'Avg Losing Trade Duration': '虧損交易平均持倉時間',
            'Avg. Holding Time': '平均持倉時間',
            'Trades': '交易次數',
            'Wins': '盈利次數',
            'Losses': '虧損次數',
            'Win/Loss Ratio': '盈虧比',
            'Profit Factor': '獲利因子',
            'Expectancy': '期望值',
            'SqN': '系統品質數',
            'K-factor': 'K因子',
            'Risk-Return Ratio': '風險收益比',
            'Daily Sharpe': '日夏普比率',
            'Daily Sortino': '日索提諾比率',
            'Daily Calmar': '日卡瑪比率',
            'Daily Omega': '日歐米伽比率',
            'Daily Value at Risk': '日風險價值',
            'Daily Expected Shortfall': '日預期損失',
            'Daily Avg. Trade [%]': '日平均交易收益 [%]',
            'Daily Avg. Win [%]': '日平均盈利 [%]',
            'Daily Avg. Loss [%]': '日平均虧損 [%]',
            'Daily Win Rate [%]': '日勝率 [%]',
            'Daily Best Trade [%]': '日最佳交易 [%]',
            'Daily Worst Trade [%]': '日最差交易 [%]',
            'Daily Avg. Holding Time': '日平均持倉時間',
            'Daily Trades': '日交易次數',
            'Daily Wins': '日盈利次數',
            'Daily Losses': '日虧損次數',
            'Daily Win/Loss Ratio': '日盈虧比',
            'Daily Profit Factor': '日獲利因子',
            'Daily Expectancy': '日期望值',
            'Daily SqN': '日系統品質數',
            'Daily K-factor': '日K因子',
            'Daily Risk-Return Ratio': '日風險收益比'
        }
        
        # 交易記錄欄位翻譯
        trades_translations = {
            'Exit Trade Id': '出場交易ID',
            'Column': '欄位',
            'Size': '交易數量',
            'Entry Timestamp': '進場時間',
            'Avg Entry Price': '平均進場價格',
            'Entry Fees': '進場費用',
            'Exit Timestamp': '出場時間',
            'Avg Exit Price': '平均出場價格',
            'Exit Fees': '出場費用',
            'PnL': '盈虧',
            'Return': '收益率',
            'Direction': '方向',
            'Status': '狀態',
            'Position Id': '持倉ID'
        }
        
        # 持倉記錄欄位翻譯
        positions_translations = {
            'Position Id': '持倉ID',
            'Column': '欄位',
            'Size': '持倉數量',
            'Entry Timestamp': '進場時間',
            'Avg Entry Price': '平均進場價格',
            'Entry Fees': '進場費用',
            'Exit Timestamp': '出場時間',
            'Avg Exit Price': '平均出場價格',
            'Exit Fees': '出場費用',
            'PnL': '盈虧',
            'Return': '收益率',
            'Direction': '方向',
            'Status': '狀態'
        }
        
        # 選擇對應的翻譯字典
        translations = {
            'stats': stats_translations,
            'trades': trades_translations,
            'positions': positions_translations
        }
        
        # 翻譯欄位名稱
        if file_type in translations:
            if isinstance(df, pd.Series):
                # 如果是Series，直接使用rename
                df = df.rename(translations[file_type])
            else:
                # 如果是DataFrame，使用rename(columns=...)
                df = df.rename(columns=translations[file_type])
        
        return df
    
    def save_statistics(self, results: Dict[str, Any]) -> None:
        """
        保存統計數據到CSV文件
        
        Parameters:
        -----------
        results : dict
            回測結果字典
        """
        # 保存基本統計數據
        stats_df = self._translate_column_names(results['stats'], 'stats')
        # 將 Series 轉換為 DataFrame 並設置索引名稱
        stats_df = pd.DataFrame(stats_df)
        stats_df.index.name = '指標'
        stats_df.to_csv(f'{self.output_dir}/詳細數據.csv')
        
        # 保存交易記錄
        trades_df = self._translate_column_names(results['trades'], 'trades')
        trades_df.to_csv(f'{self.output_dir}/交易紀錄.csv', index=False)
        
        # 保存每日收益
        daily_returns = results['daily_returns']
        daily_returns.name = '每單位收益率'
        daily_returns.to_csv(f'{self.output_dir}/單位收益.csv')
        
        # 保存持倉記錄
        positions_df = self._translate_column_names(results['positions'], 'positions')
        positions_df.to_csv(f'{self.output_dir}/持倉記錄.csv', index=False)

        return stats_df
            
    def plot_results(self, data: pd.DataFrame, results: Dict[str, Any], 
                    all_stats: Dict[str, Any], strategy_params) -> None:
        """
        繪製回測結果圖表
        
        Parameters:
        -----------
        data : pd.DataFrame
            原始數據
        results : dict
            回測結果
        all_stats : dict
            所有統計數據
        strategy_params
            策略參數
        """
        # 價格和移動平均線圖
        plt.figure(figsize=(15, 6))
        data['close'].plot(label='收盤價')
        
        # 根據策略參數設定移動平均線及beta值
        ma = strategy_params.ma
        beta = strategy_params.beta

        # 繪製移動平均線及beta值
        ma.plot(label=f'{strategy_params.ma_period}日 {strategy_params.ma_type}')
        beta.plot(label=f'{strategy_params.slope_period}日斜率')
        plt.title('價格和移動平均線')
        plt.legend()
        plt.savefig(f'{self.output_dir}/價格和移動平均線.png')
        plt.close()
        
        # 投資組合價值圖
        plt.figure(figsize=(15, 6))
        results['portfolio'].value().plot()
        plt.title('投資組合價值')
        plt.savefig(f'{self.output_dir}/投資組合價值.png')
        plt.close()
        
        # 每月度收益熱力圖
        plt.figure(figsize=(15, 8))
        daily_returns = all_stats['daily_returns']
        daily_returns_matrix = daily_returns.to_frame()
        daily_returns_matrix.index = pd.to_datetime(daily_returns_matrix.index)
        daily_returns_matrix['month'] = daily_returns_matrix.index.month
        daily_returns_matrix['year'] = daily_returns_matrix.index.year
        pivot_table = daily_returns_matrix.pivot_table(
            values=daily_returns_matrix.columns[0],
            index='year',
            columns='month',
            aggfunc='sum'
        )
        sns.heatmap(pivot_table, annot=True, fmt='.2%', cmap='RdYlGn', center=0)
        plt.title('月度收益熱力圖')
        plt.savefig(f'{self.output_dir}/月度收益熱力圖.png')
        plt.close()
        
        # 權益曲線和回撤圖
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
        
        # 權益曲線
        portfolio_value = results['portfolio'].value()
        portfolio_value.plot(ax=ax1)
        ax1.set_title('權益曲線')
        
        # 回撤圖
        drawdown = results['portfolio'].drawdown()
        drawdown.plot(ax=ax2, color='red')
        ax2.set_title('回撤')
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/權益曲線和回撤圖.png')
        plt.close()

    def _apply_excel_styling(self, worksheet):
        """應用Excel樣式"""
        for row in worksheet.iter_rows():
            for cell in row:
                cell.font = self.cell_font
                cell.border = self.border
                cell.alignment = self.alignment
                
                # 設定標題列樣式
                if cell.row == 1:
                    cell.font = self.header_font
                    cell.fill = self.header_fill
                
                # 自動調整欄寬
                column_letter = get_column_letter(cell.column)
                max_length = max(len(str(cell.value)) for cell in worksheet[column_letter])
                worksheet.column_dimensions[column_letter].width = max_length + 2

    def _create_performance_chart(self, data: pd.DataFrame, results: Dict[str, Any], output_path: str):
        """創建績效圖表"""
        plt.figure(figsize=(15, 10))
        
        # 繪製累計收益曲線
        plt.subplot(2, 2, 1)
        cumulative_returns = (1 + results['daily_returns']).cumprod()
        plt.plot(cumulative_returns.index, cumulative_returns.values, label='策略收益')
        plt.title('累計收益曲線')
        plt.xlabel('日期')
        plt.ylabel('累計收益')
        plt.legend()
        plt.grid(True)
        
        # 繪製回撤圖
        plt.subplot(2, 2, 2)
        drawdown = results['portfolio'].drawdown()
        plt.fill_between(drawdown.index, drawdown.values, 0, color='red', alpha=0.3)
        plt.title('回撤分析')
        plt.xlabel('日期')
        plt.ylabel('回撤幅度')
        plt.grid(True)
        
        # 繪製月度收益熱力圖
        plt.subplot(2, 2, 3)
        monthly_returns = results['daily_returns'].resample('M').apply(lambda x: (1 + x).prod() - 1)
        monthly_returns = monthly_returns.to_frame()
        monthly_returns.index = monthly_returns.index.strftime('%Y-%m')
        sns.heatmap(monthly_returns, annot=True, fmt='.2%', cmap='RdYlGn', center=0)
        plt.title('月度收益熱力圖')
        
        # 繪製交易分布圖
        plt.subplot(2, 2, 4)
        trades = results['trades']
        if not trades.empty:
            sns.histplot(data=trades, x='Return', bins=50)
            plt.title('交易收益分布')
            plt.xlabel('收益率')
            plt.ylabel('頻率')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_path, 'performance_chart.png'))
        plt.close()

    def export_all(self, data: pd.DataFrame, results: Dict[str, Any], stats: Dict[str, Any], strategy_params: Any) -> pd.DataFrame:
        """匯出所有結果"""
        # 創建績效圖表
        self._create_performance_chart(data, results, self.output_dir)
        
        # 保存統計數據
        stats_df = self.save_statistics(stats)
        
        # 保存到Excel並應用樣式
        excel_path = os.path.join(self.output_dir, '詳細數據.xlsx')
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            stats_df.to_excel(writer, sheet_name='統計數據')
            results['trades'].to_excel(writer, sheet_name='交易記錄', index=False)
            results['daily_returns'].to_frame('每單位收益率').to_excel(writer, sheet_name='單位收益')
            
            # 應用Excel樣式
            workbook = writer.book
            for worksheet in workbook.worksheets:
                self._apply_excel_styling(worksheet)
        
        return stats_df

    def write_df_to_excel(self, file_path: str, sheet_name: str, df: pd.DataFrame) -> None:
        """將DataFrame寫入Excel並應用樣式"""
        if os.path.exists(file_path):
            with pd.ExcelWriter(file_path, engine='openpyxl', mode='a') as writer:
                df.to_excel(writer, sheet_name=sheet_name)
                workbook = writer.book
                worksheet = workbook[sheet_name]
                self._apply_excel_styling(worksheet)
        else:
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=sheet_name)
                workbook = writer.book
                worksheet = workbook[sheet_name]
                self._apply_excel_styling(worksheet)

        
