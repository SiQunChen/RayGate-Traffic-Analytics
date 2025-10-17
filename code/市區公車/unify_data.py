# 檔名: code/市區公車/unify_data.py (V2 - 支援花蓮新格式)
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

# 目標欄位
TARGET_COLUMNS = [
    '路線', '司機', '車號', '卡號', '票種名稱', '往返程', '上車時間',
    '上車站名', '下車時間', '下車站名', '消費扣款', '旅次是否完整'
]

# --- 新增：處理花蓮電子票證格式 (TO2A) ---
def process_hualien_eticket(df):
    """
    處理花蓮縣公車電子票證資料(TO2A) 的 CSV 格式。
    """
    column_mapping = {
        '搭乘路線名稱': '路線',
        '卡號': '卡號',
        '持卡身分': '票種名稱', # 優先使用 '持卡身分'
        '搭乘公車路線方向': '往返程',
        '刷卡上車時間': '上車時間',
        '上車站牌名稱': '上車站名',
        '刷卡下車時間': '下車時間',
        '下車站牌名稱': '下車站名',
        '實際支付價格': '消費扣款'
    }
    
    # 如果 '持卡身分' 為空，則改用 '電子票證卡種'
    if '持卡身分' not in df.columns or df['持卡身分'].isnull().all():
        column_mapping['電子票證卡種'] = '票種名稱'
        
    df_renamed = df.rename(columns=column_mapping)
    
    # 補上缺少的欄位
    df_renamed['司機'] = None
    df_renamed['車號'] = None # 新資料無車號資訊
    
    return df_renamed[column_mapping.values()]

# --- 新增：處理花蓮非電子票證格式 ---
def process_hualien_non_eticket(df):
    """
    處理花蓮縣公車非電子票證資料的 CSV 格式。
    """
    df['上車時間'] = pd.to_datetime(df['乘車日期'] + ' ' + df['乘車時間'], errors='coerce')
    
    column_mapping = {
        '搭乘路線名稱': '路線',
        '票種類型': '票種名稱',
        '搭乘公車路線方向': '往返程',
        '上車時間': '上車時間',
        '站牌或站位': '上車站名', # 假設此為上車站
        '實際支付價格': '消費扣款'
    }
    
    df_renamed = df.rename(columns=column_mapping)
    
    # 補上缺少的欄位 (此格式無下車資訊)
    df_renamed['司機'] = None
    df_renamed['車號'] = df_renamed['車次代碼'] # 使用車次代碼作為車號
    df_renamed['卡號'] = None # 非電子票證無卡號
    df_renamed['下車時間'] = pd.NaT
    df_renamed['下車站名'] = None
    
    return df_renamed[column_mapping.values()]


# --- (process_format_1, process_format_2, process_format_3 等舊函式保持不變) ---
def process_format_1(df):
    """
    處理格式1 (例如: 101, 102, 201號路線)
    """
    columns_to_select = {
        '路線': '路線', '司機': '司機', '車號': '車號', '卡號': '卡號',
        '票種名稱': '票種名稱', '往返程': '往返程', '上車時間': '上車時間',
        '上車站名': '上車站名', '下車時間': '下車時間', '下車站名': '下車站名',
        '消費扣款': '消費扣款'
    }
    if '人數' in df.columns:
        columns_to_select['人數'] = '人數'
    df_selected = df[list(columns_to_select.keys())]
    df_renamed = df_selected.rename(columns=columns_to_select)
    return df_renamed

def process_format_2(df):
    """
    處理格式2 (例如: 202, 203號路線)
    """
    cols = pd.Series(df.columns)
    for dup in cols[cols.duplicated()].unique():
        cols[cols[cols == dup].index.values.tolist()] = [dup + '.' + str(i) if i != 0 else dup for i in range(sum(cols == dup))]
    df.columns = cols

    column_mapping = {
        '路線別': '路線', '司機': '司機', '車牌': '車號', '卡號': '卡號',
        '卡種': '票種名稱', '去返程': '往返程', '上車時間': '上車時間',
        '上車站名': '上車站名', '下車時間': '下車時間', '下車站名': '下車站名'
    }
    df['消費扣款'] = pd.to_numeric(df['上車扣款'], errors='coerce').fillna(0) + \
                   pd.to_numeric(df['下車扣款'], errors='coerce').fillna(0)

    df_selected = df[list(column_mapping.keys()) + ['消費扣款']]
    df_renamed = df_selected.rename(columns=column_mapping)
    return df_renamed

