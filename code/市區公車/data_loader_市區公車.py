# 檔名: code/市區公車/data_loader_市區公車.py (V2)
# 功能: 專責讀取、解析、清理並整合所有來源的市區公車資料，
#       並根據資料格式文件 (PDF) 將代碼轉換為可讀文字。
# V2 更新: 新增了月份、星期、小時、日期類型、旅次時長等衍生欄位，並移除了司機與車號。
import pandas as pd
import os
import glob
import re
import sys

# --- 從 config.py 載入設定 ---
try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    import config
except ImportError:
    print("錯誤：無法找到 config.py。請確認您的專案結構。")
    sys.exit(1)

# =============================================================================
#  資料代碼對應 (根據 PDF 文件)
# =============================================================================
TICKET_TYPE_MAP = {'1': '單程票', '2': '來回票', '3': '回數票', '4': '定期票', '5': '團體票', '9': '其他'}
HOLDER_TYPE_MAP = {'A': '普通', 'B': '學生', 'C01': '敬老', 'CO2': '愛心', 'C09': '其他優待', 'D': '員工', 'X': '無法區別'}
DIRECTION_MAP = {'0': '去程', '1': '返程', '2': '迴圈'}

# =============================================================================
#  核心資料處理函式
# =============================================================================

def process_eticket_data(df):
    """ 處理新版「電子票證」資料 (TO2A 格式)。 """
    print("    - 偵測到 [電子票證] 格式，開始處理...")
    column_mapping = {
        '搭乘路線名稱': '路線', '卡號': '卡號', '持卡身分': '票種名稱',
        '搭乘公車路線方向': '往返程', '刷卡上車時間': '上車時間', '上車站牌名稱': '上車站名',
        '刷卡下車時間': '下車時間', '下車站牌名稱': '下車站名', '實際支付價格': '消費扣款'
    }
    df_renamed = df.rename(columns=column_mapping)
    df_renamed['票種名稱'] = df_renamed['票種名稱'].astype(str).map(HOLDER_TYPE_MAP).fillna('未知身分')
    df_renamed['往返程'] = df_renamed['往返程'].astype(str).map(DIRECTION_MAP)
    return df_renamed[list(column_mapping.values())]

def process_non_eticket_data(df):
    """ 處理新版「非電子票證」資料。 """
    print("    - 偵測到 [非電子票證] 格式，開始處理...")
    df['上車時間'] = pd.to_datetime(df['乘車日期'] + ' ' + df['乘車時間'], errors='coerce')
    column_mapping = {
        '搭乘路線名稱': '路線', '票種類型': '票種名稱', '搭乘公車路線方向': '往返程',
        '上車時間': '上車時間', '站牌或站位': '上車站名', '實際支付價格': '消費扣款'
    }
    df_renamed = df.rename(columns=column_mapping)
    df_renamed['票種名稱'] = df_renamed['票種名稱'].astype(str).map(TICKET_TYPE_MAP).fillna('未知票種')
    if '往返程' in df_renamed.columns:
        df_renamed['往返程'] = df_renamed['往返程'].astype(str).map(DIRECTION_MAP)
    else:
        df_renamed['往返程'] = '未提供'
    df_renamed['卡號'] = '無卡號'
    df_renamed['下車時間'] = pd.NaT
    df_renamed['下車站名'] = '未提供'
    final_cols = ['路線', '卡號', '票種名稱', '往返程', '上車時間', '上車站名', '下車時間', '下車站名', '消費扣款']
    return df_renamed[final_cols]

# =============================================================================
#  通用清理與特徵工程函式
# =============================================================================

