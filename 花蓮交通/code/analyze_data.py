# 導入 pandas 函式庫，並使用 pd 作為簡稱，這是慣例
import pandas as pd

# --- 新增的程式碼 ---
# 設定 Pandas 的顯示選項，讓它可以顯示所有的欄位
# 'display.max_columns' 設為 None 表示不限制顯示的欄位數量
pd.set_option('display.max_columns', None)
# --------------------


def analyze_csv_format(file_path):
    """
    分析給定路徑的 CSV 檔案格式。

    這個函式會讀取 CSV 檔案的前 1000 筆資料來進行快速分析，
    並印出檔案的基本資訊，包含：
    1. 檔案維度 (行數, 列數)
    2. 欄位名稱列表
    3. 各欄位的資料類型和非空值數量
    4. 前 5 筆資料範例

    Args:
        file_path (str): CSV 檔案的路徑。
    """
    print("==========================================================")
    print(f"正在分析檔案： {file_path}")
    print("==========================================================")

    try:
        # 嘗試使用 utf-8 編碼讀取檔案。
        # 由於是大型檔案，我們先只讀取前 1000 行進行格式分析，以節省資源。
        # 如果你的檔案非常大，可以將 nrows 的數值調得更小。
        df = pd.read_csv(file_path, nrows=1000)

    except FileNotFoundError:
        # 處理找不到檔案的錯誤
        print(f"錯誤：找不到檔案 '{file_path}'。請確認檔案名稱和路徑是否正確。")
        return
    except UnicodeDecodeError:
        # 如果 utf-8 解碼失敗，嘗試使用 'big5' 編碼，這在處理台灣的舊資料時很常見
        print("使用 UTF-8 編碼讀取失敗，嘗試使用 'Big5' 編碼...")
        try:
            df = pd.read_csv(file_path, nrows=1000, encoding='big5')
        except Exception as e:
            print(f"使用 Big5 編碼也讀取失敗。錯誤訊息：{e}")
            return
    except Exception as e:
        # 處理其他可能的讀取錯誤
        print(f"讀取檔案時發生未知的錯誤：{e}")
        return

    # --- 開始顯示分析結果 ---

    # 1. 顯示資料維度 (行數, 欄位數)
    # df.shape 會回傳一個元組 (tuple)，第一個是行數，第二個是欄位數
    print(f"\n[分析] 資料維度 (前 {len(df)} 行, 總欄位數): {df.shape}\n")

    # 2. 顯示所有欄位名稱
    print("[分析] 欄位名稱列表:")
    print(list(df.columns))
    print("\n")

    # 3. 顯示欄位資料類型和非空值計數
    # df.info() 是一個非常實用的函式，可以提供 DataFrame 的簡潔摘要
    print("[分析] 各欄位資料類型及資訊:")
    df.info()
    print("\n")

    # 4. 顯示前 5 筆資料，讓我們可以預覽資料內容
    # df.head() 預設會顯示前 5 行
    print("[分析] 資料內容預覽 (前 5 筆):")
    print(df.head())
    print("\n\n")


# --- 主程式執行區 ---
if __name__ == "__main__":
    # 定義你的檔案名稱列表
    # 提醒：請確保這些 CSV 檔案和你的 Python 腳本在同一個資料夾下
    file_list = [
        "../data/台鐵/臺鐵非電子票證資料.csv",
        "../data/台鐵/臺鐵電子票證資料(TO2A).csv"
    ]

    # 透過迴圈，依序分析列表中的每一個檔案
    for file in file_list:
        analyze_csv_format(file)