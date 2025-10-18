# 檔名: code/公路客運/main_analyze_公路客運.py
# 功能: 對已整合清理過的「公路客運」資料進行全面的視覺化分析。
# 說明: 此腳本的結構與分析項目完全比照 main_analyze_市區公車.py，
#       以確保分析流程的一致性。

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys

# --- 從 config.py 載入設定 ---
try:
    # 從 code/公路客運/ 回到專案根目錄
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    import config
except ImportError:
    print("錯誤：無法找到 config.py。請確認您的專案結構。")
    sys.exit(1)


# --- 全域設定 ---
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
plt.rcParams['axes.unicode_minus'] = False

# *** 核心修改 1: 使用公路客運的輸出資料夾 ***
# 從 config.py 讀取路徑，並在底下建立一個 'main_analysis' 子資料夾來存放圖表
output_folder = os.path.join('..', '..', config.HIGHWAY_BUS_OUTPUT_DIR, 'main_analysis')
if not os.path.exists(output_folder):
    os.makedirs(output_folder)
    print(f"已建立資料夾: {output_folder}")

# --- 1. 資料讀取與預處理 ---
def load_and_preprocess_data(filepath=config.HIGHWAY_BUS_UNIFIED_DATA_FILE):
    """
    讀取由 data_loader_公路客運.py 產生的統一化資料。
    """
    print("開始讀取已預處理的公路客運資料...")
    try:
        # *** 核心修改 2: 讀取公路客運的資料檔案 ***
        # 增加 low_memory=False 參數以處理混合型別的警告
        df = pd.read_csv(filepath, dtype={'路線': str}, low_memory=False)
    except FileNotFoundError:
        print(f"錯誤：找不到檔案 '{filepath}'。請確保已先執行 data_loader_公路客運.py。")
        return None

    # 將時間相關欄位轉換為 datetime 物件
    df['上車時間'] = pd.to_datetime(df['上車時間'], errors='coerce')
    df['下車時間'] = pd.to_datetime(df['下車時間'], errors='coerce')

    # 移除時間格式轉換後可能產生的無效資料
    df.dropna(subset=['上車時間'], inplace=True)

    print("資料讀取完成。")
    return df

# --- 2. 繪圖函式 (邏輯與市區公車完全相同，僅微調圖表標題) ---

def plot_monthly_ridership(df):
    print("正在產生圖表：每月總運量分析...")
    monthly_counts = df['上車月份'].value_counts().sort_index()

    print("\n--- 1. 每月總運量分析結果 ---")
    print(monthly_counts)
    print("---------------------------------\n")

    plt.figure(figsize=(12, 7))
    sns.barplot(x=monthly_counts.index, y=monthly_counts.values, palette='viridis', hue=monthly_counts.index, legend=False)
    plt.title('公路客運 每月總運量分析', fontsize=18, fontweight='bold')
    plt.xlabel('月份', fontsize=12)
    plt.ylabel('總搭乘人次', fontsize=12)
    # 動態生成月份標籤，確保與資料匹配
    plt.xticks(ticks=range(len(monthly_counts)), labels=[f'{int(i)}月' for i in monthly_counts.index])
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, '1_每月總運量分析.png'))
    plt.close()

