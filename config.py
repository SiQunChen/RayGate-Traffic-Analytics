# 檔名: config.py
# =============================================================================
#  組態設定檔 (V7 - 使用絕對路徑修正版)
# =============================================================================
#
#  這個檔案包含了所有分析腳本中會用到的參數。
#  - 透過 PROJECT_ROOT 自動偵測專案根目錄，解決相對路徑問題。
#  - 所有分析結果都會被輸出到 `OUTPUT_BASE_DIR`
#
# =============================================================================

import os

# --- [專案根目錄設定] ---
# 自動獲取 config.py 檔案所在的目錄，也就是專案的根目錄
# 這是最關鍵的修改，讓所有路徑都有一個絕對的參考基準
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# --- [通用設定] ---

# 總輸出資料夾名稱 (基於專案根目錄)
OUTPUT_BASE_DIR = os.path.join(PROJECT_ROOT, 'analysis_output')

# 程式碼與資料的基礎路徑 (基於專案根目錄)
CODE_BASE_DIR = os.path.join(PROJECT_ROOT, 'code')
DATA_BASE_DIR = os.path.join(PROJECT_ROOT, 'data')

# --- [測試模式設定] ---
TEST_MODE = True
TEST_MODE_ROWS = 1000  # 測試模式下讀取的資料筆數


# --- [市區公車分析設定] ---

# 市區公車的原始資料路徑
BUS_RAW_DATA_DIR = os.path.join(DATA_BASE_DIR, '市區公車')

# 統一後的市區公車資料檔名 (輸出到 data/市區公車/ 底下)
BUS_UNIFIED_DATA_FILE = os.path.join(BUS_RAW_DATA_DIR, 'unified_data.csv')

# 市區公車分析的輸出子資料夾
BUS_OUTPUT_DIR = os.path.join(OUTPUT_BASE_DIR, '1_市區公車')


# --- [乘客分群分析設定] ---

# 乘客分群分析的輸入檔案路徑 (直接使用上面定義的變數)
CLUSTER_INPUT_FILE = BUS_UNIFIED_DATA_FILE

# 乘客分群分析的輸出子資料夾
CLUSTER_OUTPUT_DIR = os.path.join(OUTPUT_BASE_DIR, '2_乘客分群')

# 篩選高頻乘客的最低乘車次數門檻
CLUSTER_MIN_TRIP_COUNT = 20


# --- [台鐵資料分析設定] ---

# 台鐵原始資料路徑
TRA_RAW_DATA_DIR = os.path.join(DATA_BASE_DIR, '台鐵')

# 清洗整合後的台鐵資料檔名 (輸出到 data/台鐵/ 底下)
TRA_CLEANED_DATA_FILE = os.path.join(TRA_RAW_DATA_DIR, 'cleaned_tra_data.csv')

# 台鐵分析的輸出子資料夾
TRA_OUTPUT_DIR = os.path.join(OUTPUT_BASE_DIR, '3_台鐵')

# 台鐵分析的目標車站區間 (此設定不變)
TRA_TARGET_STATIONS = [
    '彰化', '花壇', '大村', '員林', '永靖', '社頭', '田中', '二水',
    '林內', '石榴', '斗六', '斗南', '石龜',
    '大林', '民雄', '南靖', '水上',
    '嘉北', '嘉義'
]


# --- [公路客運分析設定] ---

# 公路客運分析的輸出子資料夾
HIGHWAY_BUS_OUTPUT_DIR = os.path.join(OUTPUT_BASE_DIR, '4_公路客運')

# 日統客運的資料檔案路徑
HIGHWAY_BUS_JITONG_FILE = os.path.join(DATA_BASE_DIR, '公路客運', '日統', "日統113.xlsx")

# 嘉義客運的資料檔案路徑
HIGHWAY_BUS_CHIAYI_FOLDER = os.path.join(DATA_BASE_DIR, '公路客運', '嘉義')


# --- [轉乘行為分析設定] ---

# 轉乘行為分析的輸出子資料夾
TRANSFER_ANALYSIS_OUTPUT_DIR = os.path.join(OUTPUT_BASE_DIR, '5_轉乘行為分析')

# 設定要進行轉乘分析的「市區公車站點名稱」。
BUS_TRANSFER_STATION = None  # 例如: '斗六火車站'

# 設定要進行轉乘分析的「台鐵車站名稱」。
TRA_TRANSFER_STATION = None    # 例如: '斗六'