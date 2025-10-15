# 這是主分析檔案：main_analysis.py (僅包含分析九：斗六車站尖峰時段分析)

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
    # 篩選分析區間：限定在「彰化到嘉義」之間
    # ==============================================================================
    print("\n--- [設定分析區間：彰化到嘉義] ---")
    
    target_stations = [
        '彰化', '花壇', '大村', '員林', '永靖', '社頭', '田中', '二水',
        '林內', '石榴', '斗六', '斗南', '石龜',
        '大林', '民雄', '南靖', '水上',
        '嘉北', '嘉義'
    ]
    
    all_data = all_data[
        all_data['起點'].isin(target_stations) & 
        all_data['迄點'].isin(target_stations)
    ]
    
    print(f"已將資料範圍限定在 {len(target_stations)} 個車站內，後續將僅分析此區間的資料。")
    
    # ==============================================================================
    # 分析九：斗六車站尖峰時段分析 (細分平日/假日)
    # ==============================================================================
    print("\n--- [分析：斗六車站尖峰時段分析 (含平日/假日)] ---")
    print("註：此分析僅針對有提供進、出站時間的資料。")

    # 1. 準備高精度時間資料
    data_for_peak = all_data.copy()
    
    # 建立統一的時間欄位
    data_for_peak['進站時間'] = dd.to_datetime(
        data_for_peak['進站時間'],
        format='%Y-%m-%d %H:%M:%S',
        errors='coerce'
    )

    data_for_peak['出站時間'] = dd.to_datetime(
        data_for_peak['出站時間'],
        format='%Y-%m-%d %H:%M:%S',
        errors='coerce'
    )


    # 2. 篩選斗六站相關資料並轉換為 Pandas DataFrame
    douliu_data_dd = data_for_peak[
        (data_for_peak['起點'] == '斗六') | (data_for_peak['迄點'] == '斗六')
    ]
    douliu_data = douliu_data_dd.compute()
    print(f"已篩選出與斗六站相關的資料共 {len(douliu_data)} 筆，開始計算...")

    # 3. 計算上車人次 (Departures)，並按平日/假日分類
    douliu_departures = douliu_data[douliu_data['起點'] == '斗六'].dropna(subset=['進站時間']).copy()
    if not douliu_departures.empty:
        minute_of_day_dep = douliu_departures['進站時間'].dt.hour * 60 + douliu_departures['進站時間'].dt.minute
        douliu_departures['時段_5分'] = (minute_of_day_dep // 5).astype(int)
        dep_pivot = douliu_departures.pivot_table(index='時段_5分', columns='日期類型', values='人次', aggfunc='sum')
        dep_pivot.columns = [f'{col}_上車' for col in dep_pivot.columns] # 重新命名欄位以便區分
    else:
        dep_pivot = pd.DataFrame()

    # 4. 計算下車人次 (Arrivals)，並按平日/假日分類
    douliu_arrivals = douliu_data[douliu_data['迄點'] == '斗六'].dropna(subset=['出站時間']).copy()
    if not douliu_arrivals.empty:
        minute_of_day_arr = douliu_arrivals['出站時間'].dt.hour * 60 + douliu_arrivals['出站時間'].dt.minute
        douliu_arrivals['時段_5分'] = (minute_of_day_arr // 5).astype(int)
        arr_pivot = douliu_arrivals.pivot_table(index='時段_5分', columns='日期類型', values='人次', aggfunc='sum')
        arr_pivot.columns = [f'{col}_下車' for col in arr_pivot.columns] # 重新命名欄位以便區分
    else:
        arr_pivot = pd.DataFrame()

    # 5. 合併所有資料
    full_day_index = pd.Index(range(24 * 12), name='時段_5分')
    douliu_peak_df = pd.DataFrame(index=full_day_index)
    douliu_peak_df = douliu_peak_df.join(dep_pivot).join(arr_pivot).fillna(0).astype(int)
    
    # 確保所有可能的欄位都存在，避免因資料缺失而出錯
    expected_cols = ['平日_上車', '假日_上車', '平日_下車', '假日_下車']
    for col in expected_cols:
        if col not in douliu_peak_df.columns:
            douliu_peak_df[col] = 0

    # 重新排序欄位，方便閱讀
    douliu_peak_df = douliu_peak_df[expected_cols]

    # 6. 顯示文字報表
    print("\n--- [文字報表：斗六站各時段上、下車旅運量完整結果 (每5分鐘)] ---")
    def block_to_time(block):
        hour = block * 5 // 60
        minute = block * 5 % 60
        return f'{hour:02d}:{minute:02d}'
    
    display_df = douliu_peak_df.copy()
    display_df.index = display_df.index.map(block_to_time)
    display_df.index.name = '時間'
    print(display_df.to_string())

    # 7. 儲存CSV檔案
    output_path = os.path.join(output_csv_dir, 'analysis_douliu_peak_5min.csv')
    douliu_peak_df.to_csv(output_path, encoding='utf-8-sig')
    print(f"\n斗六站尖峰分析結果已儲存至 {output_path}")

    # 8. 繪製圖表
    time_chunks = {
        "清晨 (00-06點)": (0, 6 * 12),
        "上午 (06-12點)": (6 * 12, 12 * 12),
        "下午 (12-18點)": (12 * 12, 18 * 12),
        "傍晚至午夜 (18-24點)": (18 * 12, 24 * 12)
    }

    for title, (start_block, end_block) in time_chunks.items():
        chunk_data = douliu_peak_df.loc[start_block : end_block-1]
        
        if chunk_data.empty or chunk_data.sum().sum() == 0:
            print(f"\n時間區塊 '{title}' 沒有資料，跳過繪圖。")
            continue

        chunk_data.index = chunk_data.index.map(block_to_time)

        plt.figure(figsize=(15, 8))
        
        # 使用 melt 將寬數據轉換為長數據，以便 Seaborn 繪圖
        plot_data = chunk_data.reset_index().melt(id_vars='時段_5分', var_name='類型', value_name='人次')
        
        ax = sns.lineplot(data=plot_data, x='時段_5分', y='人次', hue='類型', style='類型',
                          markers=True, dashes=False, markersize=7, palette='tab10')
        
        plt.title(f'斗六車站尖峰時段分析 - {title}', fontsize=18, pad=20)
        plt.xlabel('時間', fontsize=12)
        plt.ylabel('總人次', fontsize=12)
        
        # 設定 x 軸刻度，每 30 分鐘一個刻度 (6個5分鐘)
        ax.xaxis.set_major_locator(mticker.MultipleLocator(6)) 
        plt.xticks(rotation=45, ha='right')
        
        plt.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.legend(title='類型', bbox_to_anchor=(1.02, 1), loc='upper left')
        plt.tight_layout(rect=[0, 0, 0.9, 1]) # 調整佈局以容納圖例
        
        chart_filename = f'chart_douliu_peak_{title.split(" ")[0]}.png'
        chart_path = os.path.join(output_chart_dir, chart_filename)
        plt.savefig(chart_path, dpi=300)
        plt.close()
        print(f"圖表已儲存至 {chart_path}")


    print("\n\n所有分析已完成！")
else:
    print("無法載入資料，分析中止。")
