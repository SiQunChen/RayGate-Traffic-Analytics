import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- 全域設定 ---
# 設定 Matplotlib 使用支援中文的字體，以避免圖表中的中文顯示為亂碼
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
# 解決 Matplotlib 圖表中負號顯示問題
plt.rcParams['axes.unicode_minus'] = False

# --- 函式定義 ---

def load_data(filepath='unified_data.csv'):
    """
    從指定的 CSV 檔案路徑讀取並進行基礎的預處理。

    Args:
        filepath (str): CSV 檔案的路徑。

    Returns:
        pd.DataFrame or None: 如果成功，返回預處理後的 DataFrame；若檔案不存在，返回 None。
    """
    print(f"開始讀取資料：'{filepath}'...")
    if not os.path.exists(filepath):
        print(f"錯誤：找不到檔案 '{filepath}'。請確保檔案與此腳本在同一個資料夾中。")
        return None

    try:
        # 為了避免 DtypeWarning，明確指定部分欄位的資料型態
        df = pd.read_csv(filepath, dtype={'路線': str, '司機': str})
        
        # 將時間字串轉換為 datetime 物件，無法轉換的設為 NaT
        df['上車時間'] = pd.to_datetime(df['上車時間'], errors='coerce')
        df['下車時間'] = pd.to_datetime(df['下車時間'], errors='coerce')
        
        # 移除時間欄位為 NaT 的無效資料
        df.dropna(subset=['上車時間', '下車時間'], inplace=True)
        
        print("資料讀取與基礎預處理完成。")
        return df
    except Exception as e:
        print(f"讀取或處理檔案時發生錯誤：{e}")
        return None

