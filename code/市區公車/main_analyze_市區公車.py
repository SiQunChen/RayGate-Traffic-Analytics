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

# 使用 config.py 中定義的輸出資料夾
output_folder = os.path.join('..', '..', config.BUS_OUTPUT_DIR, 'main_analysis')
if not os.path.exists(output_folder):
    os.makedirs(output_folder)
    print(f"已建立資料夾: {output_folder}")

# --- 1. 資料讀取與預處理 ---
def load_and_preprocess_data(filepath=config.BUS_UNIFIED_DATA_FILE):
    print("開始讀取與預處理資料...")
    try:
        # 【修正DtypeWarning】: 明確指定 路線 和 司機 欄位的資料型態為字串(str)
        df = pd.read_csv(filepath, dtype={'路線': str, '司機': str})
    except FileNotFoundError:
        print(f"錯誤：找不到檔案 '{filepath}'。請確保檔案與此腳本在同一個資料夾中。")
        return None

    df['上車時間'] = pd.to_datetime(df['上車時間'], errors='coerce')
    df['下車時間'] = pd.to_datetime(df['下車時間'], errors='coerce')
    df.dropna(subset=['上車時間', '下車時間'], inplace=True)
    df['上車月份'] = df['上車時間'].dt.month
    df['上車星期'] = df['上車時間'].dt.dayofweek
    df['上車小時'] = df['上車時間'].dt.hour
    df['平日/週末'] = df['上車星期'].apply(lambda x: '週末' if x >= 5 else '平日')
    complete_trips = df['旅次是否完整'] == True
    df.loc[complete_trips, '旅次時間_分'] = (df.loc[complete_trips, '下車時間'] - df.loc[complete_trips, '上車時間']).dt.total_seconds() / 60

    def unify_ticket_type(ticket_name):
        """
        根據關鍵字，將票種名稱統一分類。
        """
        ticket_name_str = str(ticket_name).strip()

        # 關鍵字分類字典
        ticket_keywords = {
            '代幣卡': ['代幣', '代'],
            '優待': ['敬老', '愛心', '陪伴', '博愛', '孩童', '優待', '兒童', '優惠', '國小', '新北學生卡', '雲林小', '半票'],
            '學生': ['學生', '學童', '大學', '學'],
            '普通': ['一般', '普通', '全票', '市民', '普卡'],
            '定期票': ['199', '399']
        }

        # 依序檢查關鍵字
        if any(keyword in ticket_name_str for keyword in ticket_keywords['代幣卡']):
            return '代幣卡'
        if any(keyword in ticket_name_str for keyword in ticket_keywords['優待']):
            return '優待'
        if any(keyword in ticket_name_str for keyword in ticket_keywords['學生']):
            return '學生'
        if any(keyword in ticket_name_str for keyword in ticket_keywords['普通']):
            return '普通'
        if any(keyword in ticket_name_str for keyword in ticket_keywords['定期票']):
            return '定期票'

        return '其他'

    df['票種分類'] = df['票種名稱'].apply(unify_ticket_type)
    print("資料預處理完成。")
    return df

# --- 2. 繪圖函式 ---

def plot_monthly_ridership(df):
    print("正在產生圖表：每月總運量分析...")
    monthly_counts = df['上車月份'].value_counts().sort_index()

    # 【新增】印出分析結果
    print("\n--- 1. 每月總運量分析結果 ---")
    print(monthly_counts)
    print("---------------------------------\n")

    plt.figure(figsize=(12, 7))
    sns.barplot(x=monthly_counts.index, y=monthly_counts.values, palette='viridis', hue=monthly_counts.index, legend=False)
    plt.title('每月總運量分析', fontsize=18, fontweight='bold')
    plt.xlabel('月份', fontsize=12)
    plt.ylabel('總搭乘人次', fontsize=12)
    plt.xticks(ticks=range(len(monthly_counts)), labels=[f'{i}月' for i in monthly_counts.index])
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, '1_每月總運量分析.png'))
    plt.close()

