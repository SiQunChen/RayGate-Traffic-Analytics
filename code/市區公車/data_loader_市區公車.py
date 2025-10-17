# 檔名: code/市區公車/data_loader_市區公車.py
# 功能: 專責讀取、解析、清理並整合所有來源的市區公車資料，
#       並根據資料格式文件 (PDF) 將代碼轉換為可讀文字。
import pandas as pd
import os
import glob
import re
import sys

# --- 從 config.py 載入設定 ---
try:
    # 將專案根目錄加到 Python 路徑中
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    import config
except ImportError:
    print("錯誤：無法找到 config.py。請確認您的專案結構。")
    sys.exit(1)

# =============================================================================
#  資料代碼對應 (根據 PDF 文件)
# =============================================================================

# 票種類型對應 (來源: PDF P.2 & P.9)
TICKET_TYPE_MAP = {
    '1': '單程票', '2': '來回票', '3': '回數票',
    '4': '定期票', '5': '團體票', '9': '其他'
}

# 身分別對應 (來源: PDF P.1)
HOLDER_TYPE_MAP = {
    'A': '普通', 'B': '學生', 'C01': '敬老', 'CO2': '愛心',
    'C09': '其他優待', 'D': '員工', 'X': '無法區別'
}

# 路線方向對應 (來源: PDF P.2 & P.9)
DIRECTION_MAP = {
    '0': '去程', '1': '返程', '2': '迴圈'
}

# =============================================================================
#  核心資料處理函式
# =============================================================================

def process_eticket_data(df):
    """
    處理新版「電子票證」資料 (TO2A 格式)。
    """
    print("    - 偵測到 [電子票證] 格式，開始處理...")
    # 欄位重新命名
    column_mapping = {
        '搭乘路線名稱': '路線',
        '卡號': '卡號',
        '持卡身分': '票種名稱',
        '搭乘公車路線方向': '往返程',
        '刷卡上車時間': '上車時間',
        '上車站牌名稱': '上車站名',
        '刷卡下車時間': '下車時間',
        '下車站牌名稱': '下車站名',
        '實際支付價格': '消費扣款'
    }
    df_renamed = df.rename(columns=column_mapping)

    # --- 代碼轉換 ---
    # 將 '持卡身分' 代碼轉換為中文名稱
    df_renamed['票種名稱'] = df_renamed['票種名稱'].astype(str).map(HOLDER_TYPE_MAP).fillna('未知身分')
    # 將 '搭乘公車路線方向' 代碼轉換為中文名稱
    df_renamed['往返程'] = df_renamed['往返程'].astype(str).map(DIRECTION_MAP)

    # 補上缺少的標準欄位
    df_renamed['司機'] = '未提供'
    df_renamed['車號'] = '未提供'
    
    # 選取最終需要的欄位
    final_cols = list(column_mapping.values()) + ['司機', '車號']
    return df_renamed[final_cols]

def process_non_eticket_data(df):
    """
    處理新版「非電子票證」資料。
    """
    print("    - 偵測到 [非電子票證] 格式，開始處理...")
    # 組合日期與時間
    df['上車時間'] = pd.to_datetime(df['乘車日期'] + ' ' + df['乘車時間'], errors='coerce')
    
    # 欄位重新命名
    column_mapping = {
        '搭乘路線名稱': '路線',
        '票種類型': '票種名稱',
        '搭乘公-車路線方向': '往返程', # 修正原始欄位名稱中的潛在錯誤
        '搭乘公車路線方向': '往返程',   # 增加一個可能的正確欄位名稱
        '上車時間': '上車時間',
        '站牌或站位': '上車站名',
        '實際支付價格': '消費扣款',
        '車次代碼': '車號'
    }
    # 篩選出實際存在的欄位進行重新命名
    existing_cols_mapping = {k: v for k, v in column_mapping.items() if k in df.columns}
    df_renamed = df.rename(columns=existing_cols_mapping)
    
    # --- 代碼轉換 ---
    df_renamed['票種名稱'] = df_renamed['票種名稱'].astype(str).map(TICKET_TYPE_MAP).fillna('未知票種')
    if '往返程' in df_renamed.columns:
        df_renamed['往返程'] = df_renamed['往返程'].astype(str).map(DIRECTION_MAP)
    else:
        df_renamed['往返程'] = '未提供'

    # 補上缺少的標準欄位
    df_renamed['司機'] = '未提供'
    df_renamed['卡號'] = '無卡號'
    df_renamed['下車時間'] = pd.NaT
    df_renamed['下車站名'] = '未提供'
    
    # 選取最終需要的欄位
    final_cols = ['路線', '司機', '車號', '卡號', '票種名稱', '往返程', 
                  '上車時間', '上車站名', '下車時間', '下車站名', '消費扣款']
    return df_renamed[final_cols]