def analyze_and_plot_by_time_and_day_type(df, station_name, output_folder='douliu_charts'):
    """
    分析指定車站於「平日」及「假日」在四個不同時段的上、下車尖峰，
    分別繪製圖表，並在最後輸出文字總結報告。

    Args:
        df (pd.DataFrame): 包含公車刷卡紀錄的 DataFrame。
        station_name (str): 要分析的車站名稱。
        output_folder (str): 儲存圖表的資料夾名稱。
    """
    print(f"\n開始分析車站：'{station_name}' 的時段流量...")

    # 建立儲存圖表的資料夾
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"已建立資料夾：'{output_folder}'")

    # 1. 篩選與指定車站相關的紀錄
    station_boardings_df = df[df['上車站名'] == station_name].copy()
    station_alightings_df = df[df['下車站名'] == station_name].copy()

    if station_boardings_df.empty and station_alightings_df.empty:
        print(f"警告：在資料中找不到任何與車站 '{station_name}' 相關的紀錄。")
        return

    # 2. 標記平日與假日 (星期一=0, 星期日=6)
    station_boardings_df['day_type'] = station_boardings_df['上車時間'].dt.dayofweek.apply(lambda x: '平日' if x < 5 else '假日')
    station_alightings_df['day_type'] = station_alightings_df['下車時間'].dt.dayofweek.apply(lambda x: '平日' if x < 5 else '假日')

    # 3. 計算每5分鐘一個時間區間的索引
    station_boardings_df['time_interval'] = (station_boardings_df['上車時間'].dt.hour * 12) + (station_boardings_df['上車時間'].dt.minute // 5)
    station_alightings_df['time_interval'] = (station_alightings_df['下車時間'].dt.hour * 12) + (station_alightings_df['下車時間'].dt.minute // 5)

    # 4. 按「日期類型」和「時間區間」分組，並統計人次
    boarding_counts = station_boardings_df.groupby(['day_type', 'time_interval']).size().unstack(level=0, fill_value=0)
    alighting_counts = station_alightings_df.groupby(['day_type', 'time_interval']).size().unstack(level=0, fill_value=0)

    # 5. 建立一個包含所有時間區間的 DataFrame 以便合併與繪圖
    peak_df = pd.DataFrame(index=range(288))
    peak_df['平日上車'] = peak_df.index.map(boarding_counts.get('平日', {})).fillna(0)
    peak_df['假日上車'] = peak_df.index.map(boarding_counts.get('假日', {})).fillna(0)
    peak_df['平日下車'] = peak_df.index.map(alighting_counts.get('平日', {})).fillna(0)
    peak_df['假日下車'] = peak_df.index.map(alighting_counts.get('假日', {})).fillna(0)
    
    # 6. 定義要繪製的四個時段
    time_chunks = {
        "清晨 (00:00-05:55)": (0, 6 * 12),
        "上午 (06:00-11:55)": (6 * 12, 12 * 12),
        "下午 (12:00-17:55)": (12 * 12, 18 * 12),
        "傍晚至午夜 (18:00-23:55)": (18 * 12, 24 * 12)
    }

    print("開始產生各時段的平假日流量圖...")
    # 7. 遍歷四個時段並分別繪圖
    for chunk_name, (start_interval, end_interval) in time_chunks.items():
        print(f"-> 正在繪製 '{chunk_name}' 時段圖表...")
        
        chunk_data = peak_df.loc[start_interval : end_interval - 1]

        plt.figure(figsize=(15, 8))
        sns.lineplot(data=chunk_data, dashes=False, marker='o', markersize=5)
        
        plt.title(f'{station_name} - {chunk_name} 平日與假日上下車流量分析 (每5分鐘)', fontsize=18, fontweight='bold')
        plt.xlabel('時間', fontsize=12)
        plt.ylabel('總人次', fontsize=12)

        start_hour = start_interval // 12
        end_hour = end_interval // 12
        ticks = [h * 12 for h in range(start_hour, end_hour)]
        labels = [f'{h:02d}:00' for h in range(start_hour, end_hour)]
        plt.xticks(ticks=ticks, labels=labels, rotation=45, ha="right")
        plt.xlim(start_interval, end_interval - 1)
        
        plt.grid(True, which='both', linestyle='--', alpha=0.7)
        plt.legend(title='類型')
        plt.tight_layout()

        safe_chunk_name = chunk_name.split(" ")[0]
        output_filename = os.path.join(output_folder, f'{station_name}__{safe_chunk_name}_analysis.png')
        plt.savefig(output_filename)
        plt.close()

    print(f"\n所有時段流量圖已成功產生並儲存於 '{output_folder}' 資料夾中。")

    # 8. 產生文字報告
    print(f"\n\n===== 市區公車在{station_name}的人流時段分析 =====")
    print("\n--- 各時段每5分鐘詳細流量 ---")

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
            weekday_on = int(row['平日上車'])
            weekday_off = int(row['平日下車'])
            weekend_on = int(row['假日上車'])
            weekend_off = int(row['假日下車'])
            print(f"  時間: {time_str} -> 平日(上車:{weekday_on}, 下車:{weekday_off}), 假日(上車:{weekend_on}, 下車:{weekend_off})")

    print("\n================= 分析結束 =================\n")

def plot_morning_destinations(df, station_name, output_folder='douliu_charts', top_n=15):
    """
    分析平日早上通勤時段，從指定車站上車的乘客，其主要目的地並繪製圖表。

    Args:
        df (pd.DataFrame): 包含公車刷卡紀錄的 DataFrame。
        station_name (str): 要分析的起始車站名稱。
        output_folder (str): 儲存圖表的資料夾名稱。
        top_n (int): 要顯示的目的地數量。
    """
    print(f"開始分析 '{station_name}' 的平日早上通勤目的地...")
    
    # 1. 篩選平日 (週一至週五)
    df_weekday = df[df['上車時間'].dt.dayofweek < 5].copy()
    
    # 2. 篩選早上 06:30 到 09:00 之間，且從指定車站上車的紀錄
    start_time = pd.to_datetime('06:30').time()
    end_time = pd.to_datetime('09:00').time()
    df_morning_rush = df_weekday[
        (df_weekday['上車站名'] == station_name) &
        (df_weekday['上車時間'].dt.time >= start_time) &
        (df_weekday['上車時間'].dt.time < end_time)
    ]
    
    if df_morning_rush.empty:
        print(f"在平日早上 06:30-09:00 找不到從 '{station_name}' 上車的紀錄。")
        return
        
    # 3. 統計目的地並取出前 N 名
    destination_counts = df_morning_rush['下車站名'].value_counts().nlargest(top_n)
    
    # 4. 繪製水平長條圖 (更新寫法以消除警告)
    plt.figure(figsize=(12, 8))
    sns.barplot(x=destination_counts.values, y=destination_counts.index, hue=destination_counts.index, palette='viridis', orient='h', legend=False)
    
    plt.title(f'平日早上 (06:30-09:00) {station_name}上車之主要目的地 (前{top_n}名)', fontsize=16, fontweight='bold')
    plt.xlabel('旅次數', fontsize=12)
    plt.ylabel('目的地車站', fontsize=12)
    plt.tight_layout()
    
    # 儲存圖檔
    output_filename = os.path.join(output_folder, f'{station_name}_morning_destinations.png')
    plt.savefig(output_filename)
    plt.close()
    print(f"早上通勤目的地圖表已儲存至: {output_filename}")

def plot_evening_origins(df, station_name, output_folder='douliu_charts', top_n=15):
    """
    分析平日傍晚通勤時段，抵達指定車站的乘客，其主要起始站並繪製圖表。

    Args:
        df (pd.DataFrame): 包含公車刷卡紀錄的 DataFrame。
        station_name (str): 要分析的目的地車站名稱。
        output_folder (str): 儲存圖表的資料夾名稱。
        top_n (int): 要顯示的起始站數量。
    """
    print(f"\n開始分析 '{station_name}' 的平日傍晚通勤起始站...")
    
    # 1. 篩選平日 (週一至週五)
    df_weekday = df[df['下車時間'].dt.dayofweek < 5].copy()
    
    # 2. 篩選傍晚 16:00 到 18:30 之間，且在指定車站下車的紀錄
    start_time = pd.to_datetime('16:00').time()
    end_time = pd.to_datetime('18:30').time()
    df_evening_rush = df_weekday[
        (df_weekday['下車站名'] == station_name) &
        (df_weekday['下車時間'].dt.time >= start_time) &
        (df_weekday['下車時間'].dt.time < end_time)
    ]
    
    if df_evening_rush.empty:
        print(f"在平日傍晚 16:00-18:30 找不到抵達 '{station_name}' 的紀錄。")
        return
        
    # 3. 統計起始站並取出前 N 名
    origin_counts = df_evening_rush['上車站名'].value_counts().nlargest(top_n)
    
    # 4. 繪製水平長條圖 (更新寫法以消除警告)
    plt.figure(figsize=(12, 8))
    sns.barplot(x=origin_counts.values, y=origin_counts.index, hue=origin_counts.index, palette='plasma', orient='h', legend=False)
    
    plt.title(f'平日傍晚 (16:00-18:30) 抵達{station_name}之主要起始站 (前{top_n}名)', fontsize=16, fontweight='bold')
    plt.xlabel('旅次數', fontsize=12)
    plt.ylabel('起始車站', fontsize=12)
    plt.tight_layout()
    
    # 儲存圖檔
    output_filename = os.path.join(output_folder, f'{station_name}_evening_origins.png')
    plt.savefig(output_filename)
    plt.close()
    print(f"傍晚通勤起始站圖表已儲存至: {output_filename}")


# --- 主程式執行區塊 ---
if __name__ == '__main__':
    # 讀取資料
    bus_data = load_data(filepath='unified_data.csv')

    # 如果資料成功讀取，則進行分析與繪圖
    if bus_data is not None:
        # 您可以在這裡更改要分析的車站名稱
        TARGET_STATION = '斗六火車站'
        
        # 執行原有的時段流量分析與文字報告
        analyze_and_plot_by_time_and_day_type(bus_data, station_name=TARGET_STATION)
        
        # 執行新增的通勤熱點分析
        plot_morning_destinations(bus_data, station_name=TARGET_STATION)
        plot_evening_origins(bus_data, station_name=TARGET_STATION)
