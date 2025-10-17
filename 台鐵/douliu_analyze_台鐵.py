import matplotlib
matplotlib.use('Agg')

import pandas as pd
import dask.dataframe as dd
# 修正：匯入正確的函式名稱
from data_loader import load_and_save_data
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import os
import sys

# --- 從 config.py 載入設定 ---
try:
    # 假設 config.py 在上層目錄
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    import config
except ImportError:
    print("錯誤：無法找到 config.py。請確認您的專案結構。")
    sys.exit(1)

# ==============================================================================
# 建立輸出資料夾
# ==============================================================================
output_csv_dir = os.path.join(config.OUTPUT_BASE_DIR, 'tra', 'csv')
output_chart_dir = os.path.join(config.OUTPUT_BASE_DIR, 'tra', 'charts')

os.makedirs(output_csv_dir, exist_ok=True)
os.makedirs(output_chart_dir, exist_ok=True)

print(f"CSV 結果將儲存至 '{output_csv_dir}/' 資料夾。")
print(f"圖表將儲存至 '{output_chart_dir}/' 資料夾。")

# ==============================================================================
# 圖表中文設定
# ==============================================================================
def setup_chinese_font():
    try:
        font_name = 'Microsoft JhengHei'
        plt.rcParams['font.sans-serif'] = [font_name]
        plt.rcParams['axes.unicode_minus'] = False
        sns.set_theme(style="whitegrid", font=font_name)
        print(f"Matplotlib 與 Seaborn 中文字體已設定為 '{font_name}'。")
    except Exception as e:
        print(f"警告：設定字體時發生錯誤: {e}")

setup_chinese_font()

# ==============================================================================
# 核心步驟：載入並準備所有資料
# ==============================================================================
# 從 config 讀取清洗後的資料檔名
# 修正：呼叫正確的函式
all_data = load_and_save_data(output_filename=config.TRA_CLEANED_DATA_FILE)

