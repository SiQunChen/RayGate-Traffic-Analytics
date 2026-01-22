# 檔名: config.py
# =============================================================================
#  組態設定檔 (V8 - 公路客運路徑更新)
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
TEST_MODE = False         # 是否啟用測試模式
TEST_MODE_ROWS = 50000  # 測試模式下讀取的資料筆數


# --- [市區公車分析設定] ---

# 市區公車的原始資料路徑
BUS_RAW_DATA_DIR = os.path.join(DATA_BASE_DIR, '市區公車')

# 市區公車的程式碼路徑
BUS_CODE_DIR = os.path.join(CODE_BASE_DIR, '市區公車')

# 統一後的市區公車資料檔名 (輸出到 data/市區公車/ 底下)
BUS_UNIFIED_DATA_FILE = os.path.join(BUS_CODE_DIR, 'unified_bus_data.csv')

# 市區公車分析的輸出子資料夾
BUS_OUTPUT_DIR = os.path.join(OUTPUT_BASE_DIR, '1_市區公車')


# --- [乘客分群分析設定] ---

# 乘客分群分析的輸入檔案路徑 (直接使用上面定義的變數)
CLUSTER_INPUT_FILE = BUS_UNIFIED_DATA_FILE

# 乘客分群分析的輸出子資料夾
CLUSTER_OUTPUT_DIR = os.path.join(OUTPUT_BASE_DIR, '2_乘客分群')

# 篩選高頻乘客的最低乘車次數門檻
CLUSTER_MIN_TRIP_COUNT = 0


# --- [台鐵資料分析設定] ---

# 台鐵原始資料路徑
TRA_RAW_DATA_DIR = os.path.join(DATA_BASE_DIR, '台鐵')

# 台鐵的程式碼路徑
TRA_CODE_DIR = os.path.join(CODE_BASE_DIR, '台鐵')

# 清洗整合後的台鐵資料檔名
TRA_UNIFIED_DATA_FILE = os.path.join(TRA_CODE_DIR, 'unified_tra_data.csv')

# 台鐵分析的輸出子資料夾
TRA_OUTPUT_DIR = os.path.join(OUTPUT_BASE_DIR, '3_台鐵')

# *** 【核心修改】 ***
# 台鐵分析的目標車站區間與縣市對應
# 未來若要更換分析區域 (例如花東)，只需修改此處的字典即可
TRA_STATION_TO_COUNTY = {
    # 臺東縣
    '大武': '臺東縣', '瀧溪': '臺東縣', '金崙': '臺東縣', '太麻里': '臺東縣', 
    '知本': '臺東縣', '康樂': '臺東縣', '臺東': '臺東縣', '山里': '臺東縣',
    '鹿野': '臺東縣', '瑞源': '臺東縣', '瑞和': '臺東縣', '關山': '臺東縣',
    '海端': '臺東縣', '池上': '臺東縣', 
    # 花蓮縣
    '富里': '花蓮縣', '東竹': '花蓮縣', '東里': '花蓮縣', '玉里': '花蓮縣', 
    '三民': '花蓮縣', '瑞穗': '花蓮縣', '富源': '花蓮縣', '大富': '花蓮縣', 
    '光復': '花蓮縣', '萬榮': '花蓮縣', '鳳林': '花蓮縣', '南平': '花蓮縣', 
    '林榮新光': '花蓮縣', '豐田': '花蓮縣', '壽豐': '花蓮縣', '平和': '花蓮縣', 
    '志學': '花蓮縣', '吉安': '花蓮縣', '花蓮': '花蓮縣', '北埔': '花蓮縣', 
    '景美': '花蓮縣', '新城': '花蓮縣', '崇德': '花蓮縣', '和仁': '花蓮縣', 
    '和平': '花蓮縣',
    # 宜蘭縣
    '漢本': '宜蘭縣', '武塔': '宜蘭縣', '南澳': '宜蘭縣', '東澳': '宜蘭縣',
    '永樂': '宜蘭縣', '蘇澳': '宜蘭縣', '蘇澳新': '宜蘭縣', '冬山': '宜蘭縣',
    '羅東': '宜蘭縣', '中里': '宜蘭縣', '二結': '宜蘭縣', '宜蘭': '宜蘭縣',
    '四城': '宜蘭縣', '礁溪': '宜蘭縣', '頂埔': '宜蘭縣', '頭城': '宜蘭縣',
    '外澳': '宜蘭縣', '龜山': '宜蘭縣', '大溪': '宜蘭縣', '大里': '宜蘭縣',
    '石城': '宜蘭縣'
}

# --- [公路客運分析設定] ---

# 公路客運分析的輸出子資料夾
HIGHWAY_BUS_OUTPUT_DIR = os.path.join(OUTPUT_BASE_DIR, '4_公路客運')

# 公路客運的原始資料路徑
HIGHWAY_BUS_RAW_DATA_DIR = os.path.join(DATA_BASE_DIR, '公路客運')

# *** 【新增】 ***
# 公路客運的程式碼路徑
HIGHWAY_BUS_CODE_DIR = os.path.join(CODE_BASE_DIR, '公路客運')

# *** 【新增】 ***
# 統一後的公路客運資料檔名 (輸出到 code/公路客運/ 底下)
HIGHWAY_BUS_UNIFIED_DATA_FILE = os.path.join(HIGHWAY_BUS_CODE_DIR, 'unified_highway_bus_data.csv')

# *** 【*** 新增區塊 ***】 ***
# 公路客運要篩選的特定路線清單
# 如果此清單為空 (即 [])，則 data_loader 將會處理所有路線。
# 如果此清單非空，data_loader 將只保留清單中指定的路線資料。
HIGHWAY_BUS_TARGET_ROUTES = [
    '1121', '1122', '1125', '1128', '1129', '1130', '1132', '1133', 
    '1135', '1136', '1137', '1139', '1140', '1141', '1142', '1143', 
    '1145', '8119', '8101', '8102', '8105', '8181', '8161', '8173'
]
# *** 【*** 新增區塊結束 ***】 ***

# --- [轉乘行為分析設定] ---

# 轉乘行為分析的輸出子資料夾
TRANSFER_ANALYSIS_OUTPUT_DIR = os.path.join(OUTPUT_BASE_DIR, '5_轉乘行為分析')

# 設定要進行轉乘分析的「市區公車站點名稱」。
BUS_TRANSFER_STATION = None  # 例如: '斗六火車站'

# 設定要進行轉乘分析的「台鐵車站名稱」。
TRA_TRANSFER_STATION = None    # 例如: '斗六'