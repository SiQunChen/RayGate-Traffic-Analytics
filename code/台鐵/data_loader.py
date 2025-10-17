import pandas as pd
import dask.dataframe as dd
import os
import sys # 匯入 sys 模組

# --- 從 config.py 載入設定 ---
try:
    # 假設 config.py 在上層目錄
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    import config
except ImportError:
    print("錯誤：無法找到 config.py。請確認您的專案結構。")
    sys.exit(1)

def load_and_save_data(output_filename=config.TRA_CLEANED_DATA_FILE):
    """
    讀取、清理、整合所有四個臺鐵資料集，並將結果儲存成一個 CSV 檔。
    """
    print("--- 開始載入並整合所有資料來源 ---")

    # *** 新增：測試模式 ***
    nrows_to_read = config.TEST_MODE_ROWS if config.TEST_MODE else None
    reader = pd if config.TEST_MODE else dd # 根據模式選擇 reader
    
    if config.TEST_MODE:
        print(f"--- [測試模式已啟用] ---")
        print(f"所有 CSV 檔案將只讀取前 {nrows_to_read} 行。")
        print("--------------------------\n")

    all_dfs = []
    data_dir = config.TRA_RAW_DATA_DIR

    # --- 檔案3: 臺鐵非電子票證資料 ---
    non_ic_file = os.path.join(data_dir, '臺鐵非電子票證資料.csv')
    try:
        # *** 核心修改：使用選擇的 reader 並加入 nrows ***
        df = reader.read_csv(non_ic_file, skiprows=[1], header=0,
                             dtype={'票面起站車站代碼': 'object', '票面迄站車站代碼': 'object', '票種次類型': 'object'},
                             nrows=nrows_to_read)
        df['人次'] = 1
        df = df.rename(columns={'乘車日期': '日期','票面起站車站名稱': '起點','票面迄站車站名稱': '迄點','票種類型': '票種'})
        
        # 如果是 pandas DataFrame，轉換為 dask
        if isinstance(df, pd.DataFrame):
            df = dd.from_pandas(df, npartitions=1)
            
        df['時段'] = dd.to_datetime(df['進站時間'], format='%Y-%m-%d %H:%M:%S', errors='coerce').dt.hour
        df['票證分類'] = 'N-IC'; df['卡種'] = 'N/A'; df['身分'] = 'N/A'
        all_dfs.append(df[['日期', '時段', '票證分類', '卡種', '身分', '起點', '迄點', '人次', '進站時間', '出站時間']])
        print(f"成功載入: {non_ic_file}")
    except FileNotFoundError:
        print(f"警告: 找不到檔案 {non_ic_file}，將跳過。")

    # --- 檔案4: 臺鐵電子票證資料(TO1A) ---
    ic_file = os.path.join(data_dir, '臺鐵電子票證資料(TO1A).csv')
    try:
        # *** 核心修改：使用選擇的 reader 並加入 nrows ***
        df = reader.read_csv(ic_file, skiprows=[1], header=0,
                             dtype={'刷卡進入車站代碼': 'object', '刷卡離開車站代碼': 'object', '票種次類型': 'object'},
                             nrows=nrows_to_read)
        df['人次'] = 1
        df = df.rename(columns={'資料代表日期(yyyy-MM-dd)': '日期','刷卡進入車站時間': '進站時間','刷卡離開車站時間': '出站時間','電子票證卡種': '卡種','持卡身分': '身分','刷卡進入車站名稱': '起點','刷卡離開車站名稱': '迄點'})
        
        # 如果是 pandas DataFrame，轉換為 dask
        if isinstance(df, pd.DataFrame):
            df = dd.from_pandas(df, npartitions=1)

        df['時段'] = dd.to_datetime(df['進站時間'], format='%Y-%m-%d %H:%M:%S', errors='coerce').dt.hour
        df['票證分類'] = 'IC'
        all_dfs.append(df[['日期', '時段', '票證分類', '卡種', '身分', '起點', '迄點', '人次', '進站時間', '出站時間']])
        print(f"成功載入: {ic_file}")
    except FileNotFoundError:
        print(f"警告: 找不到檔案 {ic_file}，將跳過。")
        
    if not all_dfs:
        print("錯誤：所有資料檔案都找不到，無法進行分析。")
        return None

    print("\n正在合併所有資料來源...")
    combined_df = dd.concat(all_dfs, ignore_index=True)
    
    combined_df['日期'] = dd.to_datetime(combined_df['日期'], format='%Y-%m-%d', errors='coerce')
    combined_df['星期'] = combined_df['日期'].dt.weekday
    combined_df['日期類型'] = '平日'
    combined_df['日期類型'] = combined_df['日期類型'].mask(combined_df['星期'].isin([5, 6]), '假日')
    combined_df['日期類型'] = combined_df['日期類型'].astype('category').cat.set_categories(['平日', '假日'])
    print("資料準備完成！")
    
    # --- (後續的儲存程式碼不變) ---
    print(f"\n--- 正在將清洗後的資料儲存至 '{output_filename}' ---")
    try:
        os.makedirs(os.path.dirname(output_filename), exist_ok=True)
        combined_df.to_csv(output_filename, single_file=True, index=False, encoding='utf-8-sig')
        print(f"成功！資料已儲存至 '{os.path.abspath(output_filename)}'")
    except Exception as e:
        print(f"錯誤：儲存檔案時發生問題: {e}")
    return combined_df

if __name__ == '__main__':
    final_df = load_and_save_data(output_filename='cleaned_tra_data.csv')
    if final_df is not None:
        print("\n--- 資料處理完成，以下為前 5 筆資料預覽 ---")
        print(final_df.head())