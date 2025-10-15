# -*- coding: utf-8 -*-
"""
雲林縣日統客運 (7011, 7012路線) 113年度營運數據分析與視覺化 (Excel版)

本程式會讀取指定的 Excel 檔案，整合其內部的所有工作表(worksheets)，
進行數據清洗與分析，並根據分析結果生成一系列圖表，以視覺化方式呈現客運的營運狀況。

更新日誌：
- 新增週間總運量分析圖表
- 新增學生平日通勤時段分析圖表
- 新增長者通勤時段分析圖表
- 新增長者熱門下車目的地分析圖表
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from matplotlib.font_manager import fontManager

def setup_chinese_font():
    """
    設定 Matplotlib 以正確顯示中文。
    """
    font_list = ['Microsoft JhengHei', 'PingFang TC', 'Heiti TC', 'LiHei Pro']
    for font_name in font_list:
        if any(font.name == font_name for font in fontManager.ttflist):
            plt.rcParams['font.sans-serif'] = [font_name]
            plt.rcParams['axes.unicode_minus'] = False
            print(f"成功設定中文字型為: {font_name}")
            return
    print("警告：未找到建議的中文字型，圖表中的中文可能無法正常顯示。")
    plt.rcParams['axes.unicode_minus'] = False

def load_data(file_path="日統113.xlsx"):
    """
    讀取單一Excel檔案中的所有工作表。
    """
    print(f"步驟 1: 開始讀取 Excel 檔案 '{file_path}'...")
    if not os.path.exists(file_path):
        print(f"錯誤：找不到檔案 '{file_path}'。")
        return None
    try:
        all_sheets = pd.read_excel(file_path, sheet_name=None)
        print(f"找到 {len(all_sheets)} 個工作表。")
        full_df = pd.concat(all_sheets.values(), ignore_index=True)
        print(f"資料整合完成，共 {len(full_df)} 筆乘車紀錄。")
        return full_df
    except Exception as e:
        print(f"讀取 Excel 檔案時發生錯誤: {e}")
        return None

def classify_ticket(name):
    """
    根據卡別名稱進行分類的輔助函式。
    """
    name_str = str(name)
    if '通勤' in name_str:
        return '通勤族群'
    elif '學生' in name_str:
        return '學生族群'
    elif '敬老' in name_str:
        return '敬老族群'
    elif '愛心' in name_str or '博愛' in name_str or '陪伴' in name_str:
        return '關懷族群'
    elif '一般' in name_str:
        return '一般乘客'
    else:
        return '其他'

def preprocess_data(df):
    """
    對整合後的 DataFrame 進行預處理，並衍生分析所需欄位。
    """
    if df is None:
        print("錯誤：傳入的資料為空，無法預處理。")
        return None
        
    print("步驟 2: 開始進行資料預處理...")
    full_df = df.copy()
    
    # 處理日期時間欄位
    for col in ['上車時間', '下車時間']:
        series_str = full_df[col].astype(str)
        series_replaced = series_str.str.replace('上午', 'AM').str.replace('下午', 'PM')
        full_df[col] = pd.to_datetime(series_replaced, format='%Y/%m/%d %p %I:%M:%S', errors='coerce')

    # 清理站名
    for col in ['上車站名', '下車站名']:
        if col in full_df.columns and pd.api.types.is_object_dtype(full_df[col]):
            full_df[col] = full_df[col].str.strip()

    # 移除關鍵空值
    initial_rows = len(full_df)
    full_df.dropna(subset=['上車時間', '下車時間', '上車站名', '下車站名'], inplace=True)
    if len(full_df) < initial_rows:
        print(f"移除了 {initial_rows - len(full_df)} 筆記錄。")

    # 新增分析所需衍生欄位
    print("正在新增 月份, 小時, 星期, 日期類型, 票種分類 等分析欄位...")
    full_df['月份'] = full_df['上車時間'].dt.month
    full_df['小時'] = full_df['上車時間'].dt.hour
    
    day_map = {0: '星期一', 1: '星期二', 2: '星期三', 3: '星期四', 4: '星期五', 5: '星期六', 6: '星期日'}
    full_df['星期'] = full_df['上車時間'].dt.weekday.map(day_map)
    full_df['日期類型'] = full_df['上車時間'].dt.weekday.apply(lambda x: '平日' if x < 5 else '假日')
    full_df['票種分類'] = full_df['卡別名稱'].apply(classify_ticket)
    
    print("資料預處理完成。")
    return full_df

# --- 原有繪圖函式 (部分微調以符合新的程式結構) ---

def plot_monthly_ridership(df):
    print("正在生成圖表 1: 各月份旅運量分析...")
    monthly_counts = df.groupby(['月份', '路線']).size().unstack(fill_value=0)
    monthly_counts.plot(kind='bar', figsize=(14, 8), width=0.8, colormap='viridis')
    plt.title('圖1：113年度日統客運各月份旅運量分析 (7011 & 7012路線)', fontsize=16)
    plt.xlabel('月份', fontsize=12)
    plt.ylabel('總人次', fontsize=12)
    plt.xticks(ticks=range(len(monthly_counts.index)), labels=monthly_counts.index, rotation=0)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend(title='路線')
    for container in plt.gca().containers:
        plt.gca().bar_label(container, label_type='edge', fontsize=9, padding=3)
    plt.tight_layout()
    plt.savefig("1_monthly_ridership.png", dpi=300)
    plt.close()
    print("圖表 1 已儲存。")

def plot_ticket_type_distribution(df):
    print("正在生成圖表 2: 乘客票種結構分析...")
    ticket_counts = df['票種分類'].value_counts()
    plt.figure(figsize=(12, 10))
    patches, texts, autotexts = plt.pie(ticket_counts, labels=ticket_counts.index, autopct='%1.1f%%', startangle=140, pctdistance=0.85, colors=sns.color_palette('pastel'))
    for text in texts: text.set_fontsize(12)
    for autotext in autotexts:
        autotext.set_fontsize(11)
        autotext.set_color('black')
    centre_circle = plt.Circle((0, 0), 0.70, fc='white')
    fig = plt.gcf()
    fig.gca().add_artist(centre_circle)
    plt.title('圖2：113年度乘客票種結構分析', fontsize=16)
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig("2_ticket_type_distribution.png", dpi=300)
    plt.close()
    print("圖表 2 已儲存。")

def plot_hourly_distribution(df):
    print("正在生成圖表 3: 全日各時段旅次分佈...")
    hourly_counts = df['小時'].value_counts().sort_index()
    plt.figure(figsize=(14, 7))
    sns.barplot(x=hourly_counts.index, y=hourly_counts.values, palette='plasma', hue=hourly_counts.index, legend=False)
    plt.title('圖3：全日各時段旅次分佈 (0-23時)', fontsize=16)
    plt.xlabel('小時', fontsize=12)
    plt.ylabel('總人次', fontsize=12)
    plt.xticks(range(0, 24))
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig("3_hourly_distribution.png", dpi=300)
    plt.close()
    print("圖表 3 已儲存。")

def plot_weekday_weekend_comparison(df):
    print("正在生成圖表 4: 平假日旅次模式比較...")
    comparison_counts = df.groupby(['日期類型', '小時']).size().unstack(fill_value=0).T.reindex(range(24), fill_value=0)
    plt.figure(figsize=(14, 8))
    plt.plot(comparison_counts.index, comparison_counts['平日'], marker='o', linestyle='-', label='平日 (週一至五)')
    plt.plot(comparison_counts.index, comparison_counts['假日'], marker='s', linestyle='--', label='假日 (週六、日)')
    plt.title('圖4：平假日各時段旅次模式比較', fontsize=16)
    plt.xlabel('小時', fontsize=12)
    plt.ylabel('總人次', fontsize=12)
    plt.xticks(range(0, 24))
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.legend(fontsize=12)
    plt.tight_layout()
    plt.savefig("4_weekday_weekend_comparison.png", dpi=300)
    plt.close()
    print("圖表 4 已儲存。")

def plot_top_stations(df, top_n=15):
    print(f"正在生成圖表 5: 前 {top_n} 大熱門站點分析...")
    on_counts = df['上車站名'].value_counts()
    off_counts = df['下車站名'].value_counts()
    total_counts = on_counts.add(off_counts, fill_value=0).sort_values(ascending=False).head(top_n)
    plt.figure(figsize=(12, 10))
    sns.barplot(x=total_counts.values, y=total_counts.index, palette='viridis', orient='h', hue=total_counts.index, legend=False)
    plt.title(f'圖5：年度前 {top_n} 大熱門站點 (總上下車人次)', fontsize=16)
    plt.xlabel('總上下車人次', fontsize=12)
    plt.ylabel('站點名稱', fontsize=12)
    for index, value in enumerate(total_counts.values):
        plt.text(value, index, f' {value:.0f}', va='center', fontsize=10)
    plt.tight_layout()
    plt.savefig("5_top_stations.png", dpi=300)
    plt.close()
    print("圖表 5 已儲存。")

def plot_top_od_pairs(df, top_n=10):
    print(f"正在生成圖表 6: 前 {top_n} 大旅運OD走廊分析...")
    df['OD_Pair'] = df['上車站名'].astype(str) + ' → ' + df['下車站名'].astype(str)
    od_counts = df['OD_Pair'].value_counts().head(top_n)
    plt.figure(figsize=(12, 8))
    sns.barplot(x=od_counts.values, y=od_counts.index, palette='rocket', orient='h', hue=od_counts.index, legend=False)
    plt.title(f'圖6：年度前 {top_n} 大旅運OD走廊', fontsize=16)
    plt.xlabel('總人次', fontsize=12)
    plt.ylabel('起訖點 (OD)', fontsize=12)
    for index, value in enumerate(od_counts.values):
        plt.text(value, index, f' {value}', va='center', fontsize=10)
    plt.tight_layout()
    plt.savefig("6_top_od_pairs.png", dpi=300)
    plt.close()
    print("圖表 6 已儲存。")

# --- 新增的四個繪圖函式 ---

def plot_weekly_ridership(df):
    """
    分析並繪製週間總運量。
    """
    print("正在生成圖表 7: 週間總運量分析...")
    week_order = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
    weekly_counts = df['星期'].value_counts().reindex(week_order)
    
    plt.figure(figsize=(12, 7))
    sns.barplot(x=weekly_counts.index, y=weekly_counts.values, palette='GnBu_d', hue=weekly_counts.index, legend=False)
    
    plt.title('圖7：週間總運量分析', fontsize=16)
    plt.xlabel('星期', fontsize=12)
    plt.ylabel('總人次', fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # --- 修正開始 ---
    # 計算一個小的垂直位移，讓文字標籤在長條圖的上方，而不是正好貼在頂端
    # 這取代了先前版本中無效的 'pad' 參數
    y_offset = weekly_counts.max() * 0.01 

    for index, value in enumerate(weekly_counts.values):
        # 移除無效的 'pad' 參數，並在 Y 軸上增加一個小位移 (y_offset)
        if pd.notna(value): # 增加一個檢查，確保值不是NaN
            plt.text(index, value + y_offset, f'{int(value)}', ha='center', va='bottom', fontsize=10)
    # --- 修正結束 ---

    plt.tight_layout()
    plt.savefig("7_weekly_ridership.png", dpi=300)
    plt.close()
    print("圖表 7 已儲存。")

def plot_student_commute(df):
    """
    分析並繪製學生平日的通勤時段。
    """
    print("正在生成圖表 8: 學生平日通勤時段分析...")
    students_df = df[(df['票種分類'] == '學生族群') & (df['日期類型'] == '平日')]
    hourly_counts = students_df['小時'].value_counts().reindex(range(24), fill_value=0)
    
    plt.figure(figsize=(14, 7))
    sns.lineplot(x=hourly_counts.index, y=hourly_counts.values, marker='o', color='dodgerblue', label='學生平日旅次')
    
    plt.title('圖8：學生平日各時段旅次分佈', fontsize=16)
    plt.xlabel('小時', fontsize=12)
    plt.ylabel('總人次', fontsize=12)
    plt.xticks(range(24))
    plt.grid(True, which='both', linestyle='--', alpha=0.6)

    plt.legend()
    plt.tight_layout()
    plt.savefig("8_student_commute.png", dpi=300)
    plt.close()
    print("圖表 8 已儲存。")

def plot_senior_commute(df):
    """
    分析並繪製長者的通勤時段。
    """
    print("正在生成圖表 9: 長者通勤時段分析...")
    seniors_df = df[df['票種分類'] == '敬老族群']
    hourly_counts = seniors_df['小時'].value_counts().reindex(range(24), fill_value=0)
    
    plt.figure(figsize=(14, 7))
    sns.barplot(x=hourly_counts.index, y=hourly_counts.values, palette='viridis', hue=hourly_counts.index, legend=False)
    
    plt.title('圖9：長者各時段旅次分佈', fontsize=16)
    plt.xlabel('小時', fontsize=12)
    plt.ylabel('總人次', fontsize=12)
    plt.xticks(range(24))
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    plt.tight_layout()
    plt.savefig("9_senior_commute.png", dpi=300)
    plt.close()
    print("圖表 9 已儲存。")

def plot_senior_top_stations(df, top_n=10):
    """
    分析並繪製長者熱門下車目的地。
    """
    print(f"正在生成圖表 10: 前 {top_n} 大長者熱門下車目的地...")
    seniors_df = df[df['票種分類'] == '敬老族群']
    top_stations = seniors_df['下車站名'].value_counts().head(top_n)
    
    if top_stations.empty:
        print("警告：找不到足夠的長者下車數據來生成圖表 10。")
        return

    plt.figure(figsize=(12, 8))
    sns.barplot(x=top_stations.values, y=top_stations.index, palette='magma', orient='h', hue=top_stations.index, legend=False)
    
    plt.title(f'圖10：年度前 {top_n} 大長者熱門下車目的地', fontsize=16)
    plt.xlabel('總下車人次', fontsize=12)
    plt.ylabel('下車站名', fontsize=12)
    
    for index, value in enumerate(top_stations.values):
        plt.text(value, index, f' {value}', va='center', fontsize=10)
        
    plt.tight_layout()
    plt.savefig("10_senior_top_stations.png", dpi=300)
    plt.close()
    print("圖表 10 已儲存。")


def main():
    """
    主執行函式
    """
    setup_chinese_font()
    
    data = load_data()
    processed_data = preprocess_data(data)
    
    if processed_data is not None:
        print("\n--- 開始生成既有分析圖表 ---")
        plot_monthly_ridership(processed_data)
        plot_ticket_type_distribution(processed_data)
        plot_hourly_distribution(processed_data)
        plot_weekday_weekend_comparison(processed_data)
        plot_top_stations(processed_data, top_n=15)
        plot_top_od_pairs(processed_data, top_n=10)
        plot_weekly_ridership(processed_data)
        plot_student_commute(processed_data)
        plot_senior_commute(processed_data)
        plot_senior_top_stations(processed_data, top_n=10)
        
        print("\n所有分析圖表已成功生成！")

if __name__ == "__main__":
    main()