if all_data is not None:

    print("\n--- [設定分析區間：從 config.py 讀取] ---")
    # 從 config 讀取目標車站列表
    target_stations = config.TRA_TARGET_STATIONS

    all_data = all_data[
        all_data['起點'].isin(target_stations) &
        all_data['迄點'].isin(target_stations)
    ]

    print(f"已將資料範圍限定在 {len(target_stations)} 個車站內，後續將僅分析此區間的資料。")

    # ==============================================================================
    # 分析：特定車站尖峰時段分析 (從 config 讀取站名)
    # ==============================================================================
    TARGET_STATION_NAME = config.TRA_DOULIU_TARGET_STATION
    print(f"\n--- [分析：{TARGET_STATION_NAME}車站尖峰時段分析 (含平日/假日)] ---")
    print("註：此分析僅針對有提供進、出站時間的資料。")

    data_for_peak = all_data.copy()
    data_for_peak['進站時間'] = dd.to_datetime(data_for_peak['進站時間'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
    data_for_peak['出站時間'] = dd.to_datetime(data_for_peak['出站時間'], format='%Y-%m-%d %H:%M:%S', errors='coerce')

    station_data_dd = data_for_peak[
        (data_for_peak['起點'] == TARGET_STATION_NAME) | (data_for_peak['迄點'] == TARGET_STATION_NAME)
    ]
    station_data = station_data_dd.compute()
    print(f"已篩選出與 {TARGET_STATION_NAME} 站相關的資料共 {len(station_data)} 筆，開始計算...")

    # 計算上車人次
    departures = station_data[station_data['起點'] == TARGET_STATION_NAME].dropna(subset=['進站時間']).copy()
    if not departures.empty:
        minute_of_day_dep = departures['進站時間'].dt.hour * 60 + departures['進站時間'].dt.minute
        departures['時段_5分'] = (minute_of_day_dep // 5).astype(int)
        dep_pivot = departures.pivot_table(index='時段_5分', columns='日期類型', values='人次', aggfunc='sum')
        dep_pivot.columns = [f'{col}_上車' for col in dep_pivot.columns]
    else:
        dep_pivot = pd.DataFrame()

    # 計算下車人次
    arrivals = station_data[station_data['迄點'] == TARGET_STATION_NAME].dropna(subset=['出站時間']).copy()
    if not arrivals.empty:
        minute_of_day_arr = arrivals['出站時間'].dt.hour * 60 + arrivals['出站時間'].dt.minute
        arrivals['時段_5分'] = (minute_of_day_arr // 5).astype(int)
        arr_pivot = arrivals.pivot_table(index='時段_5分', columns='日期類型', values='人次', aggfunc='sum')
        arr_pivot.columns = [f'{col}_下車' for col in arr_pivot.columns]
    else:
        arr_pivot = pd.DataFrame()

    # 合併資料
    full_day_index = pd.Index(range(24 * 12), name='時段_5分')
    station_peak_df = pd.DataFrame(index=full_day_index).join(dep_pivot).join(arr_pivot).fillna(0).astype(int)

    expected_cols = ['平日_上車', '假日_上車', '平日_下車', '假日_下車']
    for col in expected_cols:
        if col not in station_peak_df.columns:
            station_peak_df[col] = 0
    station_peak_df = station_peak_df[expected_cols]

    # 顯示與儲存
    print(f"\n--- [文字報表：{TARGET_STATION_NAME}站各時段上、下車旅運量 (每5分鐘)] ---")
    def block_to_time(block):
        return f'{block * 5 // 60:02d}:{block * 5 % 60:02d}'

    display_df = station_peak_df.copy()
    display_df.index = display_df.index.map(block_to_time)
    display_df.index.name = '時間'
    print(display_df.to_string())

    output_path = os.path.join(output_csv_dir, f'analysis_{TARGET_STATION_NAME}_peak_5min.csv')
    station_peak_df.to_csv(output_path, encoding='utf-8-sig')
    print(f"\n{TARGET_STATION_NAME}站尖峰分析結果已儲存至 {output_path}")

    # 繪圖
    time_chunks = {
        "清晨 (00-06點)": (0, 6 * 12), "上午 (06-12點)": (6 * 12, 12 * 12),
        "下午 (12-18點)": (12 * 12, 18 * 12), "傍晚至午夜 (18-24點)": (18 * 12, 24 * 12)
    }

    for title, (start_block, end_block) in time_chunks.items():
        chunk_data = station_peak_df.loc[start_block : end_block-1]

        if chunk_data.empty or chunk_data.sum().sum() == 0:
            print(f"\n時間區塊 '{title}' 沒有資料，跳過繪圖。")
            continue

        chunk_data.index = chunk_data.index.map(block_to_time)
        plt.figure(figsize=(15, 8))
        plot_data = chunk_data.reset_index().melt(id_vars='時段_5分', var_name='類型', value_name='人次')
        ax = sns.lineplot(data=plot_data, x='時段_5分', y='人次', hue='類型', style='類型', markers=True, dashes=False, markersize=7, palette='tab10')
        plt.title(f'{TARGET_STATION_NAME}車站尖峰時段分析 - {title}', fontsize=18, pad=20)
        plt.xlabel('時間', fontsize=12); plt.ylabel('總人次', fontsize=12)
        ax.xaxis.set_major_locator(mticker.MultipleLocator(6))
        plt.xticks(rotation=45, ha='right')
        plt.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.legend(title='類型', bbox_to_anchor=(1.02, 1), loc='upper left')
        plt.tight_layout(rect=[0, 0, 0.9, 1])

        chart_filename = f'chart_{TARGET_STATION_NAME}_peak_{title.split(" ")[0]}.png'
        chart_path = os.path.join(output_chart_dir, chart_filename)
        plt.savefig(chart_path, dpi=300); plt.close()
        print(f"圖表已儲存至 {chart_path}")

    print("\n\n所有分析已完成！")
else:
    print("無法載入資料，分析中止。")