def plot_weekly_ridership(df):
    print("正在產生圖表：週間總運量分析...")
    
    # *** 【核心修改】 ***
    # 使用 .reindex(range(7), fill_value=0) 確保 Series 總是包含 7 天 (0=週一 到 6=週日)
    # 即使某些天沒有數據，也會以 0 填充。
    weekly_counts = df['上車星期'].value_counts().reindex(range(7), fill_value=0)
    day_names = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']

    # 【新增】印出分析結果
    print("\n--- 2. 週間總運量分析結果 ---")
    # 建立一個新的 Series 以便顯示中文星期
    weekly_counts_display = weekly_counts.copy()
    weekly_counts_display.index = day_names # 現在這裡不會再報錯了
    print(weekly_counts_display)
    print("---------------------------------\n")
    
    plt.figure(figsize=(12, 7))
    sns.barplot(x=weekly_counts.index, y=weekly_counts.values, palette='plasma', hue=weekly_counts.index, legend=False)
    plt.title('週間總運量分析', fontsize=18, fontweight='bold')
    plt.xlabel('星期', fontsize=12)
    plt.ylabel('總搭乘人次', fontsize=12)
    plt.xticks(ticks=range(7), labels=day_names, rotation=45)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, '2_週間總運量分析.png'))
    plt.close()

def plot_top_routes(df, n=15):
    print(f"正在產生圖表：前 {n} 名路線運量排名...")
    route_counts = df['路線'].value_counts().nlargest(n)

    # 【新增】印出分析結果
    print(f"\n--- 3. 前 {n} 名路線運量排名結果 ---")
    print(route_counts)
    print("----------------------------------\n")

    plt.figure(figsize=(12, 9))
    sns.barplot(y=route_counts.index, x=route_counts.values, orient='h', palette='magma', hue=route_counts.index, legend=False)
    plt.title(f'前 {n} 名路線運量排名', fontsize=18, fontweight='bold')
    plt.xlabel('總搭乘人次', fontsize=12)
    plt.ylabel('路線編號', fontsize=12)
    for index, value in enumerate(route_counts.values):
        plt.text(value, index, f' {value:,}', va='center')
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, '3_路線運量排名.png'))
    plt.close()

def plot_passenger_distribution(df):
    print("正在產生圖表：乘客票種結構分析...")
    passenger_counts = df['票種分類'].value_counts()
    passenger_percentages = df['票種分類'].value_counts(normalize=True) * 100

    # 【新增】印出分析結果
    print("\n--- 4. 乘客票種結構分析結果 ---")
    result_df = pd.DataFrame({
        '搭乘人次': passenger_counts,
        '佔比 (%)': passenger_percentages.round(2)
    })
    print(result_df)
    print("----------------------------------\n")

    plt.figure(figsize=(10, 10))
    colors = sns.color_palette('pastel')[0:len(passenger_counts)]
    plt.pie(passenger_counts, labels=passenger_counts.index, autopct='%1.1f%%', startangle=140, colors=colors, textprops={'fontsize': 14})
    plt.title('乘客票種結構分析', fontsize=18, fontweight='bold')
    plt.ylabel('')
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, '4_乘客票種結構分析.png'))
    plt.close()

def plot_avg_trip_duration(df, n=15):
    print(f"正在產生圖表：前 {n} 名平均旅次時間最長路線...")
    valid_duration_df = df[df['旅次時間_分'] <= 180]
    avg_duration = valid_duration_df.groupby('路線')['旅次時間_分'].mean().nlargest(n).sort_values(ascending=False)

    # 【新增】印出分析結果
    print(f"\n--- 5. 前 {n} 名平均旅次時間最長路線結果 ---")
    print(avg_duration.round(2)) # 顯示到小數點後兩位
    print("------------------------------------------\n")

    plt.figure(figsize=(12, 9))
    # 修正排序，讓圖表從長到短顯示
    sorted_avg_duration = avg_duration.sort_values()
    sns.barplot(y=sorted_avg_duration.index, x=sorted_avg_duration.values, orient='h', palette='coolwarm', hue=sorted_avg_duration.index, legend=False)
    plt.title(f'各路線平均旅次時間（前 {n} 名）', fontsize=18, fontweight='bold')
    plt.xlabel('平均旅次時間（分鐘）', fontsize=12)
    plt.ylabel('路線編號', fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, '5_各路線平均旅次時間.png'))
    plt.close()

