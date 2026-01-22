# 檔名: station_transfer_analyze.py
# 功能: 分析指定市區公車站點在不同時段、平假日的詳細人流狀況。
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys

# --- 從 config.py 載入設定 ---
try:
    # 假設 config.py 在上層目錄
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    import config
except ImportError:
    print("錯誤：無法找到 config.py。請確認您的專案結構。")
    sys.exit(1)

# --- 全域設定 ---
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
plt.rcParams['axes.unicode_minus'] = False

# --- 函式定義 ---

def load_data(filepath):
    """
    從指定的 CSV 檔案路徑讀取並進行基礎的預處理。
    """
    print(f"開始讀取資料：'{filepath}'...")
    if not os.path.exists(filepath):
        print(f"錯誤：找不到檔案 '{filepath}'。請檢查 config.py 中的 BUS_UNIFIED_DATA_FILE 設定。")
        return None
    try:
        df = pd.read_csv(filepath, dtype={'路線': str, '司機': str})
        df['上車時間'] = pd.to_datetime(df['上車時間'], errors='coerce')
        df['下車時間'] = pd.to_datetime(df['下車時間'], errors='coerce')
        df.dropna(subset=['上車時間', '下車時間'], inplace=True)
        print("資料讀取與基礎預處理完成。")
        return df
    except Exception as e:
        print(f"讀取或處理檔案時發生錯誤：{e}")
        return None