def clean_and_enrich_data(df):
    """ 執行通用的資料清理與衍生欄位建立。 """
    print("\n正在執行通用資料清理與特徵工程...")

    # 1. 站名清理
    print("  - 清理站牌名稱...")
    for col in ['上車站名', '下車站名']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'^\d{2,}|[\(（].*?[\)）]|[\s=,-]', '', regex=True)

    # 2. 時間格式轉換與篩選
    print("  - 轉換時間格式...")
    df['上車時間'] = pd.to_datetime(df['上車時間'], errors='coerce')
    df['下車時間'] = pd.to_datetime(df['下車時間'], errors='coerce')
    original_rows = len(df)
    df.dropna(subset=['上車時間'], inplace=True)
    if original_rows > len(df):
        print(f"    - 移除了 {original_rows - len(df)} 筆 '上車時間' 無效的資料。")

    # 3. 標記不完整旅次
    print("  - 標記不完整旅次...")
    df['旅次是否完整'] = ~(
        df['下車時間'].isnull() | pd.isna(df['下車時間']) |
        df['下車站名'].isnull() | (df['下車站名'].astype(str).str.lower().isin(['', '0', 'nan', '未提供']))
    )
    df.loc[df['下車時間'] == df['上車時間'], '旅次是否完整'] = False

    # 4. 新增衍生欄位 (特徵工程)
    print("  - 新增分析用衍生欄位...")
    df['上車月份'] = df['上車時間'].dt.month
    df['上車星期'] = df['上車時間'].dt.dayofweek
    df['上車小時'] = df['上車時間'].dt.hour
    df['日期類型'] = df['上車星期'].apply(lambda x: '假日' if x >= 5 else '平日')
    
    # 計算旅次時長 (僅針對完整旅次)
    complete_trips_mask = df['旅次是否完整'] == True
    df.loc[complete_trips_mask, '旅次時長(分)'] = \
        (df.loc[complete_trips_mask, '下車時間'] - df.loc[complete_trips_mask, '上車時間']).dt.total_seconds() / 60
    df['旅次時長(分)'].fillna(0, inplace=True) # 將不完整旅次的時長填 0

    print("資料清理與特徵工程完成。")
    return df

# =============================================================================
#  主執行函式
# =============================================================================
def main():
    """ 主函式，讀取所有檔案並進行處理與清理。 """
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
            df = pd.read_csv(file, header=0, nrows=nrows_to_read, low_memory=False, on_bad_lines='skip')
            if df.columns[0] == 'Authority':
                 df = pd.read_csv(file, skiprows=[1], header=0, nrows=nrows_to_read, low_memory=False, on_bad_lines='skip')
        except Exception as e:
            print(f"  - 無法讀取檔案 {os.path.basename(file)}，錯誤訊息: {e}")
            continue

        try:
            processed_df = process_eticket_data(df) if '卡號' in df.columns else process_non_eticket_data(df)
            all_data.append(processed_df)
            print(f"    - 檔案 '{os.path.basename(file)}' 處理完成。")
        except Exception as e:
            print(f"    - 錯誤: 處理檔案 {os.path.basename(file)} 時發生錯誤: {e}")

    if not all_data:
        print("\n處理完成，但沒有產生任何有效資料。")
        return

    # --- 合併與最終處理 ---
    print("\n開始合併所有已處理的資料...")
    final_df = pd.concat(all_data, ignore_index=True)
    final_df = clean_and_enrich_data(final_df)
    
    # 最終輸出的欄位 (已移除司機、車號，並新增衍生欄位)
    TARGET_COLUMNS = [
        '路線', '卡號', '票種名稱', '往返程', '上車時間', '上車站名',
        '下車時間', '下車站名', '消費扣款', '旅次是否完整', '上車月份',
        '上車星期', '上車小時', '日期類型', '旅次時長(分)'
    ]
    for col in TARGET_COLUMNS:
        if col not in final_df.columns:
            final_df[col] = None
    final_df = final_df[TARGET_COLUMNS]
    
    output_filename = config.BUS_UNIFIED_DATA_FILE
    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
    
    final_df.to_csv(output_filename, index=False, encoding='utf-8-sig')
    print(f"\n✅ 資料已成功整合、清理並儲存至: {output_filename}")

if __name__ == '__main__':
    main()