def process_format_3(df):
    """
    處理格式3 (例如: 205, 301, 701號路線)
    """
    df.columns = df.columns.str.replace('\n', '', regex=False)
    date_series = pd.to_datetime(df['營運日期'], errors='coerce').dt.strftime('%Y-%m-%d')
    on_time_series = pd.to_datetime(df['上車時間'], format='%H:%M:%S', errors='coerce').dt.strftime('%H:%M:%S')
    off_time_series = pd.to_datetime(df['下車時間'], format='%H:%M:%S', errors='coerce').dt.strftime('%H:%M:%S')

    full_on_time = date_series.astype(str) + ' ' + on_time_series.astype(str)
    full_off_time = date_series.astype(str) + ' ' + off_time_series.astype(str)

    df['上車時間_完整'] = pd.to_datetime(full_on_time, format='%Y-%m-%d %H:%M:%S', errors='coerce')
    df['下車時間_完整'] = pd.to_datetime(full_off_time, format='%Y-%m-%d %H:%M:%S', errors='coerce')

    direction_map = { 1: '往程', 2: '返程' }
    df['去返'] = pd.to_numeric(df['去返'], errors='coerce').map(direction_map)

    column_mapping = {
        '路線': '路線', '駕駛員': '司機', '車輛': '車號', '卡號': '卡號',
        '卡種': '票種名稱', '去返': '往返程', '上車時間_完整': '上車時間',
        '上車站': '上車站名', '下車時間_完整': '下車時間', '下車站': '下車站名',
        '扣款金額': '消費扣款'
    }
    required_original_cols = ['路線', '駕駛員', '車輛', '卡號', '卡種', '去返', '上車站', '下車站', '扣款金額']
    df_selected = df[required_original_cols + ['上車時間_完整', '下車時間_完整']]
    df_renamed = df_selected.rename(columns=column_mapping)
    return df_renamed

def mark_incomplete_trips(df):
    print("正在標記不完整旅次...")
    df['旅次是否完整'] = ~(df['下車時間'].isnull() | pd.isna(df['下車時間']) |
                       df['下車站名'].isnull() | (df['下車站名'] == '0') | (df['下車站名'] == 'nan'))
    # 如果下車時間等於上車時間，也視為不完整
    df['旅次是否完整'] = df['旅次是否完整'] & (df['下車時間'] != df['上車時間'])
    return df

def normalize_station_names(df):
    print("正在進行站名清理...")
    station_columns = ['上車站名', '下車站名']
    for col in station_columns:
        df[col] = df[col].astype(str).fillna('')
        df[col] = df[col].apply(lambda x: re.sub(r'^\d{2,}|[\(（].*?[\)）]|[\s=,-]', '', x))
    print("站名正規化完成。")
    return df