def analyze_and_plot_by_time_and_day_type(df, station_name, output_folder):
    """
    分析指定車站於「平日」及「假日」在四個不同時段的上、下車尖峰。
    """
    print(f"\n開始分析車站：'{station_name}' 的時段流量...")
    os.makedirs(output_folder, exist_ok=True)
    print(f"圖表將儲存於：'{output_folder}'")

    station_boardings_df = df[df['上車站名'] == station_name].copy()
    station_alightings_df = df[df['下車站名'] == station_name].copy()

    if station_boardings_df.empty and station_alightings_df.empty:
        print(f"警告：在資料中找不到任何與車站 '{station_name}' 相關的紀錄。")
        return

    station_boardings_df['day_type'] = station_boardings_df['上車時間'].dt.dayofweek.apply(lambda x: '平日' if x < 5 else '假日')
    station_alightings_df['day_type'] = station_alightings_df['下車時間'].dt.dayofweek.apply(lambda x: '平日' if x < 5 else '假日')
    station_boardings_df['time_interval'] = (station_boardings_df['上車時間'].dt.hour * 12) + (station_boardings_df['上車時間'].dt.minute // 5)
    station_alightings_df['time_interval'] = (station_alightings_df['下車時間'].dt.hour * 12) + (station_alightings_df['下車時間'].dt.minute // 5)

    boarding_counts = station_boardings_df.groupby(['day_type', 'time_interval']).size().unstack(level=0, fill_value=0)
    alighting_counts = station_alightings_df.groupby(['day_type', 'time_interval']).size().unstack(level=0, fill_value=0)

    peak_df = pd.DataFrame(index=range(288))
    peak_df['平日上車'] = peak_df.index.map(boarding_counts.get('平日', {})).fillna(0)
    peak_df['假日上車'] = peak_df.index.map(boarding_counts.get('假日', {})).fillna(0)
    peak_df['平日下車'] = peak_df.index.map(alighting_counts.get('平日', {})).fillna(0)
    peak_df['假日下車'] = peak_df.index.map(alighting_counts.get('假日', {})).fillna(0)
    
    time_chunks = {
        "清晨 (00:00-05:55)": (0, 6 * 12), "上午 (06:00-11:55)": (6 * 12, 12 * 12),
        "下午 (12:00-17:55)": (12 * 12, 18 * 12), "傍晚至午夜 (18:00-23:55)": (18 * 12, 24 * 12)
    }

    print("開始產生各時段的平假日流量圖...")
    for chunk_name, (start_interval, end_interval) in time_chunks.items():
        print(f"-> 正在繪製 '{chunk_name}' 時段圖表...")
        chunk_data = peak_df.loc[start_interval : end_interval - 1]
        plt.figure(figsize=(15, 8)); sns.lineplot(data=chunk_data, dashes=False, marker='o', markersize=5)
        plt.title(f'{station_name} - {chunk_name} 平日與假日上下車流量分析 (每5分鐘)', fontsize=18, fontweight='bold')
        plt.xlabel('時間', fontsize=12); plt.ylabel('總人次', fontsize=12)
        start_hour, end_hour = start_interval // 12, end_interval // 12
        ticks = [h * 12 for h in range(start_hour, end_hour)]
        labels = [f'{h:02d}:00' for h in range(start_hour, end_hour)]
        plt.xticks(ticks=ticks, labels=labels, rotation=45, ha="right")
        plt.xlim(start_interval, end_interval - 1)
        plt.grid(True, which='both', linestyle='--', alpha=0.7); plt.legend(title='類型'); plt.tight_layout()
        safe_chunk_name = chunk_name.split(" ")[0]
        output_filename = os.path.join(output_folder, f'bus_transfer_{station_name}_{safe_chunk_name}.png')
        plt.savefig(output_filename); plt.close()

    print(f"\n所有時段流量圖已成功產生並儲存於 '{output_folder}' 資料夾中。")

    print(f"\n\n===== 市區公車在 {station_name} 的人流時段分析報告 =====")
    for chunk_name, (start_interval, end_interval) in time_chunks.items():
        print(f"\n時段: {chunk_name}")
        chunk_data = peak_df.loc[start_interval : end_interval - 1]
        active_times = chunk_data[chunk_data.sum(axis=1) > 0]
        if active_times.empty:
            print("  此時段無搭乘紀錄。")
            continue
        for idx, row in active_times.iterrows():
            hour = idx // 12
            minute = (idx % 12) * 5
            time_str = f'{hour:02d}:{minute:02d}'
            print(f"  時間: {time_str} -> 平日(上車:{int(row['平日上車'])}, 下車:{int(row['平日下車'])}), 假日(上車:{int(row['假日上車'])}, 下車:{int(row['假日下車'])})")
    print("\n================= 分析結束 =================\n")
    
def plot_morning_destinations(df, station_name, output_folder, top_n=15):
    print(f"開始分析 '{station_name}' 的平日早上通勤目的地...")
    df_weekday = df[df['上車時間'].dt.dayofweek < 5].copy()
    start_time, end_time = pd.to_datetime('06:30').time(), pd.to_datetime('09:00').time()
    df_morning_rush = df_weekday[(df_weekday['上車站名'] == station_name) & (df_weekday['上車時間'].dt.time >= start_time) & (df_weekday['上車時間'].dt.time < end_time)]
    if df_morning_rush.empty:
        print(f"在平日早上 06:30-09:00 找不到從 '{station_name}' 上車的紀錄。")
        return
    destination_counts = df_morning_rush['下車站名'].value_counts().nlargest(top_n)
    plt.figure(figsize=(12, 8)); sns.barplot(x=destination_counts.values, y=destination_counts.index, hue=destination_counts.index, palette='viridis', orient='h', legend=False)
    plt.title(f'平日早上 (06:30-09:00) 從 {station_name} 上車之主要目的地 (前{top_n}名)', fontsize=16, fontweight='bold')
    plt.xlabel('旅次數', fontsize=12); plt.ylabel('目的地車站', fontsize=12); plt.tight_layout()
    output_filename = os.path.join(output_folder, f'bus_transfer_{station_name}_morning_dest.png')
    plt.savefig(output_filename); plt.close()
    print(f"早上通勤目的地圖表已儲存至: {output_filename}")

def plot_evening_origins(df, station_name, output_folder, top_n=15):
    print(f"\n開始分析 '{station_name}' 的平日傍晚通勤起始站...")
    df_weekday = df[df['下車時間'].dt.dayofweek < 5].copy()
    start_time, end_time = pd.to_datetime('16:00').time(), pd.to_datetime('18:30').time()
    df_evening_rush = df_weekday[(df_weekday['下車站名'] == station_name) & (df_weekday['下車時間'].dt.time >= start_time) & (df_weekday['下車時間'].dt.time < end_time)]
    if df_evening_rush.empty:
        print(f"在平日傍晚 16:00-18:30 找不到抵達 '{station_name}' 的紀錄。")
        return
    origin_counts = df_evening_rush['上車站名'].value_counts().nlargest(top_n)
    plt.figure(figsize=(12, 8)); sns.barplot(x=origin_counts.values, y=origin_counts.index, hue=origin_counts.index, palette='plasma', orient='h', legend=False)
    plt.title(f'平日傍晚 (16:00-18:30) 抵達 {station_name} 之主要起始站 (前{top_n}名)', fontsize=16, fontweight='bold')
    plt.xlabel('旅次數', fontsize=12); plt.ylabel('起始車站', fontsize=12); plt.tight_layout()
    output_filename = os.path.join(output_folder, f'bus_transfer_{station_name}_evening_org.png')
    plt.savefig(output_filename); plt.close()
    print(f"傍晚通勤起始站圖表已儲存至: {output_filename}")


# --- 主程式執行區塊 ---
if __name__ == '__main__':
    TARGET_STATION = config.BUS_TRANSFER_STATION

    if not TARGET_STATION:
        print("設定檔 (config.py) 中未指定市區公車轉乘分析車站 (BUS_TRANSFER_STATION)。")
        print("將跳過此分析腳本。")
        sys.exit(0)

    data_file = config.BUS_UNIFIED_DATA_FILE
    bus_data = load_data(filepath=data_file)

    if bus_data is not None:
        # 從 code/市區公車/ 需要往上兩層才能到專案根目錄
        OUTPUT_FOLDER = os.path.join('..', '..', config.TRANSFER_ANALYSIS_OUTPUT_DIR, '市區公車')
        
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)

        analyze_and_plot_by_time_and_day_type(bus_data, station_name=TARGET_STATION, output_folder=OUTPUT_FOLDER)
        plot_morning_destinations(bus_data, station_name=TARGET_STATION, output_folder=OUTPUT_FOLDER)
        plot_evening_origins(bus_data, station_name=TARGET_STATION, output_folder=OUTPUT_FOLDER)