def plot_hourly_ridership(df):
    print("正在產生圖表：平日與週末每小時運量比較...")
    hourly_counts = df.groupby(['上車小時', '平日/週末']).size().unstack(fill_value=0)

    # 【新增】印出分析結果
    print("\n--- 6. 平日與週末每小時運量比較結果 ---")
    print(hourly_counts)
    print("----------------------------------------\n")

    plt.figure(figsize=(15, 8))
    hourly_counts.plot(kind='line', marker='o', ax=plt.gca())
    plt.title('平日與週末每小時運量比較', fontsize=18, fontweight='bold')
    plt.xlabel('小時', fontsize=12)
    plt.ylabel('平均搭乘人次', fontsize=12)
    plt.xticks(ticks=range(24), labels=[f'{i}:00' for i in range(24)], rotation=45)
    plt.grid(True, which='both', linestyle='--', alpha=0.7)
    plt.legend(title='時段')
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, '6_平日週末每小時運量比較.png'))
    plt.close()

def plot_top_stations(df, n=15):
    print(f"正在產生圖表：前 {n} 名最繁忙站點排名...")
    boardings = df['上車站名'].value_counts()
    alightings = df['下車站名'].value_counts()
    total_activity = boardings.add(alightings, fill_value=0).sort_values(ascending=False).nlargest(n)

    # 【新增】印出分析結果
    print(f"\n--- 7. 前 {n} 名最繁忙站點排名結果 ---")
    print(total_activity)
    print("------------------------------------\n")

    plt.figure(figsize=(12, 10))
    sns.barplot(y=total_activity.index, x=total_activity.values, orient='h', palette='rocket', hue=total_activity.index, legend=False)
    plt.title(f'前 {n} 名最繁忙站點（上下車總人次）', fontsize=18, fontweight='bold')
    plt.xlabel('總活動人次（上車+下車）', fontsize=12)
    plt.ylabel('站點名稱', fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, '7_最繁忙站點排名.png'))
    plt.close()

def plot_top_od_pairs(df, n=15):
    print(f"正在產生圖表：前 {n} 名主要交通廊帶...")
    od_counts = df.groupby(['上車站名', '下車站名']).size().nlargest(n)

    # 【新增】印出分析結果
    print(f"\n--- 8. 前 {n} 名主要交通廊帶結果 ---")
    print(od_counts)
    print("------------------------------------\n")

    plt.figure(figsize=(12, 10))
    od_labels = [f"{start} → {end}" for start, end in od_counts.index]
    sns.barplot(y=od_labels, x=od_counts.values, orient='h', palette='crest', hue=od_labels, legend=False)
    plt.title(f'前 {n} 名主要交通廊帶（起訖點分析）', fontsize=18, fontweight='bold')
    plt.xlabel('總旅次數', fontsize=12)
    plt.ylabel('起訖點', fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, '8_主要交通廊帶分析.png'))
    plt.close()

