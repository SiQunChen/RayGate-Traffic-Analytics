# tra/station_analyzer.py (修改後的版本)

import matplotlib
matplotlib.use('Agg')

import pandas as pd
import dask.dataframe as dd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import os
import argparse # 匯入 argparse 以便獨立執行時接收參數

# (setup_chinese_font 函式維持原樣)

def run_analysis(data_path, station_name):
    """
    對指定的台鐵車站進行深度尖峰時段分析。
    Args:
        data_path (str): 清理過的台鐵資料檔案路徑 (cleaned_tra_data.csv)。
        station_name (str): 要分析的車站名稱 (例如: '斗六', '嘉義')。
    """
    print(f"\n--- [分析：{station_name}車站尖峰時段分析 (含平日/假日)] ---")
    print("註：此分析僅針對有提供進、出站時間的資料。")

    # 建立輸出資料夾
    output_csv_dir = os.path.join('tra', 'analysis_results')
    output_chart_dir = os.path.join('tra', 'charts')
    os.makedirs(output_csv_dir, exist_ok=True)
    os.makedirs(output_chart_dir, exist_ok=True)

    # 讀取資料
    all_data = dd.read_csv(data_path, dtype={'卡種': 'object', '身分': 'object'})

    # 1. 準備高精度時間資料
    data_for_peak = all_data.copy()
    data_for_peak['進站時間'] = dd.to_datetime(data_for_peak['進站時間'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
    data_for_peak['出站時間'] = dd.to_datetime(data_for_peak['出站時間'], format='%Y-%m-%d %H:%M:%S', errors='coerce')

    # 2. 【修改點】篩選指定車站相關資料並轉換為 Pandas DataFrame
    station_data_dd = data_for_peak[
        (data_for_peak['起點'] == station_name) | (data_for_peak['迄點'] == station_name)
    ]
    station_data = station_data_dd.compute()
    print(f"已篩選出與 {station_name} 站相關的資料共 {len(station_data)} 筆，開始計算...")

    # 3. 【修改點】計算上車人次
    departures = station_data[station_data['起點'] == station_name].dropna(subset=['進站時間']).copy()
    if not departures.empty:
        minute_of_day_dep = departures['進站時間'].dt.hour * 60 + departures['進站時間'].dt.minute
        departures['時段_5分'] = (minute_of_day_dep // 5).astype(int)
        dep_pivot = departures.pivot_table(index='時段_5分', columns='日期類型', values='人次', aggfunc='sum')
        dep_pivot.columns = [f'{col}_上車' for col in dep_pivot.columns]
    else:
        dep_pivot = pd.DataFrame()

    # 4. 【修改點】計算下車人次
    arrivals = station_data[station_data['迄點'] == station_name].dropna(subset=['出站時間']).copy()
    if not arrivals.empty:
        minute_of_day_arr = arrivals['出站時間'].dt.hour * 60 + arrivals['出站時間'].dt.minute
        arrivals['時段_5分'] = (minute_of_day_arr // 5).astype(int)
        arr_pivot = arrivals.pivot_table(index='時段_5分', columns='日期類型', values='人次', aggfunc='sum')
        arr_pivot.columns = [f'{col}_下車' for col in arr_pivot.columns]
    else:
        arr_pivot = pd.DataFrame()

    # 5. 合併所有資料
    full_day_index = pd.Index(range(24 * 12), name='時段_5分')
    peak_df = pd.DataFrame(index=full_day_index)
    peak_df = peak_df.join(dep_pivot).join(arr_pivot).fillna(0).astype(int)

    expected_cols = ['平日_上車', '假日_上車', '平日_下車', '假日_下車']
    for col in expected_cols:
        if col not in peak_df.columns:
            peak_df[col] = 0
    peak_df = peak_df[expected_cols]

    # 6. 【修改點】顯示與儲存結果
    print(f"\n--- [文字報表：{station_name}站各時段上、下車旅運量完整結果 (每5分鐘)] ---")
    def block_to_time(block):
        hour = block * 5 // 60
        minute = block * 5 % 60
        return f'{hour:02d}:{minute:02d}'
    
    display_df = peak_df.copy()
    display_df.index = display_df.index.map(block_to_time)
    display_df.index.name = '時間'
    print(display_df.to_string())

    output_path = os.path.join(output_csv_dir, f'analysis_{station_name}_peak_5min.csv')
    peak_df.to_csv(output_path, encoding='utf-8-sig')
    print(f"\n{station_name}站尖峰分析結果已儲存至 {output_path}")

    # 7. 【修改點】繪製圖表
    time_chunks = {
        "清晨 (00-06點)": (0, 6 * 12),
        "上午 (06-12點)": (6 * 12, 12 * 12),
        "下午 (12-18點)": (12 * 12, 18 * 12),
        "傍晚至午夜 (18-24點)": (18 * 12, 24 * 12)
    }

    for title, (start_block, end_block) in time_chunks.items():
        chunk_data = peak_df.loc[start_block : end_block-1]
        
        if chunk_data.empty or chunk_data.sum().sum() == 0:
            print(f"\n時間區塊 '{title}' 沒有資料，跳過繪圖。")
            continue

        chunk_data.index = chunk_data.index.map(block_to_time)

        plt.figure(figsize=(15, 8))
        
        # 使用 melt 將寬數據轉換為長數據，以便 Seaborn 繪圖
        plot_data = chunk_data.reset_index().melt(id_vars='時段_5分', var_name='類型', value_name='人次')
        
        ax = sns.lineplot(data=plot_data, x='時段_5分', y='人次', hue='類型', style='類型',
                          markers=True, dashes=False, markersize=7, palette='tab10')
        
        plt.title(f'{station_name}車站尖峰時段分析 - {title}', fontsize=18, pad=20)
        plt.xlabel('時間', fontsize=12)
        plt.ylabel('總人次', fontsize=12)
        
        # 設定 x 軸刻度，每 30 分鐘一個刻度 (6個5分鐘)
        ax.xaxis.set_major_locator(mticker.MultipleLocator(6)) 
        plt.xticks(rotation=45, ha='right')
        
        plt.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.legend(title='類型', bbox_to_anchor=(1.02, 1), loc='upper left')
        plt.tight_layout(rect=[0, 0, 0.9, 1]) # 調整佈局以容納圖例

        chart_filename = f'chart_{station_name}_peak_{title.split(" ")[0]}.png'
        chart_path = os.path.join(output_chart_dir, chart_filename)
        plt.savefig(chart_path, dpi=300)
        plt.close()
        print(f"圖表已儲存至 {chart_path}")

    print("\n\n分析已完成！")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="執行特定台鐵車站的深度分析。")
    parser.add_argument('--station', type=str, default='斗六', help="要分析的車站名稱。")
    parser.add_argument('--data', type=str, default='tra/cleaned_tra_data.csv', help="已清理的資料檔案路徑。")
    args = parser.parse_args()
    
    # setup_chinese_font() # 如果需要獨立執行，記得取消註解
    run_analysis(data_path=args.data, station_name=args.station)