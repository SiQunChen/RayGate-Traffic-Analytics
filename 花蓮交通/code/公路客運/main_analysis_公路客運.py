# 檔名: main_analysis_公路客運.py (V1 - 整合新版CSV資料)
# -*- coding: utf-8 -*-
"""
公路客運 113年度營運數據分析與視覺化 (整合電子票證與非電子票證資料)

本程式會讀取 config.py 中設定的兩個公路客運 CSV 檔案，
整合其數據，進行數據清洗與分析，並根據分析結果生成一系列圖表，
以視覺化方式呈現客運的營運狀況。
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys
from matplotlib.font_manager import fontManager

# --- 從 config.py 載入設定 ---
try:
    # 假設 config.py 在上兩層目錄
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    import config
except ImportError:
    print("錯誤：無法找到 config.py。請確認您的專案結構。")
    sys.exit(1)

def setup_chinese_font():
    """
    設定 Matplotlib 以正確顯示中文。
    """
    font_list = ['Microsoft JhengHei', 'PingFang TC', 'Heiti TC', 'LiHei Pro', 'Noto Sans CJK TC']
    for font_name in font_list:
        if any(font.name == font_name for font in fontManager.ttflist):
            plt.rcParams['font.sans-serif'] = [font_name]
            plt.rcParams['axes.unicode_minus'] = False
            print(f"成功設定中文字型為: {font_name}")
            return
    print("警告：未找到建議的中文字型，圖表中的中文可能無法正常顯示。")
    plt.rcParams['axes.unicode_minus'] = False

def load_and_unify_data(ic_file_path, non_ic_file_path):
    """
    讀取並整合電子票證與非電子票證的 CSV 檔案。
    """
    print("步驟 1: 開始讀取並整合公路客運資料...")
    nrows_to_read = config.TEST_MODE_ROWS if config.TEST_MODE else None
    if config.TEST_MODE:
        print(f"--- [測試模式已啟用] ---")
        print(f"所有 CSV 檔案將只讀取前 {nrows_to_read} 行。")
        print("--------------------------\n")

    all_dfs = []

    # 讀取電子票證資料
    try:
        df_ic = pd.read_csv(ic_file_path, skiprows=[1], header=0, nrows=nrows_to_read, low_memory=False)
        # 欄位對應
        ic_cols = {
            '搭乘路線名稱': '路線',
            '刷卡上車時間': '上車時間',
            '刷卡下車時間': '下車時間',
            '上車站牌名稱': '上車站名',
            '下車站牌名稱': '下車站名',
            '持卡身分': '卡別名稱',
            '業者編號': '業者編號'
        }
        df_ic_renamed = df_ic[list(ic_cols.keys())].rename(columns=ic_cols)
        all_dfs.append(df_ic_renamed)
        print(f"  - 已成功讀取電子票證資料: {os.path.basename(ic_file_path)}")
    except FileNotFoundError:
        print(f"警告：找不到檔案 '{ic_file_path}'，將跳過。")
    except Exception as e:
        print(f"讀取檔案 {os.path.basename(ic_file_path)} 時發生錯誤: {e}")

    # 讀取非電子票證資料
    try:
        df_non_ic = pd.read_csv(non_ic_file_path, skiprows=[1], header=0, nrows=nrows_to_read, low_memory=False)
        # 欄位對應
        non_ic_cols = {
            '搭乘路線名稱': '路線',
            '乘車日期': '日期',
            '乘車時間': '時間',
            '站牌或站位': '上車站名', # 非電子票證只有單一站牌資訊，在此統一為上車站
            '票種類型': '卡別名稱',
            '業者編號': '業者編號'
        }
        df_non_ic_renamed = df_non_ic[list(non_ic_cols.keys())].rename(columns=non_ic_cols)
        # 組合日期與時間
        df_non_ic_renamed['上車時間'] = pd.to_datetime(df_non_ic_renamed['日期'] + ' ' + df_non_ic_renamed['時間'], errors='coerce')
        df_non_ic_renamed.drop(columns=['日期', '時間'], inplace=True)
        # 補上下車相關欄位
        df_non_ic_renamed['下車時間'] = pd.NaT
        df_non_ic_renamed['下車站名'] = '未知'
        all_dfs.append(df_non_ic_renamed)
        print(f"  - 已成功讀取非電子票證資料: {os.path.basename(non_ic_file_path)}")
    except FileNotFoundError:
        print(f"警告：找不到檔案 '{non_ic_file_path}'，將跳過。")
    except Exception as e:
        print(f"讀取檔案 {os.path.basename(non_ic_file_path)} 時發生錯誤: {e}")

    if not all_dfs:
        print("錯誤：未能成功讀取任何有效的 CSV 檔案。")
        return None

    full_df = pd.concat(all_dfs, ignore_index=True)
    print(f"資料整合完成，共 {len(full_df)} 筆乘車紀錄。")
    return full_df

def classify_ticket(name):
    """
    根據卡別名稱進行分類的輔助函式。
    (此處的分類邏輯可能需要根據新資料的實際值進行微調)
    """
    name_str = str(name).lower() # 轉換成小寫以利比對
    if 'student' in name_str or '學生' in name_str:
        return '學生族群'
    elif 'senior' in name_str or '敬老' in name_str:
        return '敬老族群'
    elif 'disabled' in name_str or '愛心' in name_str or '博愛' in name_str:
        return '關懷族群'
    elif 'adult' in name_str or '一般' in name_str or '全票' in name_str:
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
    full_df['上車時間'] = pd.to_datetime(full_df['上車時間'], errors='coerce')
    full_df['下車時間'] = pd.to_datetime(full_df['下車時間'], errors='coerce')

    # 清理站名
    for col in ['上車站名', '下車站名']:
        if col in full_df.columns and pd.api.types.is_object_dtype(full_df[col]):
            full_df[col] = full_df[col].str.strip()

    # 移除關鍵空值
    initial_rows = len(full_df)
    full_df.dropna(subset=['上車時間', '上車站名', '路線'], inplace=True)
    if len(full_df) < initial_rows:
        print(f"移除了 {initial_rows - len(full_df)} 筆關鍵欄位為空的記錄。")

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

# --- (以下所有繪圖函式 plot_... 與舊版大致相同，僅修改標題與細節) ---
def plot_monthly_ridership(df, output_dir):
    print("正在生成圖表 1: 各月份旅運量分析...")
    monthly_counts = df.groupby('月份').size()
    plt.figure(figsize=(14, 8))
    sns.barplot(x=monthly_counts.index, y=monthly_counts.values, palette='viridis', hue=monthly_counts.index, legend=False)
    plt.title('圖1：113年度公路客運各月份旅運量分析', fontsize=16)
    plt.xlabel('月份', fontsize=12); plt.ylabel('總人次', fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "1_monthly_ridership.png"), dpi=300)
    plt.close()
    print("圖表 1 已儲存。")

def plot_ticket_type_distribution(df, output_dir):
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
    plt.axis('equal'); plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "2_ticket_type_distribution.png"), dpi=300)
    plt.close()
    print("圖表 2 已儲存。")

def plot_hourly_distribution(df, output_dir):
    print("正在生成圖表 3: 全日各時段旅次分佈...")
    hourly_counts = df['小時'].value_counts().sort_index()
    plt.figure(figsize=(14, 7)); sns.barplot(x=hourly_counts.index, y=hourly_counts.values, palette='plasma', hue=hourly_counts.index, legend=False)
    plt.title('圖3：全日各時段旅次分佈 (0-23時)', fontsize=16)
    plt.xlabel('小時', fontsize=12); plt.ylabel('總人次', fontsize=12)
    plt.xticks(range(0, 24)); plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "3_hourly_distribution.png"), dpi=300)
    plt.close()
    print("圖表 3 已儲存。")

def plot_weekday_weekend_comparison(df, output_dir):
    print("正在生成圖表 4: 平假日旅次模式比較...")
    comparison_counts = df.groupby(['日期類型', '小時']).size().unstack(fill_value=0).T.reindex(range(24), fill_value=0)
    plt.figure(figsize=(14, 8))
    plt.plot(comparison_counts.index, comparison_counts.get('平日', pd.Series(0, index=comparison_counts.index)), marker='o', linestyle='-', label='平日 (週一至五)')
    plt.plot(comparison_counts.index, comparison_counts.get('假日', pd.Series(0, index=comparison_counts.index)), marker='s', linestyle='--', label='假日 (週六、日)')
    plt.title('圖4：平假日各時段旅次模式比較', fontsize=16)
    plt.xlabel('小時', fontsize=12); plt.ylabel('總人次', fontsize=12)
    plt.xticks(range(0, 24)); plt.grid(True, which='both', linestyle='--', linewidth=0.5); plt.legend(fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "4_weekday_weekend_comparison.png"), dpi=300)
    plt.close()
    print("圖表 4 已儲存。")

def plot_top_stations(df, output_dir, top_n=15):
    print(f"正在生成圖表 5: 前 {top_n} 大熱門站點分析...")
    on_counts = df['上車站名'].value_counts()
    off_counts = df['下車站名'].value_counts()
    total_counts = on_counts.add(off_counts, fill_value=0).sort_values(ascending=False).head(top_n)
    plt.figure(figsize=(12, 10)); sns.barplot(x=total_counts.values, y=total_counts.index, palette='viridis', orient='h', hue=total_counts.index, legend=False)
    plt.title(f'圖5：年度前 {top_n} 大熱門站點 (總上下車人次)', fontsize=16)
    plt.xlabel('總上下車人次', fontsize=12); plt.ylabel('站點名稱', fontsize=12)
    for index, value in enumerate(total_counts.values):
        plt.text(value, index, f' {value:.0f}', va='center', fontsize=10)
    plt.tight_layout(); plt.savefig(os.path.join(output_dir, "5_top_stations.png"), dpi=300)
    plt.close()
    print("圖表 5 已儲存。")

def plot_top_od_pairs(df, output_dir, top_n=10):
    print(f"正在生成圖表 6: 前 {top_n} 大旅運OD走廊分析...")
    od_df = df.dropna(subset=['上車站名', '下車站名']).copy()
    od_df['OD_Pair'] = od_df['上車站名'].astype(str) + ' → ' + od_df['下車站名'].astype(str)
    # 排除 '未知' 的下車站
    od_df = od_df[od_df['下車站名'] != '未知']
    od_counts = od_df['OD_Pair'].value_counts().head(top_n)
    if od_counts.empty:
        print("警告：找不到足夠的OD資料來生成圖表 6。")
        return
    plt.figure(figsize=(12, 8)); sns.barplot(x=od_counts.values, y=od_counts.index, palette='rocket', orient='h', hue=od_counts.index, legend=False)
    plt.title(f'圖6：年度前 {top_n} 大旅運OD走廊', fontsize=16)
    plt.xlabel('總人次', fontsize=12); plt.ylabel('起訖點 (OD)', fontsize=12)
    for index, value in enumerate(od_counts.values):
        plt.text(value, index, f' {value}', va='center', fontsize=10)
    plt.tight_layout(); plt.savefig(os.path.join(output_dir, "6_top_od_pairs.png"), dpi=300)
    plt.close()
    print("圖表 6 已儲存。")

def main():
    """
    主執行函式
    """
    setup_chinese_font()
    
    output_dir = os.path.join('..', '..', config.HIGHWAY_BUS_OUTPUT_DIR, '綜合分析')
    os.makedirs(output_dir, exist_ok=True)
    print(f"所有圖表將儲存至: {os.path.abspath(output_dir)}")
    
    data = load_and_unify_data(
        ic_file_path=config.HIGHWAY_BUS_IC_FILE,
        non_ic_file_path=config.HIGHWAY_BUS_NON_IC_FILE
    )
    processed_data = preprocess_data(data)
    
    if processed_data is not None:
        print("\n--- 開始生成分析圖表 ---")
        plot_monthly_ridership(processed_data, output_dir)
        plot_ticket_type_distribution(processed_data, output_dir)
        plot_hourly_distribution(processed_data, output_dir)
        plot_weekday_weekend_comparison(processed_data, output_dir)
        plot_top_stations(processed_data, output_dir, top_n=15)
        plot_top_od_pairs(processed_data, output_dir, top_n=10)
        
        print("\n所有分析圖表已成功生成！")

if __name__ == "__main__":
    main()