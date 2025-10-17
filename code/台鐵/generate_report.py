import pandas as pd
import os
import sys

# --- 從 config.py 載入設定 ---
try:
    # 從 code/台鐵/ 回到根目錄
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    import config
except ImportError:
    print("錯誤：無法找到 config.py。請確認您的專案結構。")
    sys.exit(1)

# --- 設定 ---
# 從 config 讀取台鐵分析的輸出路徑
base_output_dir = os.path.join('..', '..', config.TRA_OUTPUT_DIR)
csv_dir = os.path.join(base_output_dir, 'csv')
chart_dir = os.path.join(base_output_dir, 'charts')

# 確保輸出圖表的資料夾存在
os.makedirs(chart_dir, exist_ok=True)

# --- 檔案路徑 ---
# 輸入的 CSV 檔案路徑
input_csv_path = os.path.join(csv_dir, 'analysis_hot_stations.csv')
# 輸出的圖表檔案路徑
output_chart_path = os.path.join(chart_dir, 'chart_hot_stations_from_csv.png')

# --- 主程式 ---
try:
    # --- 步驟 1: 讀取已存在的 CSV 檔案 ---
    print(f"正在從 {input_csv_path} 讀取資料...")
    # 讀取 CSV，並將第一欄當作索引 (車站名稱)
    hot_stations_df = pd.read_csv(input_csv_path)
    
    # 重新命名欄位以便後續使用
    # to_csv 預設會將 Series 的值存到一個名為 '0' 的欄位
    hot_stations_df.columns = ['車站', '總人次']
    print("資料讀取成功！")
    
    # --- 步驟 2: 設定中文字體 ---
    plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei'] 
    plt.rcParams['axes.unicode_minus'] = False # 解決負號顯示問題

    # --- 步驟 3: 繪製圖表 (Seaborn) ---
    print(f"正在繪製圖表...")
    plt.figure(figsize=(12, 8)) # 稍微加大畫布，讓車站名稱更清楚

    # 繪製水平長條圖，並根據 '總人次' 排序
    sns.barplot(
        x='總人次', 
        y='車站', 
        data=hot_stations_df.sort_values('總人次', ascending=False), 
        palette='rocket',
        hue='車站', # 讓每個長條有不同顏色
        legend=False # 關閉圖例，因為 Y 軸已有車站名稱
    )
    
    # --- 步驟 4: 美化圖表 ---
    plt.title('彰化至嘉義客運量 Top 20 車站', fontsize=18)
    plt.xlabel('總人次 (進站+出站)', fontsize=14)
    plt.ylabel('車站', fontsize=14)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    
    # 自動調整版面，避免標籤被裁切
    plt.tight_layout()

    # --- 步驟 5: 儲存圖表 ---
    plt.savefig(output_chart_path, dpi=300)
    plt.close() # 關閉畫布，釋放記憶體

    print(f"圖表已成功儲存至: {output_chart_path}")

except FileNotFoundError:
    print(f"錯誤：找不到檔案 {input_csv_path}。")
    print("請確認檔案名稱和路徑是否正確，以及程式是否在正確的資料夾中執行。")
except Exception as e:
    print(f"發生未預期的錯誤：{e}")