# =============================================================================
#  通用清理函式
# =============================================================================

def mark_incomplete_trips(df):
    """
    標記沒有下車時間或下車站名的旅次為不完整。
    """
    print("正在標記不完整旅次...")
    df['旅次是否完整'] = ~(
        df['下車時間'].isnull() | pd.isna(df['下車時間']) |
        df['下車站名'].isnull() | (df['下車站名'].astype(str).str.lower().isin(['', '0', 'nan', '未提供']))
    )
    # 如果下車時間等於上車時間，也視為不完整
    df.loc[df['下車時間'] == df['上車時間'], '旅次是否完整'] = False
    return df

def normalize_station_names(df):
    """
    清理站牌名稱，移除括號、多餘空格等。
    """
    print("正在進行站名清理...")
    station_columns = ['上車站名', '下車站名']
    for col in station_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'^\d{2,}|[\(（].*?[\)）]|[\s=,-]', '', regex=True)
    print("站名正規化完成。")
    return df

# =============================================================================
#  主執行函式
# =============================================================================

def main():
    """
    主函式，讀取所有檔案並進行處理與清理。
    """
    # 讀取 config 中的設定
    nrows_to_read = config.TEST_MODE_ROWS if config.TEST_MODE else None
    if config.TEST_MODE:
        print(f"--- [測試模式已啟用] ---\n所有檔案將只讀取前 {nrows_to_read} 行。\n" + "-"*26 + "\n")
        
    data_dir = config.BUS_RAW_DATA_DIR
    files = glob.glob(os.path.join(data_dir, '*.csv'))
    
    if not files:
        print(f"錯誤：在 '{data_dir}' 資料夾中找不到任何 .csv 檔案。")
        return

    all_data = []
    for file in files:
        print(f"正在處理檔案: {os.path.basename(file)}")
        try:
            # 移除 CSV 檔案中可能存在的英文標頭
            df = pd.read_csv(file, header=0, nrows=nrows_to_read, low_memory=False, on_bad_lines='skip')
            if df.columns[0] == 'Authority':
                 df = pd.read_csv(file, skiprows=[1], header=0, nrows=nrows_to_read, low_memory=False, on_bad_lines='skip')
        except Exception as e:
            print(f"  - 無法讀取檔案 {os.path.basename(file)}，錯誤訊息: {e}")
            continue

        processed_df = None
        try:
            # 核心判斷：有 '卡號' 欄位的是電子票證，沒有的則為非電子票證
            if '卡號' in df.columns:
                processed_df = process_eticket_data(df)
            else:
                processed_df = process_non_eticket_data(df)
                
            all_data.append(processed_df)
            print(f"    - 檔案 '{os.path.basename(file)}' 處理完成。")
        except Exception as e:
            print(f"    - 錯誤: 處理檔案 {os.path.basename(file)} 時發生錯誤: {e}")

    if not all_data:
        print("\n處理完成，但沒有產生任何有效資料。請檢查您的檔案內容與格式。")
        return

    # --- 合併與最終清理 ---
    print("\n開始合併所有已處理的資料...")
    final_df = pd.concat(all_data, ignore_index=True)
    
    final_df = normalize_station_names(final_df)
    final_df = mark_incomplete_trips(final_df)
    
    print("\n正在轉換時間格式並篩選無效資料...")
    final_df['上車時間'] = pd.to_datetime(final_df['上車時間'], errors='coerce')
    final_df['下車時間'] = pd.to_datetime(final_df['下車時間'], errors='coerce')

    original_rows = len(final_df)
    final_df.dropna(subset=['上車時間'], inplace=True)
    if original_rows > len(final_df):
        print(f"  - 已移除 {original_rows - len(final_df)} 筆 '上車時間' 為空的資料。")
    
    print(f"篩選完成，剩下 {len(final_df)} 筆有效資料。")
    
    # 確保所有目標欄位都存在
    TARGET_COLUMNS = [
        '路線', '司機', '車號', '卡號', '票種名稱', '往返程', '上車時間',
        '上車站名', '下車時間', '下車站名', '消費扣款', '旅次是否完整'
    ]
    for col in TARGET_COLUMNS:
        if col not in final_df.columns:
            final_df[col] = None # 如果缺少則補上空值
    final_df = final_df[TARGET_COLUMNS] # 確保欄位順序一致
    
    output_filename = config.BUS_UNIFIED_DATA_FILE
    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
    
    final_df.to_csv(output_filename, index=False, encoding='utf-8-sig')
    print(f"\n✅ 資料已成功合併、清理、轉換並儲存至: {output_filename}")

if __name__ == '__main__':
    main()