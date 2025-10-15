import pandas as pd

def analyze_card_usage(file_path='unified_data.csv'):
    """
    分析 unified_data.csv 中的卡號使用情況。

    Args:
        file_path (str): CSV 檔案的路徑。
    """
    try:
        # 讀取 CSV 檔案
        print(f"正在讀取檔案: {file_path}...")
        df = pd.read_csv(file_path)
        print("檔案讀取成功。")

        # 確認 '卡號' 欄位是否存在
        if '卡號' not in df.columns:
            print(f"錯誤：在檔案 '{file_path}' 中找不到 '卡號' 欄位。")
            return

        # --- 核心分析 ---
        print("正在分析卡號資料...")
        # 1. 依據 '卡號' 進行分組，並計算每個卡號的出現次數（即搭乘次數）
        trip_counts_by_card = df.groupby('卡號').size()

        # 2. 總人數即為唯一卡號的數量
        total_people = len(trip_counts_by_card)

        # 3. 篩選出搭乘次數 > 20 的卡號
        frequent_travelers = trip_counts_by_card[trip_counts_by_card > 50]
        num_frequent_travelers = len(frequent_travelers)
        
        print("\n--- 分析結果 ---")
        print(f"總唯一卡號數 (總人數): {total_people} 人")
        print(f"搭乘次數超過 20 次的人數: {num_frequent_travelers} 人")
        print("--------------------")

    except FileNotFoundError:
        print(f"錯誤：找不到檔案 '{file_path}'。")
        print("請確認檔案名稱與路徑是否正確，且程式與 CSV 檔在同一個資料夾中。")
    except Exception as e:
        print(f"處理過程中發生未預期的錯誤: {e}")

if __name__ == '__main__':
    # 執行分析函式
    analyze_card_usage()