def plot_weekly_ridership(df):
    print("正在產生圖表：週間總運量分析...")
    weekly_counts = df['上車星期'].value_counts().sort_index()
    # *** 錯誤修正：不再寫死 day_names，而是根據實際資料動態產生標籤 ***
    day_map = {0: '星期一', 1: '星期二', 2: '星期三', 3: '星期四', 4: '星期五', 5: '星期六', 6: '星期日'}
    dynamic_day_names = [day_map[i] for i in weekly_counts.index]

    print("\n--- 2. 週間總運量分析結果 ---")
    weekly_counts_display = weekly_counts.copy()
    weekly_counts_display.index = dynamic_day_names # 使用動態產生的標籤
    print(weekly_counts_display)
    print("---------------------------------\n")

    plt.figure(figsize=(12, 7))
    sns.barplot(x=weekly_counts.index, y=weekly_counts.values, palette='plasma', hue=weekly_counts.index, legend=False)
    plt.title('公路客運 週間總運量分析', fontsize=18, fontweight='bold')
    plt.xlabel('星期', fontsize=12)
    plt.ylabel('總搭乘人次', fontsize=12)
    # *** 錯誤修正：使用動態標籤來設定X軸刻度 ***
    plt.xticks(ticks=range(len(weekly_counts)), labels=dynamic_day_names, rotation=45)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, '2_週間總運量分析.png'))
    plt.close()

def plot_top_routes(df, n=15):
    print(f"正在產生圖表：前 {n} 名路線運量排名...")
    route_counts = df['路線'].value_counts().nlargest(n)

    print(f"\n--- 3. 前 {n} 名路線運量排名結果 ---")
    print(route_counts)
    print("----------------------------------\n")

    plt.figure(figsize=(12, 9))
    sns.barplot(y=route_counts.index, x=route_counts.values, orient='h', palette='magma', hue=route_counts.index, legend=False)
    plt.title(f'公路客運 前 {n} 名路線運量排名', fontsize=18, fontweight='bold')
    plt.xlabel('總搭乘人次', fontsize=12)
    plt.ylabel('路線編號', fontsize=12)
    for index, value in enumerate(route_counts.values):
        plt.text(value, index, f' {value:,}', va='center')
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, '3_路線運量排名.png'))
    plt.close()

def plot_passenger_distribution(df):
    print("正在產生圖表：乘客身分結構分析...")
    passenger_counts = df['持卡身分'].value_counts()
    passenger_percentages = df['持卡身分'].value_counts(normalize=True) * 100

    print("\n--- 4. 乘客身分結構分析結果 ---")
    result_df = pd.DataFrame({
        '搭乘人次': passenger_counts,
        '佔比 (%)': passenger_percentages.round(2)
    })
    print(result_df)
    print("----------------------------------\n")

    plt.figure(figsize=(10, 10))
    colors = sns.color_palette('pastel')[0:len(passenger_counts)]
    plt.pie(passenger_counts, labels=passenger_counts.index, autopct='%1.1f%%', startangle=140, colors=colors, textprops={'fontsize': 14})
    plt.title('公路客運 乘客身分結構分析', fontsize=18, fontweight='bold')
    plt.ylabel('')
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, '4_乘客身分結構分析.png'))
    plt.close()

def plot_avg_trip_duration(df, n=15):
    print(f"正在產生圖表：前 {n} 名平均旅次時間最長路線...")
    valid_duration_df = df[df['旅次時長(分)'] <= 180] # 篩選掉可能的異常值 (例如 > 3 小時)
    avg_duration = valid_duration_df.groupby('路線')['旅次時長(分)'].mean().nlargest(n).sort_values(ascending=False)

    print(f"\n--- 5. 前 {n} 名平均旅次時間最長路線結果 ---")
    print(avg_duration.round(2))
    print("------------------------------------------\n")

    plt.figure(figsize=(12, 9))
    sorted_avg_duration = avg_duration.sort_values()
    sns.barplot(y=sorted_avg_duration.index, x=sorted_avg_duration.values, orient='h', palette='coolwarm', hue=sorted_avg_duration.index, legend=False)
    plt.title(f'公路客運 各路線平均旅次時間（前 {n} 名）', fontsize=18, fontweight='bold')
    plt.xlabel('平均旅次時間（分鐘）', fontsize=12)
    plt.ylabel('路線編號', fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, '5_各路線平均旅次時間.png'))
    plt.close()