def plot_student_pattern_per_route(df, min_records=20):
    print("正在為各路線產生學生平日通勤模式圖...")
    
    per_route_folder = os.path.join(output_folder, '各路線學生通勤模式')
    if not os.path.exists(per_route_folder):
        os.makedirs(per_route_folder)
        
    student_df = df[(df['票種分類'] == '學生') & (df['平日/週末'] == '平日')]
    unique_routes = student_df['路線'].unique()
    
    print(f"偵測到 {len(unique_routes)} 條路線有學生搭乘記錄，將開始逐一製圖...")
    
    # 【新增】印出分析結果的標題
    print("\n--- 9. 各路線學生平日通勤模式分析結果 ---")
    
    for route in unique_routes:
        route_df = student_df[student_df['路線'] == route]
        
        if len(route_df) < min_records:
            print(f"-> 路線 {route} 的學生搭乘資料量過少 ({len(route_df)} 筆)，已跳過。")
            continue
            
        print(f"-> 正在產生路線 {route} 的圖表...")
        
        student_hourly = route_df.groupby('上車小時').size()
        student_hourly = student_hourly.reindex(range(24), fill_value=0)

        # 【新增】印出該路線的分析數據
        print(f"\n===== 路線 {route} 學生搭乘時段分佈 =====")
        print(student_hourly)
        print("=" * 40)
        
        plt.figure(figsize=(15, 8))
        sns.lineplot(x=student_hourly.index, y=student_hourly.values, marker='o', color='dodgerblue')
        plt.title(f'路線 {route} - 學生平日搭乘時段分佈', fontsize=18, fontweight='bold')
        plt.xlabel('上車小時', fontsize=12)
        plt.ylabel('總搭乘人次', fontsize=12)
        plt.xticks(ticks=range(24))
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        safe_route_name = str(route).replace('/', '_')
        plt.savefig(os.path.join(per_route_folder, f'學生通勤模式_路線_{safe_route_name}.png'))
        plt.close()

    print("-------------------------------------------\n")
    print("所有路線的學生通勤模式圖表已產生完畢。")

def plot_elderly_pattern_and_destinations(df):
    elderly_df = df[df['票種分類'] == '優待']

    print("正在產生圖表：長者愛心乘客出行模式...")
    elderly_hourly = elderly_df.groupby('上車小時').size().reindex(range(24), fill_value=0)
    
    # 【新增】印出分析結果
    print("\n--- 10. 長者愛心乘客分析結果 ---")
    print("===== 優待乘客出行時段分佈 =====")
    print(elderly_hourly)
    print("-" * 35)

    print("正在產生圖表：優待乘客熱門目的地...")
    top_destinations = elderly_df['下車站名'].value_counts().nlargest(15)
    
    print("\n===== 優待乘客熱門目的地 (Top 15) =====")
    print(top_destinations)
    print("------------------------------------\n")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 16), gridspec_kw={'height_ratios': [1, 2]})
    sns.lineplot(x=elderly_hourly.index, y=elderly_hourly.values, marker='o', color='green', ax=ax1)
    ax1.set_title('優待乘客出行時段分佈', fontsize=16, fontweight='bold')
    ax1.set_xlabel('上車小時', fontsize=12)
    ax1.set_ylabel('搭乘人次', fontsize=12)
    ax1.set_xticks(ticks=range(24))
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.axvspan(9, 11, color='lightgreen', alpha=0.4, label='日間高峰')
    ax1.legend()
    
    sns.barplot(y=top_destinations.index, x=top_destinations.values, orient='h', palette='BuGn_r', ax=ax2, hue=top_destinations.index, legend=False)
    ax2.set_title('優待乘客熱門目的地（下車站點）', fontsize=16, fontweight='bold')
    ax2.set_xlabel('下車人次', fontsize=12)
    ax2.set_ylabel('站點名稱', fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, '10_長者愛心乘客分析.png'))
    plt.close()

# --- 3. 主程式執行區塊 ---
if __name__ == '__main__':
    bus_data = load_and_preprocess_data()
    if bus_data is not None:
        # 【新增】提示使用者即將開始輸出分析結果
        print("\n==============================================")
        print("          開始輸出各項分析結果          ")
        print("==============================================\n")
        
        plot_monthly_ridership(bus_data)
        plot_weekly_ridership(bus_data)
        plot_top_routes(bus_data)
        plot_passenger_distribution(bus_data)
        plot_avg_trip_duration(bus_data)
        plot_hourly_ridership(bus_data)
        plot_top_stations(bus_data)
        plot_top_od_pairs(bus_data)
        plot_student_pattern_per_route(bus_data)
        plot_elderly_pattern_and_destinations(bus_data)
        print("\n所有圖表已成功產生並儲存於 '{}' 資料夾中。".format(output_folder))