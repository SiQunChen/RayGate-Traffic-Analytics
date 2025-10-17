# 檔名: config.py
# =============================================================================
#  組態設定檔 (V4 - 新增測試模式)
# =============================================================================
#
#  這個檔案包含了所有分析腳本中會用到的參數。
#  所有分析結果都會被輸出到 `OUTPUT_BASE_DIR` 指定的資料夾中。
#
# =============================================================================

import os

# --- [通用設定] ---

# 圖表和分析結果的總輸出資料夾名稱
OUTPUT_BASE_DIR = 'analysis_output'

# --- [!!! 新增：測試模式設定 !!!] ---
# 說明: 將 TEST_MODE 設為 True，所有資料讀取腳本將只會讀取前 TEST_MODE_ROWS 筆資料。
#       這可以讓你快速測試完整流程，而無需等待完整資料載入。
#       測試完成後，請務必將此設回 False 以進行完整分析。
TEST_MODE = True
TEST_MODE_ROWS = 1000  # 測試模式下讀取的資料筆數


# --- [市區公車分析設定] ---

# 統一後的市區公車資料檔名
BUS_UNIFIED_DATA_FILE = 'unified_data.csv'

# 斗六市區公車分析的目標車站名稱
BUS_DOULIU_TARGET_STATION = '斗六火車站'

# 市區公車分析的輸出子資料夾
BUS_OUTPUT_DIR = os.path.join(OUTPUT_BASE_DIR, '1_市區公車')


# --- [乘客分群分析設定] ---

# 乘客分群分析的輸入檔案路徑 (相對於 cluster_analysis.py)
CLUSTER_INPUT_FILE = f'./市區公車/{BUS_UNIFIED_DATA_FILE}'

# 乘客分群分析的輸出子資料夾
CLUSTER_OUTPUT_DIR = os.path.join(OUTPUT_BASE_DIR, '2_乘客分群')

# 篩選高頻乘客的最低乘車次數門檻
CLUSTER_MIN_TRIP_COUNT = 20


# --- [台鐵資料分析設定] ---

# 清洗整合後的台鐵資料檔名
TRA_CLEANED_DATA_FILE = 'cleaned_tra_data.csv'

# 台鐵分析的輸出子資料夾
TRA_OUTPUT_DIR = os.path.join(OUTPUT_BASE_DIR, '3_台鐵')

# 台鐵分析的目標車站區間
TRA_TARGET_STATIONS = [
    '彰化', '花壇', '大村', '員林', '永靖', '社頭', '田中', '二水',
    '林內', '石榴', '斗六', '斗南', '石龜',
    '大林', '民雄', '南靖', '水上',
    '嘉北', '嘉義'
]

# 斗六台鐵分析的目標車站名稱
TRA_DOULIU_TARGET_STATION = '斗六'


# --- [公路客運分析設定] ---

# 公路客運分析的輸出子資料夾
HIGHWAY_BUS_OUTPUT_DIR = os.path.join(OUTPUT_BASE_DIR, '4_公路客運')

# 日統客運的資料檔案路徑 (相對於 公路客運/日統/analyze.py)
HIGHWAY_BUS_JITONG_FILE = "日統113.xlsx"

# 嘉義客運的資料檔案路徑 (相對於 公路客運/嘉義/analyze.py)
HIGHWAY_BUS_CHIAYI_FOLDER = "data"