def plot_hourly_ridership(df):
    print("正在產生圖表：平日與假日每小時運量比較...")
    hourly_counts = df.groupby(['上車小時', '日期類型']).size().unstack(fill_value=0)

    print("\n--- 6. 平日與假日每小時運量比較結果 ---")
    print(hourly_counts)
    print("----------------------------------------\n")

    plt.figure(figsize=(15, 8))
    hourly_counts.plot(kind='line', marker='o', ax=plt.gca())
    plt.title('公路客運 平日與假日每小時運量比較', fontsize=18, fontweight='bold')
    plt.xlabel('小時', fontsize=12)
    plt.ylabel('平均搭乘人次', fontsize=12)
    plt.xticks(ticks=range(24), labels=[f'{i}:00' for i in range(24)], rotation=45)
    plt.grid(True, which='both', linestyle='--', alpha=0.7)
    plt.legend(title='時段')
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, '6_平假日每小時運量比較.png'))
    plt.close()

def plot_top_stations(df, n=15):
    print(f"正在產生圖表：前 {n} 名最繁忙站點排名...")
    boardings = df['上車站名'].value_counts()
    alightings = df['下車站名'].value_counts()
    total_activity = boardings.add(alightings, fill_value=0).sort_values(ascending=False).nlargest(n)

    print(f"\n--- 7. 前 {n} 名最繁忙站點排名結果 ---")
    print(total_activity)
    print("------------------------------------\n")

    plt.figure(figsize=(12, 10))
    sns.barplot(y=total_activity.index, x=total_activity.values, orient='h', palette='rocket', hue=total_activity.index, legend=False)
    plt.title(f'公路客運 前 {n} 名最繁忙站點（上下車總人次）', fontsize=18, fontweight='bold')
    plt.xlabel('總活動人次（上車+下車）', fontsize=12)
    plt.ylabel('站點名稱', fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, '7_最繁忙站點排名.png'))
    plt.close()

def plot_top_od_pairs(df, n=15):
    print(f"正在產生圖表：前 {n} 名主要交通廊帶...")
    complete_trips_df = df[df['旅次是否完整'] == True]
    od_counts = complete_trips_df.groupby(['上車站名', '下車站名']).size().nlargest(n)

    print(f"\n--- 8. 前 {n} 名主要交通廊帶結果 ---")
    print(od_counts)
    print("------------------------------------\n")

    plt.figure(figsize=(12, 10))
    od_labels = [f"{start} → {end}" for start, end in od_counts.index]
    sns.barplot(y=od_labels, x=od_counts.values, orient='h', palette='crest', hue=od_labels, legend=False)
    plt.title(f'公路客運 前 {n} 名主要交通廊帶（起訖點分析）', fontsize=18, fontweight='bold')
    plt.xlabel('總旅次數', fontsize=12)
    plt.ylabel('起訖點', fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, '8_主要交通廊帶分析.png'))
    plt.close()

# --- 3. 主程式執行區塊 ---
if __name__ == '__main__':
    # 變數名稱改為 highway_bus_data 以符合情境
    highway_bus_data = load_and_preprocess_data()

    if highway_bus_data is not None:
        print("\n==============================================")
        print("       開始輸出公路客運各項分析結果       ")
        print("==============================================\n")

        plot_monthly_ridership(highway_bus_data)
        plot_weekly_ridership(highway_bus_data)
        plot_top_routes(highway_bus_data)
        plot_passenger_distribution(highway_bus_data)
        plot_avg_trip_duration(highway_bus_data)
        plot_hourly_ridership(highway_bus_data)
        plot_top_stations(highway_bus_data)
        plot_top_od_pairs(highway_bus_data)

        # 註：公路客運資料較不具備學生/長者通勤的典型模式，
        # 因此暫時移除 plot_student_pattern_per_route 和
        # plot_elderly_pattern_and_destinations 這兩項分析。
        # 如果未來需要，也可以隨時加回來。

        print("\n所有公路客運分析圖表已成功產生並儲存於 '{}' 資料夾中。".format(output_folder))