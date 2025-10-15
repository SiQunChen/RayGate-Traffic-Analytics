# data_loader.py (已修正為正確的時間格式並新增存檔功能)

import dask.dataframe as dd
import os # 匯入 os 模組來處理檔案路徑

def load_and_save_data(output_filename='cleaned_tra_data.csv'):
    """
    讀取、清理、整合所有四個臺鐵資料集，並將結果儲存成一個 CSV 檔。
    
    Args:
        output_filename (str): 清洗後要儲存的 CSV 檔案名稱。
    """
    print("--- 開始載入並整合所有資料來源 ---")
    all_dfs = []

    # --- 檔案1 & 2: 臺鐵每日各站分時OD資料 (O & D) ---
    # od_files = ['臺鐵每日各站分時OD資料(O).csv', '臺鐵每日各站分時OD資料(D).csv']
    # for f in od_files:
    #     try:
    #         ddf = dd.read_csv(f, skiprows=[1], header=0, 
    #                           dtype={'起站代碼': 'object', '迄站代碼': 'object', '票種次類型': 'object'})
    #         ddf = ddf.rename(columns={
    #             '旅次日期': '日期',
    #             '旅次時段(Ex: 12表示為12時00分至12時59分)': '時段',
    #             '票證分類 (N-IC: 非電子票證; IC: 電子票證)': '票證分類',
    #             '電子票證卡種': '卡種',
    #             '持卡身分': '身分',
    #             '起站中文名稱': '起點',
    #             '迄站中文名稱': '迄點',
    #             '旅運量': '人次'
    #         })
    #         ddf = ddf[ddf['時段'] != -99]
    #         all_dfs.append(ddf[['日期', '時段', '票證分類', '卡種', '身分', '起點', '迄點', '人次']])
    #         print(f"成功載入: {f}")
    #     except FileNotFoundError:
    #         print(f"警告: 找不到檔案 {f}，將跳過。")

    # --- 檔案3: 臺鐵非電子票證資料 ---
    non_ic_file = '臺鐵非電子票證資料.csv'
    try:
        ddf = dd.read_csv(non_ic_file, skiprows=[1], header=0,
                          dtype={'票面起站車站代碼': 'object', '票面迄站車站代碼': 'object', '票種次類型': 'object'})
        ddf['人次'] = 1
        ddf = ddf.rename(columns={'乘車日期': '日期','票面起站車站名稱': '起點','票面迄站車站名稱': '迄點','票種類型': '票種'})
        correct_format = '%Y-%m-%d %H:%M:%S'
        
        print(f"\n>>> 正在檢查 '{non_ic_file}' 中的 '進站時間' 欄位格式...")
        is_bad_time = dd.to_datetime(ddf['進站時間'], format=correct_format, errors='coerce').isna()
        if is_bad_time.any().compute():
            print(f"警告: 在檔案 '{non_ic_file}' 中找到無法解析為 '{correct_format}' 格式的時間資料。")
            bad_rows_df = ddf[is_bad_time]
            print("--- 以下為問題資料範例 (最多顯示前 5 筆) ---")
            print(bad_rows_df[['日期', '起點', '迄點', '進站時間']].head())
            print("------------------------------------------")
        else:
            print(f"'{non_ic_file}' 中的時間格式皆符合預期。")

        ddf['時段'] = dd.to_datetime(ddf['進站時間'], format=correct_format, errors='coerce').dt.hour
        ddf['票證分類'] = 'N-IC'
        ddf['卡種'] = 'N/A'
        ddf['身分'] = 'N/A'
        all_dfs.append(ddf[['日期', '時段', '票證分類', '卡種', '身分', '起點', '迄點', '人次', '進站時間', '出站時間']])
        print(f"成功載入: {non_ic_file}")
    except FileNotFoundError:
        print(f"警告: 找不到檔案 {non_ic_file}，將跳過。")

    # --- 檔案4: 臺鐵電子票證資料(TO1A) ---
    ic_file = '臺鐵電子票證資料(TO1A).csv'
    try:
        ddf = dd.read_csv(ic_file, skiprows=[1], header=0,
                          dtype={'刷卡進入車站代碼': 'object', '刷卡離開車站代碼': 'object', '票種次類型': 'object'})
        ddf['人次'] = 1
        ddf = ddf.rename(columns={'資料代表日期(yyyy-MM-dd)': '日期','刷卡進入車站時間': '進站時間','刷卡離開車站時間': '出站時間','電子票證卡種': '卡種','持卡身分': '身分','刷卡進入車站名稱': '起點','刷卡離開車站名稱': '迄點'})
        correct_format = '%Y-%m-%d %H:%M:%S'

        print(f"\n>>> 正在檢查 '{ic_file}' 中的 '進站時間' 欄位格式...")
        is_bad_time_ic = dd.to_datetime(ddf['進站時間'], format=correct_format, errors='coerce').isna()
        if is_bad_time_ic.any().compute():
            print(f"警告: 在檔案 '{ic_file}' 中找到無法解析為 '{correct_format}' 格式的進站時間資料。")
            bad_rows_df_ic = ddf[is_bad_time_ic]
            print("--- 以下為問題資料範例 (最多顯示前 5 筆) ---")
            print(bad_rows_df_ic[['日期', '起點', '迄點', '進站時間', '出站時間']].head())
            print("------------------------------------------")
        else:
            print(f"'{ic_file}' 中的時間格式皆符合預期。")

        ddf['時段'] = dd.to_datetime(ddf['進站時間'], format=correct_format, errors='coerce').dt.hour
        ddf['票證分類'] = 'IC'
        ddf_with_travel_time = ddf[['日期', '時段', '票證分類', '卡種', '身分', '起點', '迄點', '人次', '進站時間', '出站時間']]
        all_dfs.append(ddf_with_travel_time)
        print(f"成功載入: {ic_file}")
    except FileNotFoundError:
        print(f"警告: 找不到檔案 {ic_file}，將跳過。")
        
    if not all_dfs:
        print("錯誤：所有資料檔案都找不到，無法進行分析。")
        return None

    print("\n正在合併所有資料來源...")
    combined_df = dd.concat(all_dfs, ignore_index=True)
    
    # *** 修正點 (1): 明確指定 '日期' 欄位的格式 ***
    # 根據您的資料，'日期' 欄位格式為 '年-月-日'
    combined_df['日期'] = dd.to_datetime(combined_df['日期'], format='%Y-%m-%d', errors='coerce')
    
    combined_df['星期'] = combined_df['日期'].dt.weekday
    
    combined_df['日期類型'] = '平日'
    combined_df['日期類型'] = combined_df['日期類型'].mask(combined_df['星期'].isin([5, 6]), '假日')
    combined_df['日期類型'] = combined_df['日期類型'].astype('category').cat.set_categories(['平日', '假日'])

    print("資料準備完成！")
    
    # =======================================================
    # +++ 新增功能：儲存處理後的資料 +++
    # =======================================================
    print(f"\n--- 正在將清洗後的資料儲存至 '{output_filename}' ---")
    try:
        # 使用 to_csv 方法儲存
        # single_file=True: 將所有分割區(partitions)合併成一個檔案
        # index=False: 不將 DataFrame 的索引寫入檔案
        # encoding='utf-8-sig': 確保中文在 Excel 中能正確顯示
        combined_df.to_csv(output_filename, single_file=True, index=False, encoding='utf-8-sig')
        # .compute() 會觸發實際的計算與存檔動作
        print(f"成功！資料已儲存至 '{os.path.abspath(output_filename)}'")
    except Exception as e:
        print(f"錯誤：儲存檔案時發生問題: {e}")
    # =======================================================
    
    return combined_df

# 當這個 .py 檔案被直接執行時，會執行以下程式碼
if __name__ == '__main__':
    # 執行資料載入、清洗與儲存
    final_df = load_and_save_data(output_filename='cleaned_tra_data.csv')

    # 如果資料成功處理，可以選擇性地顯示一些資訊
    if final_df is not None:
        print("\n--- 資料處理完成，以下為前 5 筆資料預覽 ---")
        # .head() 會觸發計算並回傳前 n 筆資料
        print(final_df.head())