def main():
    """
    主函式，讀取所有檔案並進行處理與清理
    """
    nrows_to_read = config.TEST_MODE_ROWS if config.TEST_MODE else None
    if config.TEST_MODE:
        print(f"--- [測試模式已啟用] ---\n所有檔案將只讀取前 {nrows_to_read} 行。\n--------------------------\n")
        
    data_dir = config.BUS_RAW_DATA_DIR
    # *** 核心修改：同時搜尋 .xlsx 和 .csv 檔案 ***
    files = glob.glob(os.path.join(data_dir, '*.xlsx')) + glob.glob(os.path.join(data_dir, '*.csv'))
    
    if not files:
        print(f"錯誤：在 '{data_dir}' 資料夾中找不到任何 .xlsx 或 .csv 檔案。")
        return

    all_data = []
    for file in files:
        print(f"正在處理檔案: {os.path.basename(file)}")
        
        # --- 根據副檔名選擇讀取方式 ---
        is_csv = file.endswith('.csv')
        try:
            if is_csv:
                # *** 核心修改：讀取 CSV 檔案 ***
                # 先只讀取表頭，用於格式判斷
                header_df = pd.read_csv(file, nrows=1, encoding='utf-8', on_bad_lines='skip')
                # 移除第一行可能是英文標題的情況
                if header_df.iloc[0,0] == 'Authority':
                    df = pd.read_csv(file, skiprows=[1], header=0, nrows=nrows_to_read, encoding='utf-8', on_bad_lines='skip')
                else:
                    df = pd.read_csv(file, nrows=nrows_to_read, encoding='utf-8', on_bad_lines='skip')
            else: # 處理 Excel
                xls = pd.ExcelFile(file)
                # (處理 Excel 的邏輯保持不變，此處為簡化版，實際執行時應包含完整邏輯)
                sheet_name = xls.sheet_names[0]
                df = pd.read_excel(file, sheet_name=sheet_name, nrows=nrows_to_read)

        except Exception as e:
            print(f"  - 無法讀取檔案 {os.path.basename(file)}，錯誤訊息: {e}")
            continue

        print(f"    - {os.path.basename(file)} 共 {len(df)} 筆資料")
        processed_df = None
        try:
            # *** 核心修改：新的格式判斷邏輯 ***
            if '刷卡上車時間' in df.columns and '卡號' in df.columns:
                print("    - 偵測到 [花蓮電子票證] 格式...")
                processed_df = process_hualien_eticket(df)
            elif '站牌或站位' in df.columns and '卡號' not in df.columns:
                print("    - 偵測到 [花蓮非電子票證] 格式...")
                processed_df = process_hualien_non_eticket(df)
            elif '路線' in df.columns and '票種名稱' in df.columns:
                print("    - 偵測到 [舊格式 1]...")
                processed_df = process_format_1(df)
            elif '路線別' in df.columns and '卡種' in df.columns:
                print("    - 偵測到 [舊格式 2]...")
                processed_df = process_format_2(df)
            elif '駕駛員' in df.columns and '車輛' in df.columns:
                print("    - 偵測到 [舊格式 3]...")
                processed_df = process_format_3(df)
            else:
                print(f"    - 警告: 無法識別檔案 {os.path.basename(file)} 的格式，已跳過。")
                continue
                
            all_data.append(processed_df)
        except Exception as e:
            print(f"    - 錯誤: 處理檔案 {os.path.basename(file)} 時發生錯誤: {e}")


    if all_data:
        print("\n開始合併所有已處理的資料...")
        final_df = pd.concat(all_data, ignore_index=True)
        
        # --- 後續清理流程 ---
        final_df = normalize_station_names(final_df)
        final_df = mark_incomplete_trips(final_df)
        
        print("\n正在轉換時間格式並篩選資料...")
        final_df['上車時間'] = pd.to_datetime(final_df['上車時間'], errors='coerce')
        final_df['下車時間'] = pd.to_datetime(final_df['下車時間'], errors='coerce')

        original_rows = len(final_df)
        final_df.dropna(subset=['上車時間'], inplace=True)
        if original_rows > len(final_df):
            print(f"  - 已移除 {original_rows - len(final_df)} 筆 '上車時間' 格式不正確或為空的資料。")
        
        # (可選) 如果需要，可以加入日期篩選
        # final_df = final_df[final_df['上車時間'] >= '2024-01-01'].copy()
        print(f"篩選完成，剩下 {len(final_df)} 筆有效資料。")
        
        # 確保所有目標欄位都存在
        for col in TARGET_COLUMNS:
            if col not in final_df.columns:
                final_df[col] = None
        final_df = final_df[TARGET_COLUMNS]
        
        output_filename = config.BUS_UNIFIED_DATA_FILE
        os.makedirs(os.path.dirname(output_filename), exist_ok=True)
        
        final_df.to_csv(output_filename, index=False, encoding='utf-8-sig')
        print(f"\n資料已成功合併、清理、篩選並儲存至 {output_filename}")
    else:
        print("\n處理完成，但沒有產生任何資料。請檢查您的檔案內容與格式。")

if __name__ == '__main__':
    main()