# 這是主分析檔案：main_analysis.py (已加入區間篩選與斗六站尖峰分析)

import matplotlib
matplotlib.use('Agg')

import pandas as pd
import dask.dataframe as dd
from data_loader import load_all_data
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns 
import os 

# ==============================================================================
# 建立輸出資料夾
# ==============================================================================
output_csv_dir = 'analysis_results'
output_chart_dir = 'charts'

os.makedirs(output_csv_dir, exist_ok=True)
os.makedirs(output_chart_dir, exist_ok=True)

print(f"CSV 結果將儲存至 '{output_csv_dir}/' 資料夾。")
print(f"圖表將儲存至 '{output_chart_dir}/' 資料夾。")


# ==============================================================================
# 圖表中文設定 (使用系統字體)
# ==============================================================================
def setup_chinese_font():
    """
    設定 Matplotlib 與 Seaborn 使用系統內建的中文字體。
    """
    try:
        # 使用 'Microsoft JhengHei' 作為預設繁體中文字體
        font_name = 'Microsoft JhengHei'
        plt.rcParams['font.sans-serif'] = [font_name] 
        plt.rcParams['axes.unicode_minus'] = False
        
        sns.set_theme(style="whitegrid", font=font_name)
        print(f"Matplotlib 與 Seaborn 中文字體已設定為 '{font_name}'。")
        
    except Exception as e:
        print(f"警告：設定字體時發生錯誤: {e}")
        print("圖表中的中文可能無法正確顯示。請確認您的系統中是否已安裝 '微軟正黑體'。")

setup_chinese_font()


# ==============================================================================
# 核心步驟：載入並準備所有資料
# ==============================================================================
all_data = load_all_data()

