# 檔名: code/公路客運/data_loader_公路客運.py
# 功能: 專責讀取、解析、清理並整合所有來源的公路客運資料，
#       並根據資料格式文件將代碼轉換為可讀文字。
# 說明: 此腳本的邏輯完全比照 data_loader_市區公車.py，
#       以確保資料處理的一致性。
# V2 : 新增 config 路線篩選功能
import pandas as pd
import os
import glob
import sys

# --- 從 config.py 載入設定 ---
try:
    # 從目前的 code/公路客運/ 目錄往上兩層找到專案根目錄
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    import config
except ImportError:
    print("錯誤：無法找到 config.py。請確認您的專案結構。")
    sys.exit(1)

# =============================================================================
#  資料代碼對應 (根據 PDF 文件)
# =============================================================================
TICKET_TYPE_MAP = {'1': '單程票', '2': '來回票', '3': '回數票', '4': '定期票', '5': '團體票', '9': '其他'}
HOLDER_TYPE_MAP = {'A': '普通', 'B': '學生', 'C01': '敬老', 'C02': '愛心', 'C09': '其他優待', 'D': '員工', 'X': '無法區別'}
DIRECTION_MAP = {'0': '去程', '1': '返程', '2': '迴圈'}

# =============================================================================
#  核心資料處理函式
# =============================================================================

def process_eticket_data(df):
    """ 處理「電子票證」資料 (TO2A 格式)。 """
    print("    - 偵測到 [電子票證] 格式，開始處理...")
    column_mapping = {
        '搭乘附屬路線名稱': '路線', '卡號': '卡號', '持卡身分': '持卡身分', '票種類型': '票種類型',
        '搭乘公車路線方向': '往返程', '刷卡上車時間': '上車時間', '上車站牌名稱': '上車站名',
        '刷卡下車時間': '下車時間', '下車站牌名稱': '下車站名', '實際支付價格': '消費扣款'
    }
    df_renamed = df.rename(columns=column_mapping)
    df_renamed['持卡身分'] = df_renamed['持卡身分'].astype(str).map(HOLDER_TYPE_MAP).fillna('未知身分')
    df_renamed['票種類型'] = df_renamed['票種類型'].astype(str).map(TICKET_TYPE_MAP).fillna('未知票種')
    df_renamed['往返程'] = df_renamed['往返程'].astype(str).map(DIRECTION_MAP)
    return df_renamed[list(column_mapping.values())]

def process_non_eticket_data(df):
    """ 處理「非電子票證」資料。 """
    print("    - 偵測到 [非電子票證] 格式，開始處理...")
    df['上車時間'] = pd.to_datetime(df['乘車日期'] + ' ' + df['乘車時間'], errors='coerce')
    column_mapping = {
        '搭乘附屬路線名稱': '路線', '票種類型': '票種類型', '搭乘公車路線方向': '往返程',
        '上車時間': '上車時間', '實際支付價格': '消費扣款'
    }
    df_renamed = df.rename(columns=column_mapping)
    df_renamed['票種類型'] = df_renamed['票種類型'].astype(str).map(TICKET_TYPE_MAP).fillna('未知票種')
    if '往返程' in df_renamed.columns:
        df_renamed['往返程'] = df_renamed['往返程'].astype(str).map(DIRECTION_MAP)
    else:
        df_renamed['往返程'] = '未提供'
    df_renamed['卡號'] = '非電子票證'
    df_renamed['上車站名'] = '非電子票證'
    df_renamed['下車時間'] = df_renamed['上車時間']  # 非電子票證無下車時間，暫時設為上車時間
    df_renamed['下車站名'] = '非電子票證'
    df_renamed['持卡身分'] = '非電子票證'
    final_cols = ['路線', '卡號', '持卡身分', '票種類型', '往返程', '上車時間', '上車站名', '下車時間', '下車站名', '消費扣款']
    return df_renamed[final_cols]

# =============================================================================
#  通用清理與特徵工程函式
# =============================================================================

