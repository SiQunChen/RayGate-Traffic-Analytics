# 檔名: code/台鐵/data_loader.py
# 版本: V2 (動態載入版)
# 說明:
# 1. 自動從 config.py 讀取台鐵原始資料路徑 (TRA_RAW_DATA_DIR)。
# 2. 自動掃描該路徑下所有的 .csv 檔案。
# 3. 透過檢查檔案標頭是否包含 '卡號' 欄位，自動判斷為「電子票證」或「非電子票證」資料。
# 4. 根據不同類型套用各自的清理邏輯，最後再全部合併。

import pandas as pd
import dask.dataframe as dd
import os
import sys
import glob  # *** 新增：用於掃描檔案 ***

# --- 從 config.py 載入設定 ---
try:
    # 假設 config.py 在上層目錄
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    import config
except ImportError:
    print("錯誤：無法找到 config.py。請確認您的專案結構。")
    sys.exit(1)


def load_and_save_data(output_filename=config.TRA_UNIFIED_DATA_FILE):
    """
    動態讀取、清理、整合所有在 config.TRA_RAW_DATA_DIR 中的臺鐵資料集，
    並將結果儲存成一個 CSV 檔。
    """
    print("--- 開始載入並整合所有資料來源 (動態掃描模式) ---")

    # --- 測試模式設定 ---
    nrows_to_read = config.TEST_MODE_ROWS if config.TEST_MODE else None
    
    if config.TEST_MODE:
        print(f"--- [測試模式已啟用] ---")
        print(f"所有 CSV 檔案將只讀取前 {nrows_to_read} 行。")
        print("--------------------------\n")
        reader = pd  # 測試模式使用 Pandas
    else:
        reader = dd  # 正式模式使用 Dask

    all_dfs = []
    data_dir = config.TRA_RAW_DATA_DIR

    # *** 核心修改：使用 glob 自動掃描所有 .csv 檔案 ***
    files_to_process = glob.glob(os.path.join(data_dir, '*.csv'))

    if not files_to_process:
        print(f"錯誤：在資料夾 '{data_dir}' 中找不到任何 .csv 檔案。")
        return None

    # 準備 read_csv 的參數 (根據你的分析，我們需要跳過第一行英文標頭)
    read_csv_kwargs = {
        'skiprows': [1],
        'header': 0,
    }
    if config.TEST_MODE:
        read_csv_kwargs['nrows'] = nrows_to_read

    # --- 迭代處理所有掃描到的檔案 ---
    for file_path in files_to_process:
        file_name = os.path.basename(file_path)
        print(f"\n--- 正在處理檔案: {file_name} ---")

        try:
            # --- 步驟 1: 判斷檔案類型 ---
            # 我們先用 pandas 快速讀取標頭 (skiprows=[1], header=0, nrows=0) 來判斷欄位
            print("正在讀取標頭以判斷檔案類型...")
            header_df = pd.read_csv(file_path, skiprows=[1], header=0, nrows=0, low_memory=False, on_bad_lines='skip')
            columns = set(header_df.columns)
            
            # 根據你提供的分析：
            # '臺鐵電子票證資料(TO2A).csv' 有 '卡號' 欄位
            # '臺鐵非電子票證資料.csv' 沒有 '卡號' 欄位，但有 '票面起站車站名稱'
            
            if '卡號' in columns and '刷卡進入車站名稱' in columns:
                # --- 類型 A: 臺鐵電子票證資料(TO1A / TO2A) ---
                print("偵測到 [電子票證] 格式...")
                dtype_ic = {'刷卡進入車站代碼': 'object', '刷卡離開車站代碼': 'object', '票種次類型': 'object'}
                df = reader.read_csv(file_path, dtype=dtype_ic, **read_csv_kwargs)
                
                df['人次'] = 1
                df = df.rename(columns={
                    '資料代表日期(yyyy-MM-dd)': '日期',
                    '刷卡進入車站時間': '進站時間',
                    '刷卡離開車站時間': '出站時間',
                    '電子票證卡種': '卡種',
                    '持卡身分': '身分',
                    '刷卡進入車站名稱': '起點',
                    '刷卡離開車站名稱': '迄點'
                })
                
                if isinstance(df, pd.DataFrame) and not config.TEST_MODE:
                    df = dd.from_pandas(df, npartitions=1)

                df['時段'] = dd.to_datetime(df['進站時間'], format='%Y-%m-%d %H:%M:%S', errors='coerce').dt.hour
                df['票證分類'] = 'IC'
                
                # 確保欄位一致
                required_cols = ['日期', '時段', '票證分類', '卡種', '身分', '起點', '迄點', '人次', '進站時間', '出站時間']
                # 補上可能缺少的欄位 (例如 '票種')
                if '票種' not in df.columns:
                    df['票種'] = 'N/A' 
                
                all_dfs.append(df[required_cols])
                print(f"成功載入: {file_name}")

            elif '票面起站車站名稱' in columns and '票面迄站車站名稱' in columns:
                # --- 類型 B: 臺鐵非電子票證資料 ---
                print("偵測到 [非電子票證] 格式...")
                dtype_non_ic = {'票面起站車站代碼': 'object', '票面迄站車站代碼': 'object', '票種次類型': 'object'}
                df = reader.read_csv(file_path, dtype=dtype_non_ic, **read_csv_kwargs)
                
                df['人次'] = 1
                df = df.rename(columns={
                    '乘車日期': '日期',
                    '票面起站車站名稱': '起點',
                    '票面迄站車站名稱': '迄點',
                    '票種類型': '票種'
                })
                
                if isinstance(df, pd.DataFrame) and not config.TEST_MODE:
                    df = dd.from_pandas(df, npartitions=1)
                    
                df['時段'] = dd.to_datetime(df['進站時間'], format='%Y-%m-%d %H:%M:%S', errors='coerce').dt.hour
                df['票證分類'] = 'N-IC'
                df['卡種'] = 'N/A'
                df['身分'] = 'N/A'
                
                # 確保欄位一致
                required_cols = ['日期', '時段', '票證分類', '卡種', '身分', '起點', '迄點', '人次', '進站時間', '出站時間']
                
                all_dfs.append(df[required_cols])
                print(f"成功載入: {file_name}")
                
            else:
                print(f"警告: 檔案 {file_name} 的欄位格式無法識別，將跳過。")
                
        except Exception as e:
            print(f"錯誤: 處理檔案 {file_name} 時發生問題: {e}，將跳過此檔案。")
            continue
        
    # --- 檔案迴圈結束 ---

    if not all_dfs:
        print("錯誤：所有資料檔案都處理失敗或格式無法識別，無法進行分析。")
        return None

    print("\n正在合併所有資料來源...")
    combined_df = dd.concat(all_dfs, ignore_index=True)
    
    # --- 後續處理 (與原版相同) ---
    print("正在進行最終資料清理與衍生欄位計算...")
    combined_df['日期'] = dd.to_datetime(combined_df['日期'], format='%Y-%m-%d', errors='coerce')
    combined_df['星期'] = combined_df['日期'].dt.weekday
    combined_df['日期類型'] = '平日'
    # 修正: Dask 的 mask 語法
    combined_df['日期類型'] = combined_df['日期類型'].mask(combined_df['星期'].isin([5, 6]), '假日')
    # 轉換為 category 類型以節省記憶體
    combined_df['日期類型'] = combined_df['日期類型'].astype('category').cat.set_categories(['平日', '假日'])
    
    print("資料準備完成！")
    
    print(f"\n--- 正在將清洗後的資料儲存至 '{output_filename}' ---")
    try:
        # 確保目標資料夾存在
        os.makedirs(os.path.dirname(output_filename), exist_ok=True)
        # 使用 Dask 的 to_csv 儲存為單一檔案
        combined_df.to_csv(output_filename, single_file=True, index=False, encoding='utf-8-sig')
        print(f"成功！資料已儲存至 '{os.path.abspath(output_filename)}'")
    except Exception as e:
        print(f"錯誤：儲存檔案時發生問題: {e}")
        
    return combined_df

if __name__ == '__main__':
    # *** 核心修改：main 執行時，使用 config 的路徑，而不是寫死在本地 ***
    final_df = load_and_save_data(output_filename=config.TRA_UNIFIED_DATA_FILE)
    
    if final_df is not None:
        print("\n--- 資料處理完成，以下為前 5 筆資料預覽 ---")
        # 使用 Dask 的 .head()
        print(final_df.head())