if all_data is not None:
    
    # ==============================================================================
    # <<< 新增區塊：定義並篩選車站區間 >>>
    # ==============================================================================
    print("\n--- [設定分析區間：彰化到嘉義] ---")
    
    # 1. 定義「彰化到嘉義」區間的所有車站
    target_stations = [
        # 彰化縣
        '彰化', '花壇', '大村', '員林', '永靖', '社頭', '田中', '二水',
        # 雲林縣
        '林內', '石榴', '斗六', '斗南', '石龜',
        # 嘉義縣
        '大林', '民雄', '南靖', '水上',
        # 嘉義市
        '嘉北', '嘉義'
    ]
    
    # 2. 篩選資料：只保留起點和迄點都在目標清單中的旅次
    # 使用 .isin() 方法來判斷起點和迄點是否在我們的目標車站清單內
    all_data = all_data[
        all_data['起點'].isin(target_stations) & 
        all_data['迄點'].isin(target_stations)
    ]
    
    print(f"已將資料範圍限定在 {len(target_stations)} 個車站內，後續將僅分析此區間的資料。")
    # <<< 新增區塊結束 >>>
    # ==============================================================================
    
    # ==============================================================================
    # 分析一：黃金路線分析 (熱門OD)
    # ==============================================================================
    print("\n--- [分析一：黃金路線分析] ---")
    hot_od = all_data.groupby(['起點', '迄點'])['人次'].sum().nlargest(20).compute()
    print("全台客運量最高的 Top 20 路線 (OD):")
    print(hot_od)
    output_path = os.path.join(output_csv_dir, 'analysis_hot_od.csv')
    hot_od.to_csv(output_path, encoding='utf-8-sig')
    print(f"結果已儲存至 {output_path}")

    # --- 繪圖 (Seaborn) ---
    plt.figure(figsize=(10, 8))
    hot_od_df = hot_od.reset_index()
    hot_od_df.columns = ['起點', '迄點', '總人次']
    hot_od_df['路線'] = hot_od_df['起點'] + ' → ' + hot_od_df['迄點']
    
    sns.barplot(x='總人次', y='路線', data=hot_od_df.sort_values('總人次', ascending=False), palette='viridis', hue='路線', legend=False)
    plt.title('全台客運量 Top 20 路線 (OD)', fontsize=16)
    plt.xlabel('總人次', fontsize=12)
    plt.ylabel('路線', fontsize=12)
    plt.tight_layout()
    chart_path = os.path.join(output_chart_dir, 'chart_hot_od.png')
    plt.savefig(chart_path, dpi=300)
    plt.close()
    print(f"Seaborn 圖表已儲存至 {chart_path}")

    # ==============================================================================
    # 分析二：尖峰時段分析 (高精度 - 5分鐘間隔)
    # ==============================================================================
    print("\n--- [分析二：尖峰時段分析 (高精度 - 5分鐘間隔)] ---")
    print("註：此分析僅針對有提供進站時間的電子票證與非電子票證資料。")

    # 1. 複製資料以便進行此項專門分析
    data_for_5min = all_data.copy()

    # 2. 建立一個統一的、精確到分鐘的時間欄位        
    data_for_5min['進站時間'] = dd.to_datetime(
        data_for_5min['進站時間'],
        format='%Y-%m-%d %H:%M:%S',
        errors='coerce'
    )
    data_for_5min = data_for_5min.dropna(subset=['進站時間'])

    minute_of_day = data_for_5min['進站時間'].dt.hour * 60 + data_for_5min['進站時間'].dt.minute
    data_for_5min['時段_5分'] = (minute_of_day // 5).astype(int)

    # 3. 進行 pivot table 計算
    peak_5min = data_for_5min.pivot_table(index='時段_5分', columns='日期類型', values='人次', aggfunc='sum').compute()
    peak_5min = peak_5min.fillna(0).astype(int)

    print("平日 vs. 假日 各時段旅運量分佈 (每5分鐘):")
    print(peak_5min)
    output_path = os.path.join(output_csv_dir, 'analysis_peak_5min.csv')
    peak_5min.to_csv(output_path, encoding='utf-8-sig')
    print(f"高精度分析結果已儲存至 {output_path}")

    # 4. 分成多張圖表繪製
    time_chunks = {
        "清晨 (00-06點)": (0, 6 * 12),
        "上午 (06-12點)": (6 * 12, 12 * 12),
        "下午 (12-18點)": (12 * 12, 18 * 12),
        "傍晚至午夜 (18-24點)": (18 * 12, 24 * 12)
    }

    for title, (start_block, end_block) in time_chunks.items():
        chunk_data = peak_5min.loc[start_block : end_block-1]
        
        if chunk_data.empty:
            print(f"\n時間區塊 '{title}' 沒有資料，跳過繪圖。")
            continue

        def block_to_time(block):
            hour = block * 5 // 60
            minute = block * 5 % 60
            return f'{hour:02d}:{minute:02d}'
        
        chunk_data.index = chunk_data.index.map(block_to_time)

        plt.figure(figsize=(15, 7))
        ax = sns.lineplot(data=chunk_data, marker='.', dashes=False, markersize=8)
        
        plt.title(f'尖峰時段分析 (5分鐘間隔) - {title}', fontsize=18)
        plt.xlabel('時間', fontsize=12)
        plt.ylabel('總人次', fontsize=12)
        
        ax.xaxis.set_major_locator(mticker.MultipleLocator(6)) 
        plt.xticks(rotation=45)
        
        plt.grid(True, linestyle='--')
        plt.legend(title='日期類型')
        plt.tight_layout()
        
        chart_filename = f'chart_peak_5min_{title.split(" ")[0]}.png'
        chart_path = os.path.join(output_chart_dir, chart_filename)
        plt.savefig(chart_path, dpi=300)
        plt.close()
        print(f"Seaborn 圖表已儲存至 {chart_path}")
    
    # ==============================================================================
    # 分析三：票證使用分析
    # ==============================================================================
    print("\n--- [分析三：票證使用分析] ---")
    ticket_class = all_data.groupby('票證分類')['人次'].sum().compute()
    print("電子票證(IC) vs. 非電子票證(N-IC) 使用量:")
    print(ticket_class)
    
    card_type = all_data[all_data['票證分類'] == 'IC'].groupby('卡種')['人次'].sum().nlargest(10).compute()
    print("\nTop 10 各類電子票證卡種使用量:")
    print(card_type)
    
    ticket_class_path = os.path.join(output_csv_dir, 'analysis_ticket_class.csv')
    card_type_path = os.path.join(output_csv_dir, 'analysis_card_type.csv')
    ticket_class.to_csv(ticket_class_path, encoding='utf-8-sig')
    card_type.to_csv(card_type_path, encoding='utf-8-sig')
    print(f"結果已儲存至 {ticket_class_path} 與 {card_type_path}")

    # --- 繪圖 (Seaborn - 票證分類) ---
    plt.figure(figsize=(7, 5))
    sns.barplot(x=ticket_class.index, y=ticket_class.values, palette='coolwarm', hue=ticket_class.index, legend=False)
    plt.title('電子票證 vs. 非電子票證 使用量', fontsize=16)
    plt.xlabel('票證分類', fontsize=12)
    plt.ylabel('總人次', fontsize=12)
    plt.xticks(rotation=0)
    plt.tight_layout()
    chart_path = os.path.join(output_chart_dir, 'chart_ticket_class.png')
    plt.savefig(chart_path, dpi=300)
    plt.close()
    print(f"Seaborn 圖表已儲存至 {chart_path}")

    # --- 繪圖 (Seaborn - 卡種) ---
    plt.figure(figsize=(10, 6))
    card_type_df = card_type.reset_index()
    card_type_df.columns = ['卡種', '總人次']
    sns.barplot(x='總人次', y='卡種', data=card_type_df.sort_values('總人次', ascending=False), palette='summer', hue='卡種', legend=False)
    plt.title('Top 10 電子票證卡種使用量', fontsize=16)
    plt.xlabel('總人次', fontsize=12)
    plt.ylabel('卡種', fontsize=12)
    plt.tight_layout()
    chart_path = os.path.join(output_chart_dir, 'chart_card_type.png')
    plt.savefig(chart_path, dpi=300)
    plt.close()
    print(f"Seaborn 圖表已儲存至 {chart_path}")
    
    # ==============================================================================
    # 分析四：持卡身分分析
    # ==============================================================================
    print("\n--- [分析四：持卡身分分析] ---")
    holder_type = all_data.groupby('身分')['人次'].sum().nlargest(10).compute()
    holder_type = holder_type[holder_type.index != 'N/A']
    print("Top 10 旅運量持卡身分:")
    print(holder_type)
    output_path = os.path.join(output_csv_dir, 'analysis_holder_type.csv')
    holder_type.to_csv(output_path, encoding='utf-8-sig')
    print(f"結果已儲存至 {output_path}")

    # --- 繪圖 (Seaborn) ---
    plt.figure(figsize=(10, 6))
    holder_type_df = holder_type.reset_index()
    holder_type_df.columns = ['身分', '總人次']
    sns.barplot(x='總人次', y='身分', data=holder_type_df.sort_values('總人次', ascending=False), palette='autumn', hue='身分', legend=False)
    plt.title('Top 10 旅運量持卡身分', fontsize=16)
    plt.xlabel('總人次', fontsize=12)
    plt.ylabel('身分', fontsize=12)
    plt.tight_layout()
    chart_path = os.path.join(output_chart_dir, 'chart_holder_type.png')
    plt.savefig(chart_path, dpi=300)
    plt.close()
    print(f"Seaborn 圖表已儲存至 {chart_path}")
    
    # ==============================================================================
    # 分析五：平均旅次時間分析
    # ==============================================================================
    print("\n--- [分析五：平均旅次時間分析] ---")
    time_df = all_data.dropna(subset=['進站時間', '出站時間'])
    correct_format = '%Y-%m-%d %H:%M:%S'
    time_df['進站時間'] = dd.to_datetime(time_df['進站時間'], format=correct_format, errors='coerce')
    time_df['出站時間'] = dd.to_datetime(time_df['出站時間'], format=correct_format, errors='coerce')
    time_df['旅次時間(分)'] = (time_df['出站時間'] - time_df['進站時間']).dt.total_seconds() / 60
    time_df = time_df[(time_df['旅次時間(分)'] > 1) & (time_df['旅次時間(分)'] < 360)]
    avg_travel_time = time_df.groupby(['起點', '迄點'])['旅次時間(分)'].mean().nlargest(20).compute()
    print("平均旅次時間最長的 Top 20 路線:")
    print(avg_travel_time)
    output_path = os.path.join(output_csv_dir, 'analysis_avg_travel_time.csv')
    avg_travel_time.to_csv(output_path, encoding='utf-8-sig')
    print(f"結果已儲存至 {output_path}")

    # --- 繪圖 (Seaborn) ---
    plt.figure(figsize=(10, 8))
    avg_travel_time_df = avg_travel_time.reset_index()
    avg_travel_time_df.columns = ['起點', '迄點', '平均時間(分)']
    avg_travel_time_df['路線'] = avg_travel_time_df['起點'] + ' → ' + avg_travel_time_df['迄點']
    sns.barplot(x='平均時間(分)', y='路線', data=avg_travel_time_df.sort_values('平均時間(分)', ascending=False), palette='plasma', hue='路線', legend=False)
    plt.title('平均旅次時間最長 Top 20 路線', fontsize=16)
    plt.xlabel('平均時間 (分鐘)', fontsize=12)
    plt.ylabel('路線', fontsize=12)
    plt.tight_layout()
    chart_path = os.path.join(output_chart_dir, 'chart_avg_travel_time.png')
    plt.savefig(chart_path, dpi=300)
    plt.close()
    print(f"Seaborn 圖表已儲存至 {chart_path}")
    
    # ==============================================================================
    # 分析六：通勤走廊識別
    # ==============================================================================
    print("\n--- [分析六：通勤走廊識別] ---")
    weekday_df = all_data[all_data['日期類型'] == '平日']
    
    morning_commute = weekday_df[weekday_df['時段'].isin([7, 8])].groupby(['起點', '迄點'])['人次'].sum().nlargest(10).compute()
    print("平日上午尖峰(7-9點) Top 10 通勤路線:")
    print(morning_commute)
    
    evening_commute = weekday_df[weekday_df['時段'].isin([17, 18])].groupby(['起點', '迄點'])['人次'].sum().nlargest(10).compute()
    print("\n平日傍晚尖峰(17-19點) Top 10 通勤路線:")
    print(evening_commute)
    
    morning_path = os.path.join(output_csv_dir, 'analysis_morning_commute.csv')
    evening_path = os.path.join(output_csv_dir, 'analysis_evening_commute.csv')
    morning_commute.to_csv(morning_path, encoding='utf-8-sig')
    evening_commute.to_csv(evening_path, encoding='utf-8-sig')
    print(f"結果已儲存至 {morning_path} 與 {evening_path}")

    # --- 繪圖 (Seaborn - 上午) ---
    plt.figure(figsize=(10, 6))
    morning_commute_df = morning_commute.reset_index()
    morning_commute_df.columns = ['起點', '迄點', '總人次']
    morning_commute_df['路線'] = morning_commute_df['起點'] + ' → ' + morning_commute_df['迄點']
    sns.barplot(x='總人次', y='路線', data=morning_commute_df.sort_values('總人次', ascending=False), palette='Oranges_r', hue='路線', legend=False)
    plt.title('平日上午尖峰(7-9點) Top 10 通勤路線', fontsize=16)
    plt.xlabel('總人次', fontsize=12)
    plt.ylabel('路線', fontsize=12)
    plt.tight_layout()
    chart_path = os.path.join(output_chart_dir, 'chart_morning_commute.png')
    plt.savefig(chart_path, dpi=300)
    plt.close()
    print(f"Seaborn 圖表已儲存至 {chart_path}")
    
    # --- 繪圖 (Seaborn - 傍晚) ---
    plt.figure(figsize=(10, 6))
    evening_commute_df = evening_commute.reset_index()
    evening_commute_df.columns = ['起點', '迄點', '總人次']
    evening_commute_df['路線'] = evening_commute_df['起點'] + ' → ' + evening_commute_df['迄點']
    sns.barplot(x='總人次', y='路線', data=evening_commute_df.sort_values('總人次', ascending=False), palette='GnBu_d', hue='路線', legend=False)
    plt.title('平日傍晚尖峰(17-19點) Top 10 通勤路線', fontsize=16)
    plt.xlabel('總人次', fontsize=12)
    plt.ylabel('路線', fontsize=12)
    plt.tight_layout()
    chart_path = os.path.join(output_chart_dir, 'chart_evening_commute.png')
    plt.savefig(chart_path, dpi=300)
    plt.close()
    print(f"Seaborn 圖表已儲存至 {chart_path}")
    
    # ==============================================================================
    # 分析七：特定區間流量分析 (彰化-雲林-嘉義)
    # ==============================================================================
    print("\n--- [分析七：特定區間流量分析 (彰化-雲林-嘉義)] ---")

    # 1. 建立車站到縣市的對應字典
    station_to_city = {
        '彰化': '彰化縣', '花壇': '彰化縣', '大村': '彰化縣', '員林': '彰化縣', '永靖': '彰化縣', '社頭': '彰化縣', '田中': '彰化縣', '二水': '彰化縣',
        '林內': '雲林縣', '石榴': '雲林縣', '斗六': '雲林縣', '斗南': '雲林縣', '石龜': '雲林縣',
        '大林': '嘉義縣', '民雄': '嘉義縣', '南靖': '嘉義縣', '水上': '嘉義縣',
        '嘉北': '嘉義市', '嘉義': '嘉義市'
    }

    # 2. 建立縣市欄位
    all_data['起點縣市'] = all_data['起點'].map(station_to_city, meta=('起點縣市', 'object'))
    all_data['迄點縣市'] = all_data['迄點'].map(station_to_city, meta=('迄點縣市', 'object'))

    # 3. 計算縣市間流量
    county_to_county = all_data.groupby(['起點縣市', '迄點縣市'])['人次'].sum().compute()
    final_summary = county_to_county[county_to_county > 0].sort_values(ascending=False)

    print("\n--- 特定路線流量分析結果 ---")
    print(final_summary)

    # 4. 儲存至 CSV
    output_path = os.path.join(output_csv_dir, 'analysis_specific_flows.csv')
    final_summary.to_csv(output_path, encoding='utf-8-sig', header=['總人次'])
    print(f"詳細流量分析結果已儲存至 {output_path}")

    # 5. 繪圖
    plt.figure(figsize=(12, 10))
    summary_df = final_summary.reset_index()
    summary_df.columns = ['起點縣市', '迄點縣市', '總人次']
    summary_df['路線'] = summary_df['起點縣市'] + ' → ' + summary_df['迄點縣市']
    
    ax = sns.barplot(x='總人次', y='路線', data=summary_df, palette='cividis', hue='路線', legend=False)
    ax.set_title('彰化-雲林-嘉義 縣市間流量分析', fontsize=18)
    ax.set_xlabel('總人次', fontsize=12)
    ax.set_ylabel('路線 (起點 → 迄點)', fontsize=12)

    plt.tight_layout()
    chart_path = os.path.join(output_chart_dir, 'chart_specific_flows.png')
    plt.savefig(chart_path, dpi=300)
    plt.close()
    print(f"Seaborn 圖表已儲存至 {chart_path}")
    
    # ==============================================================================
    # 分析八：熱門車站分析
    # ==============================================================================
    print("\n--- [分析八：熱門車站分析] ---")
    
    arrivals = all_data.groupby('迄點')['人次'].sum()
    departures = all_data.groupby('起點')['人次'].sum()
    total_station_traffic = arrivals.add(departures, fill_value=0)
    hot_stations = total_station_traffic.nlargest(20).compute()
    
    print("彰化至嘉義客運量最高的 Top 20 車站:")
    print(hot_stations)
    output_path = os.path.join(output_csv_dir, 'analysis_hot_stations.csv')
    hot_stations.to_csv(output_path, encoding='utf-8-sig')
    print(f"結果已儲存至 {output_path}")

    # --- 繪圖 (Seaborn) ---
    plt.figure(figsize=(10, 8))
    hot_stations_df = hot_stations.reset_index()
    hot_stations_df.columns = ['車站', '總人次']
    sns.barplot(x='總人次', y='車站', data=hot_stations_df.sort_values('總人次', ascending=False), palette='rocket', hue='車站', legend=False)
    plt.title('彰化至嘉義客運量 Top 20 車站', fontsize=16)
    plt.xlabel('總人次 (進站+出站)', fontsize=12)
    plt.ylabel('車站', fontsize=12)
    plt.tight_layout()
    chart_path = os.path.join(output_chart_dir, 'chart_hot_stations.png')
    plt.savefig(chart_path, dpi=300)
    plt.close()
    print(f"Seaborn 圖表已儲存至 {chart_path}")

    print("\n\n所有分析已完成！")