def filter_by_validation_result(df):
    """只保留『檢核結果』欄位為 3 (完全通過) 的資料。"""
    validation_col = next((col for col in df.columns if '檢核結果' in col), None)
    if not validation_col:
        print("    - 未找到 '檢核結果' 欄位，保留所有資料。")
        return df

    validation_values = pd.to_numeric(df[validation_col], errors='coerce')
    before_rows = len(df)
    df = df[validation_values == 3].copy()
    removed_rows = before_rows - len(df)

    if removed_rows > 0:
        print(f"    - 已根據 '檢核結果' 篩除 {removed_rows} 筆未通過資料。")
    else:
        print("    - 所有資料皆通過檢核。")

    if df.empty:
        print("    - 警告：依檢核結果篩選後沒有資料可用。")

    return df

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

    # 3. 標記不完整旅次 (*** 這是修改後的區塊 ***)
    print("  - 標記不完整旅次...")
    
    # 找出電子票證的資料 (持卡身分 '非電子票證' 是在 process_non_eticket_data 中設定的)
    is_eticket_mask = (df['持卡身分'] != '非電子票證')

    # 1. 預設所有旅次為 True (包含所有 '非電子票證' 資料)
    df['旅次是否完整'] = True

    # 2. 找出電子票證中「不完整」的條件
    # 條件1: 下車時間為空
    condition_no_alight_time = df['下車時間'].isnull() | pd.isna(df['下車時間'])
    # 條件2: 下車站名為空或無效
    condition_no_alight_stop = df['下車站名'].isnull() | (df['下車站名'].astype(str).str.lower().isin(['', '0', 'nan', '未提供']))

    # 3. 結合所有不完整的條件
    is_incomplete_eticket = (condition_no_alight_time | condition_no_alight_stop)
    
    # 4. 只在「電子票證」資料上 (is_eticket_mask)，將「不完整」的旅次 (is_incomplete_eticket) 設為 False
    df.loc[is_eticket_mask & is_incomplete_eticket, '旅次是否完整'] = False
    # (*** 修改區塊結束 ***)


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
    # 將不完整旅次(包含非電子票證)的時長填 0
    # (備註: 非電子票證的旅次時長在此邏輯下也會是 0，因為它們的 complete_trips_mask 是 True，
    # 但 process_non_eticket_data 中設定了 下車時間 == 上車時間)
    df['旅次時長(分)'].fillna(0, inplace=True) 

    print("資料清理與特徵工程完成。")
    return df

# =============================================================================
#  主執行函式
# =============================================================================
def main():
    """ 主函式，讀取所有公路客運檔案並進行處理與清理。 """
    nrows_to_read = config.TEST_MODE_ROWS if config.TEST_MODE else None
    if config.TEST_MODE:
        print(f"--- [測試模式已啟用] ---\n所有檔案將只讀取前 {nrows_to_read} 行。\n" + "-"*26 + "\n")
        
    data_dir = config.HIGHWAY_BUS_RAW_DATA_DIR
    files = glob.glob(os.path.join(data_dir, '*.csv'))
    
    if not files:
        print(f"錯誤：在 '{data_dir}' 資料夾中找不到任何 .csv 檔案。")
        return
        
    # *** 新增：檢查 config 中是否有篩選清單 ***
    target_routes = config.HIGHWAY_BUS_TARGET_ROUTES
    if target_routes:
        print(f"--- [路線篩選已啟用] ---\n將只保留以下 {len(target_routes)} 條路線的資料：")
        print(f"{', '.join(target_routes)}\n" + "-"*26 + "\n")
    else:
        print("--- [路線篩選未啟用] ---\n將處理所有偵測到的路線資料。\n" + "-"*26 + "\n")


    all_data = [] # 用於收集所有檔案處理完的最終 DataFrame
    
    for file in files:
        print(f"正在處理檔案: {os.path.basename(file)}")
        
        # *** 核心修改：使用 chunksize 解決記憶體不足問題 ***
        try:
            # 設定每個區塊的行數。
            # 如果是測試模式，nrows_to_read 依然會生效。
            # 如果不是測試模式，我們會一次處理 500,000 筆。
            chunk_size_to_use = 500000
            
            # 用於收集單一檔案中，所有已處理完畢的區塊
            processed_chunks_for_this_file = []
            
            # 準備 read_csv 的共用參數
            iterator_kwargs = {
                'header': 0, 
                'nrows': nrows_to_read, 
                'low_memory': False, 
                'on_bad_lines': 'skip'
            }
            
            # 檢查是否有 'Authority' 標頭問題
            try:
                # 預讀第一行來檢查欄位
                temp_df_check = pd.read_csv(file, header=0, nrows=1, low_memory=False, on_bad_lines='skip')
                if temp_df_check.columns[0] == 'Authority':
                    print("    - 偵測到 'Authority' 標頭，將自動跳過第二行。")
                    iterator_kwargs['skiprows'] = [1]
            except Exception as e:
                print(f"  - 警告：預讀檔案標頭失敗 ({e})，將使用預設方式讀取。")

            print(f"    - 開始以 {chunk_size_to_use} 筆為單位分批讀取...")

            # 使用 with pd.read_csv(...) as reader: 來建立一個迭代器
            with pd.read_csv(file, chunksize=chunk_size_to_use, **iterator_kwargs) as reader:
                
                for i, df_chunk in enumerate(reader):
                    print(f"    - 正在處理第 {i+1} 區塊 (大小: {len(df_chunk)} 筆)...")
                    
                    try:
                        # --- 套用你原有的處理邏輯 ---
                        # 1. 檢核篩選
                        df_chunk = filter_by_validation_result(df_chunk)
                        if df_chunk.empty:
                            print(f"      - 區塊 {i+1} 在檢核篩選後沒有資料，跳過。")
                            continue
                        
                        # 2. 格式處理
                        processed_df_chunk = process_eticket_data(df_chunk) if '卡號' in df_chunk.columns else process_non_eticket_data(df_chunk)
                        
                        # 3. 路線篩選
                        if target_routes:
                            original_rows = len(processed_df_chunk)
                            # 確保 '路線' 欄位是字串型別，以便比對
                            processed_df_chunk['路線'] = processed_df_chunk['路線'].astype(str)
                            processed_df_chunk = processed_df_chunk[processed_df_chunk['路線'].isin(target_routes)]
                            filtered_rows = len(processed_df_chunk)
                            
                            if original_rows > filtered_rows:
                                print(f"      - 已根據 config 篩選路線，此區塊資料從 {original_rows} 筆減少至 {filtered_rows} 筆。")
                        
                        # 4. 加入列表 (僅在篩選後仍有資料時才加入)
                        if not processed_df_chunk.empty:
                            processed_chunks_for_this_file.append(processed_df_chunk)
                            
                    except Exception as e:
                        print(f"    - 錯誤: 處理區塊 {i+1} 時發生錯誤: {e}")
                        print("      - 將跳過此錯誤區塊並繼續處理下一個...")
            
            # --- 區塊處理迴圈結束 ---

            # 如果這個檔案有產生任何處理過的區塊，才將它們合併起來
            if processed_chunks_for_this_file:
                print(f"    - 正在合併檔案 '{os.path.basename(file)}' 的所有已處理區塊...")
                all_data.append(pd.concat(processed_chunks_for_this_file, ignore_index=True))
                print(f"    - 檔案 '{os.path.basename(file)}' 處理完成。")
            else:
                print(f"    - 檔案 '{os.path.basename(file)}' 處理完成，但未產生任何有效資料。")

        except Exception as e:
            # 捕捉讀取檔案時的致命錯誤 (例如檔案不存在或完全無法解析)
            print(f"  - 無法讀取檔案 {os.path.basename(file)}，錯誤訊息: {e}")
            continue
    
    # --- 檔案迴圈結束 ---

    if not all_data:
        print("\n處理完成，但沒有產生任何有效資料 (可能所有資料都已被篩選掉)。")
        return

    # --- 合併與最終處理 (此處邏輯不變) ---
    print("\n開始合併所有已處理的資料...")
    final_df = pd.concat(all_data, ignore_index=True)
    final_df = clean_and_enrich_data(final_df)
    
    # 最終輸出的欄位 (已移除司機、車號，並新增衍生欄位)
    TARGET_COLUMNS = [
        '路線', '卡號', '持卡身分', '票種類型', '往返程', '上車時間', '上車站名',
        '下車時間', '下車站名', '消費扣款', '旅次是否完整', '上車月份',
        '上車星期', '上車小時', '日期類型', '旅次時長(分)'
    ]
    for col in TARGET_COLUMNS:
        if col not in final_df.columns:
            final_df[col] = None
    final_df = final_df[TARGET_COLUMNS]
    
    if hasattr(config, 'HIGHWAY_BUS_UNIFIED_DATA_FILE'):
        output_filename = config.HIGHWAY_BUS_UNIFIED_DATA_FILE
    else:
        print("警告：config.py 中未找到 'HIGHWAY_BUS_UNIFIED_DATA_FILE' 設定。")
        output_filename = os.path.join(os.path.dirname(__file__), 'unified_highway_bus_data.csv')
        print(f"將使用預設路徑：{output_filename}")

    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
    
    final_df.to_csv(output_filename, index=False, encoding='utf-8-sig')
    print(f"\n公路客運資料已成功整合、清理並儲存至: {output_filename}")
    print(f"最終整合資料筆數: {len(final_df)}")

if __name__ == '__main__':
    main()