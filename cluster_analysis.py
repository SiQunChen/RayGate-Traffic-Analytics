# 檔名: cluster_analysis.py (V10 - 整合 config.py)
# =============================================================================
# 雲林公車乘客 K-Means 分群完整流程
# 
# 本腳本涵蓋以下步驟：
# 1. 環境設定與資料載入 (從 config.py 讀取設定)
# 2. 特徵工程
# 3. 根據總乘車次數篩選乘客 (從 config.py 讀取門檻)
# 4. 特徵準備
# 5. (可選) 使用 PCA 進行降維
# 6. 使用手肘法與輪廓係數尋找最佳 K 值
# 7. 執行 K-Means 分群
# 8. 分群結果分析與視覺化
# 9. 整合 Tpass 資料
# =============================================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
from scipy.stats import entropy
import os
import sys

# --- 步驟 0: 從 config.py 載入全域設定 ---
try:
    # 確保能從根目錄找到 config.py
    # sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) # 這行可能不需要，取決於您的執行方式
    import config
except ImportError:
    print("錯誤：無法找到 config.py。請確認您的專案結構。")
    sys.exit(1)

# 設定圖表使用的中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
plt.rcParams['axes.unicode_minus'] = False

# 建立儲存結果的資料夾 (從 config 讀取)
# 這裡的路徑是相對於專案根目錄的
output_dir = config.CLUSTER_OUTPUT_DIR
os.makedirs(output_dir, exist_ok=True)
print(f"分析結果與圖表將儲存於 '{output_dir}/' 資料夾。")


# --- 步驟 1: 資料載入與預處理 ---

# (票種定義的程式碼與原版相同，此處省略以節省空間)
# ... (REGULAR_TICKETS, ORDINARY_TICKETS, etc.) ...
REGULAR_TICKETS = {
    '悠遊-雲林縣199', '悠遊-雲林縣399', '一卡通-雲林縣199', 
    '一卡通-雲林縣399', '愛金卡-雲林縣199', '愛金卡-雲林縣399'
}

ORDINARY_TICKETS = {
    '台南市市民一般卡', 'LinePay-全票', '一卡通一般卡', '一卡通-一般卡', 
    '一卡通-一般卡32', '一卡通-台南市民卡', '一般', '一般卡', '台中市一般', 
    '台中市一般卡', '台北市一般票', '金門縣一般票', '桃園縣一般票', 
    '基隆市一般票', '悠遊全票', '悠遊全票-03', '悠遊-桃園市民卡', 
    '悠遊-普通', '悠遊-普通0A', '悠遊普通卡', '愛金卡-普卡', 
    '愛金卡-普通卡', '嗶乘車-普通卡', '彰化縣一般票', '臺中市一般票'
}

CONCESSIONARY_TICKETS = {
    '一卡通-中市敬老愛心', '一卡通-台中博愛', '一卡通-台中敬老', 
    '一卡通-宜蘭縣愛心卡', '一卡通-宜蘭縣敬老卡', '一卡通-高市陪伴卡', 
    '一卡通-高市博愛卡', '一卡通-高市敬老卡', '一卡通-高雄市博愛卡', 
    '一卡通-敬老11', '一卡通嘉義愛心卡', '台中市博愛卡', '台中市博愛陪伴卡', 
    '台中市敬老卡', '台北市陪伴票', '台北市愛心票', '台北市敬老1票', 
    '台北市優惠票', '台東縣敬老卡', '台南市博愛卡', '台南市博愛陪伴卡', 
    '台南市敬老卡', '宜蘭縣愛心票', '宜蘭縣敬老1票', '宜蘭縣敬老卡', 
    '花蓮縣愛心票', '花蓮縣敬老1票', '金門縣敬老1票', '南投縣敬老1票', 
    '南投縣敬老卡', '南投縣敬老卡(老人)', '屏東縣敬老卡', '苗栗縣愛心票', 
    '苗栗縣敬老1票', '苗栗縣敬老卡', '桃園縣陪伴票', '桃園縣愛心票', 
    '桃園縣敬老1票', '桃園縣優惠票', '高雄市 敬老卡', '高雄市博愛卡', 
    '高雄市博愛陪伴卡', '基隆市愛心票', '基隆市敬老1票', 
    '台南市國小數位學生證', '悠遊-中市孩童', '悠遊-台中愛心', 
    '悠遊-台中敬老', '悠遊-花蓮愛心', '悠遊-花蓮敬老', '悠遊孩童', 
    '悠遊孩童(全)', '悠遊-孩童(全)', '悠遊孩童-01', '悠遊-桃園愛心', 
    '悠遊-桃園敬老', '悠遊陪伴', '悠遊陪伴(全)', '悠遊-陪伴08', 
    '悠遊-雲林愛心', '悠遊-雲林愛心卡', '悠遊-雲林愛陪(全)', 
    '悠遊-雲林愛陪卡', '悠遊-雲林敬老', '悠遊愛心', '悠遊-愛心', 
    '悠遊愛心-01', '悠遊愛心-02', '悠遊-愛心09', '悠遊愛陪', '悠遊-愛陪', 
    '悠遊-愛陪(全)', '悠遊愛陪-01', '悠遊敬老', '悠遊-敬老', '悠遊敬老-01', 
    '悠遊敬老-02', '悠遊敬老-03', '悠遊-敬老09', '悠遊-敬老1', 
    '悠遊敬老-1A', '悠遊-新北敬老', '悠遊-新北學生卡', '悠遊-嘉義縣敬老', 
    '悠遊-優待', '雲林小', '雲林縣陪伴票', '雲林縣愛心票', '雲林縣敬老1票', 
    '雲林縣優惠票', '愛金卡-敬老', '新北市陪伴票', '新北市愛心票', 
    '新北市敬老1票', '新北市優惠票', '新竹市敬老1票', '新竹市優惠票', 
    '新竹縣愛心票', '新竹縣敬老1票', '嘉義市敬老1票', '嘉義縣博愛卡', 
    '嘉義縣愛心票', '嘉義縣敬老1票', '嘉義縣敬老卡', '彰化縣陪伴票', 
    '彰化縣博愛卡', '彰化縣愛心票', '彰化縣敬老1票', '彰化縣敬老卡', 
    '彰縣敬老卡(老人)', '臺中市陪伴票', '臺中市愛心票', '臺中市敬老1票', 
    '澎湖縣敬老卡', '臺中市優惠票'
}

STUDENT_TICKETS = {
    '一卡通-中市學生卡', '一卡通-台南大專學生', '一卡通-屏東學生卡', 
    '一卡通-桃園高中數位', '一卡通-新竹學 生卡', '一卡通-彰縣學生', 
    '一卡通-學生', '一卡通學生卡', '一卡通-學生卡', '一卡通-學生卡14', 
    '一卡通學生卡20', '一卡通學生卡32', '台中市學生卡', '台北市學生卡', 
    '台北市學生票', '台南市學生', '台南市學生卡', '台南市學生票', 
    '屏東縣學生卡', '桃園縣學生票', '高雄市學生卡', '基隆市學生卡', 
    '悠遊-北市學生卡', '悠遊-台中市學生卡', '悠遊-台南學生卡', 
    '悠遊-桃園學生卡', '悠遊-雲林縣199-學', '悠遊-雲林縣學生卡', 
    '悠遊-嘉義縣學生卡', '悠遊-彰化縣學生卡', '悠遊學生', '連江縣學生票', 
    '雲林縣學生卡', '雲林縣學生票', '愛金卡-學生', '愛金-學生', 
    '新北市學生卡', '新北市學生票', '新竹市學生卡', '新竹縣學生卡', 
    '嗶乘車-學生卡', '嘉義市學生卡', '嘉義學生卡', '嘉義縣學生票', 
    '彰化縣學生卡', '彰化縣學生票', '臺中市學生票', '學生卡', '學生認同卡', 
    '聯合科大學生卡', '悠遊-學生', '暨南大學學生卡'
}

TOKEN_CARDS = {
    '一卡通-代幣卡(半)', '一卡通-代幣卡(全)', '代兒童', '代普通卡', 
    '代幣半', '代幣全'
}

def unify_ticket_type(ticket_name):
    ticket_name_str = str(ticket_name).strip()
    if ticket_name_str in REGULAR_TICKETS: return '定期票'
    elif ticket_name_str in ORDINARY_TICKETS: return '普通'
    elif ticket_name_str in CONCESSIONARY_TICKETS: return '優待'
    elif ticket_name_str in STUDENT_TICKETS: return '學生'
    elif ticket_name_str in TOKEN_CARDS: return '代幣卡'
    else: return '其他'

def load_and_preprocess_data(filepath):
    print(f"步驟 1: 正在載入與預處理資料 from '{filepath}'...")
    try:
        df = pd.read_csv(filepath, dtype={'路線': str, '司機': str})
    except FileNotFoundError:
        print(f"錯誤：找不到檔案 '{filepath}'。請檢查 config.py 中的 CLUSTER_INPUT_FILE 設定。")
        return None
    df['票種分類'] = df['票種名稱'].apply(unify_ticket_type)
    print("票種統一完成，分類預覽：")
    print(df['票種分類'].value_counts())
    df['上車時間'] = pd.to_datetime(df['上車時間'], errors='coerce')
    df['下車時間'] = pd.to_datetime(df['下車時間'], errors='coerce')
    df = df[df['旅次是否完整'] == True].copy()
    df['旅次時長'] = (df['下車時間'] - df['上車時間']).dt.total_seconds() / 60
    print(f"資料預處理完成，共計 {len(df)} 筆有效旅次紀錄。")
    return df

# --- 步驟 2: 特徵工程 (與原版相同) ---
def create_user_features(df):
    """
    以每個 '卡號' 為單位，建立使用者行為特徵。
    """
    print("\n步驟 2: 正在進行特徵工程...")
    
    # --- 時間相關特徵 ---
    df['星期'] = df['上車時間'].dt.dayofweek  # 0=週一, 6=週日
    df['小時'] = df['上車時間'].dt.hour
    df['是否平日'] = df['星期'].isin(range(5)) # 0-4 代表週一到週五
    df['是否尖峰'] = df['小時'].isin([7, 8, 17, 18]) # 上下班尖峰
    df['是否深夜清晨'] = df['小時'].isin([22, 23, 0, 1, 2, 3, 4, 5])
    
    # --- 空間相關特徵 ---
    df['OD對'] = df['上車站名'] + ' -> ' + df['下車站名']
    
    # --- 以卡號進行分組，計算各項特徵 ---
    safe_mode = lambda x: x.mode().iloc[0] if not x.mode().empty else None

    def calculate_entropy(series):
        counts = series.value_counts()
        probabilities = counts / counts.sum()
        return entropy(probabilities, base=2)

    user_features = df.groupby('卡號').agg(
        總乘車次數=('卡號', 'count'),
        平均旅次時長=('旅次時長', 'mean'),
        平日乘車比例=('是否平日', lambda x: x.sum() / x.count()),
        尖峰時段乘車比例=('是否尖峰', lambda x: x.sum() / x.count()),
        深夜清晨乘車次數=('是否深夜清晨', 'sum'),
        旅次起終點熵=('OD對', calculate_entropy),
        搭乘路線數=('路線', 'nunique'),
        最常上車站點=('上車站名', safe_mode),
        最常下車站點=('下車站名', safe_mode),
        主要活動路線=('路線', safe_mode),
        主要票種=('票種分類', safe_mode)
    ).reset_index()
    
    user_features.replace([np.inf, -np.inf], 0, inplace=True)
    user_features.fillna(0, inplace=True)

    print(f"特徵工程完成，共建立 {len(user_features)} 位獨立乘客的特徵資料。")
    print("特徵預覽：")
    print(user_features.head())
    return user_features

# --- 步驟 3: 特徵準備 (與原版相同) ---
def prepare_features_for_clustering(features_df):
    print("\n步驟 3: 正在準備特徵 (使用精簡版核心特徵)...")
    core_numerical_features = ['總乘車次數', '平均旅次時長', '平日乘車比例', '尖峰時段乘車比例', '旅次起終點熵']
    core_categorical_features = ['主要票種', '最常上車站點', '最常下車站點']
    model_df = features_df.set_index('卡號')
    features_for_model = model_df[core_numerical_features + core_categorical_features]
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), core_numerical_features),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), core_categorical_features)
        ],
        remainder='drop'
    )
    processed_features = preprocessor.fit_transform(features_for_model)
    print(f"特徵準備完成，共使用 {len(core_numerical_features)} 個數值特徵與 {len(core_categorical_features)} 個類別特徵進行分群。")
    return processed_features, model_df.index

# # --- 步驟 3: 特徵準備 (使用所有特徵) ---
# def prepare_features_for_clustering(features_df):
#     """
#     準備用於分群的特徵矩陣。
#     本次更新：使用所有數值特徵與低基數類別特徵。
#     """
#     print("\n步驟 3: 正在準備特徵 (使用所有特徵)...")
    
#     # 將 '卡號' 設為索引，以便後續處理
#     model_df = features_df.set_index('卡號')

#     # 自動選取所有數值型特徵
#     numerical_features = model_df.select_dtypes(include=np.number).columns.tolist()
    
#     # 明確定義要進行 One-Hot 編碼的低基數類別特徵
#     # 排除高基數的站點、路線特徵，因為它們會產生過多維度，不適合直接分群
#     categorical_features = ['主要票種']
    
#     print(f"  - 自動選取的數值特徵 ({len(numerical_features)}個): {numerical_features}")
#     print(f"  - 手動選取的類別特徵 ({len(categorical_features)}個): {categorical_features}")

#     # 建立一個處理流程
#     preprocessor = ColumnTransformer(
#         transformers=[
#             ('num', StandardScaler(), numerical_features),
#             ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
#         ],
#         remainder='drop' # 丟棄未指定的欄位 (例如高基數的站點名稱)
#     )
    
#     processed_features = preprocessor.fit_transform(model_df)
    
#     print(f"特徵準備完成，共使用 {len(numerical_features)} 個數值特徵與 {len(categorical_features)} 個類別特徵進行分群。")
#     return processed_features, model_df.index

# --- 步驟 4: PCA (與原版相同) ---
def apply_pca(processed_data, n_components=0.95):
    print(f"\n步驟 4: 正在使用 PCA 進行降維，目標保留 {n_components*100}% 的變異...")
    pca = PCA(n_components=n_components, random_state=42, svd_solver='full')
    pca_data = pca.fit_transform(processed_data)
    print(f"PCA 完成。原始特徵維度: {processed_data.shape[1]}, 降維後維度: {pca.n_components_}")
    plt.figure(figsize=(10, 6))
    plt.plot(np.cumsum(pca.explained_variance_ratio_), marker='o', linestyle='--')
    plt.xlabel('主成分數量'); plt.ylabel('累積解釋變異數比例'); plt.title('PCA 解釋變異數'); plt.grid(True)
    plt.axhline(y=n_components, color='r', linestyle=':', label=f'{n_components*100}% 解釋變異數閾值')
    plt.axvline(x=pca.n_components_ - 1, color='g', linestyle=':', label=f'選擇 {pca.n_components_} 個主成分')
    plt.legend()
    pca_plot_path = os.path.join(output_dir, 'pca_explained_variance.png')
    plt.savefig(pca_plot_path)
    plt.show()
    print(f"PCA 解釋變異數圖已儲存至 '{pca_plot_path}'。")
    return pca_data

# --- 步驟 5: 尋找 K 值 (與原版相同) ---
def find_optimal_k(scaled_data):
    print("\n步驟 5: 正在使用手肘法與輪廓係數尋找最佳 K 值...")
    sse, silhouette_scores = [], []
    k_range = range(2, 20)
    for k in k_range:
        print(f"  正在計算 K={k}...")
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(scaled_data)
        sse.append(kmeans.inertia_)
        sample_size = 10000 if scaled_data.shape[0] > 10000 else None
        score = silhouette_score(scaled_data, kmeans.labels_, metric='euclidean', sample_size=sample_size, random_state=42)
        silhouette_scores.append(score)
    fig, ax1 = plt.subplots(figsize=(12, 7))
    ax1.set_xlabel('分群數量 (K)'); ax1.set_ylabel('SSE (群內誤差平方和)', color='tab:blue')
    ax1.plot(k_range, sse, marker='o', linestyle='--', color='tab:blue', label='SSE (手肘法)')
    ax1.tick_params(axis='y', labelcolor='tab:blue'); ax1.legend(loc='upper left')
    ax2 = ax1.twinx()
    ax2.set_ylabel('平均輪廓係數', color='tab:red')
    ax2.plot(k_range, silhouette_scores, marker='s', linestyle='-', color='tab:red', label='平均輪廓係數')
    ax2.tick_params(axis='y', labelcolor='tab:red'); ax2.legend(loc='upper right')
    fig.tight_layout(); plt.title('K-Means 最佳 K 值評估 (手肘法 vs. 輪廓係數)', pad=20)
    plt.xticks(k_range); plt.grid(True)
    plot_path = os.path.join(output_dir, 'optimal_k_evaluation.png')
    plt.savefig(plot_path); plt.show()
    print(f"評估圖表已儲存至 '{plot_path}'。")
    best_k_by_silhouette = k_range[np.argmax(silhouette_scores)]
    print(f"提示：根據最高的輪廓係數，建議的 K 值為 {best_k_by_silhouette}。")
    print("請綜合觀察兩條曲線來決定最終的 K 值。")

# --- 步驟 6: K-Means (與原版相同) ---
def apply_kmeans(scaled_data, k):
    print(f"\n步驟 6: 正在以 K={k} 執行 K-Means 分群...")
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(scaled_data)
    print("K-Means 分群完成。")
    return clusters

# --- 步驟 7: 結果分析 (與原版相同) ---
def analyze_and_visualize_clusters(features_df, clusters):
    print("\n步驟 7: 正在進行分群結果分析與視覺化...")
    features_df['群組'] = clusters
    numerical_summary = features_df.groupby('群組').mean(numeric_only=True)
    numerical_summary['群組人數'] = features_df['群組'].value_counts().sort_index()
    print("各群組數值特徵平均值與人數："); print(numerical_summary)
    summary_path = os.path.join(output_dir, 'cluster_numerical_summary.csv')
    numerical_summary.to_csv(summary_path, encoding='utf-8-sig')
    print(f"數值特徵摘要已儲存至 '{summary_path}'。")
    safe_mode = lambda x: x.mode().iloc[0] if not x.mode().empty else 'N/A'
    spatial_summary = features_df.groupby('群組').agg(
        主要票種=('主要票種', safe_mode), 最常上車站點=('最常上車站點', safe_mode),
        最常下車站點=('最常下車站點', safe_mode), 主要活動路線=('主要活動路線', safe_mode)
    )
    print("\n各群組主要空間與身份特徵："); print(spatial_summary)
    spatial_summary_path = os.path.join(output_dir, 'cluster_spatial_summary.csv')
    spatial_summary.to_csv(spatial_summary_path, encoding='utf-8-sig')
    print(f"空間與身份特徵摘要已儲存至 '{spatial_summary_path}'。")
    numerical_summary.drop(columns='群組人數').plot(kind='bar', subplots=True, figsize=(16, 10), layout=(2, 4), legend=False, sharex=True, title='各群組數值特徵比較')
    plt.tight_layout(); barchart_path = os.path.join(output_dir, 'cluster_feature_comparison.png'); plt.savefig(barchart_path); plt.show()
    ticket_distribution = pd.crosstab(features_df['群組'], features_df['主要票種'])
    ticket_distribution.plot(kind='bar', stacked=True, figsize=(12, 7), colormap='viridis')
    plt.title('各群組主要票種分佈'); plt.xlabel('群組'); plt.ylabel('人數'); plt.xticks(rotation=0); plt.legend(title='主要票種'); plt.tight_layout()
    ticket_plot_path = os.path.join(output_dir, 'cluster_ticket_distribution_plot.png'); plt.savefig(ticket_plot_path); plt.show()
    return features_df

# --- 步驟 8: Tpass (與原版相同) ---
def integrate_tpass_data(clustered_users_df):
    print("\n步驟 8: 正在整合 Tpass 資料 (依據'主要票種'欄位)...")
    clustered_users_df['是否為Tpass用戶'] = (clustered_users_df['主要票種'] == '定期票')
    tpass_analysis = clustered_users_df.groupby('群組')['是否為Tpass用戶'].agg(['count', 'sum'])
    tpass_analysis.rename(columns={'count': '群組總人數', 'sum': 'Tpass用戶數'}, inplace=True)
    tpass_analysis['Tpass用戶比例'] = (tpass_analysis['Tpass用戶數'] / tpass_analysis['群組總人數']) * 100
    print("\n各群組 Tpass 用戶分析："); print(tpass_analysis)
    tpass_analysis_path = os.path.join(output_dir, 'tpass_analysis.csv'); tpass_analysis.to_csv(tpass_analysis_path, encoding='utf-8-sig')
    print(f"Tpass 分析結果已儲存至 '{tpass_analysis_path}'。")
    plt.figure(figsize=(10, 6)); sns.barplot(x=tpass_analysis.index, y=tpass_analysis['Tpass用戶比例'])
    plt.title('各群組 Tpass 用戶比例'); plt.xlabel('群組'); plt.ylabel('Tpass 用戶比例 (%)')
    tpass_plot_path = os.path.join(output_dir, 'tpass_user_ratio.png'); plt.savefig(tpass_plot_path); plt.show()
    return clustered_users_df

# --- 主執行流程 ---
if __name__ == '__main__':
    # 從 config 讀取檔案路徑
    raw_df = load_and_preprocess_data(filepath=config.CLUSTER_INPUT_FILE)
    
    if raw_df is not None:
        user_features_df = create_user_features(raw_df)
        
        initial_passenger_count = len(user_features_df)
        print(f"\n進行篩選前，共有 {initial_passenger_count} 位獨立乘客。")

        # 從 config 讀取最低乘車次數
        min_trips = config.CLUSTER_MIN_TRIP_COUNT
        user_features_df = user_features_df[user_features_df['總乘車次數'] >= min_trips].copy()

        remaining_passenger_count = len(user_features_df)
        removed_passenger_count = initial_passenger_count - remaining_passenger_count
        print(f"移除了 {removed_passenger_count} 位總乘車次數小於 {min_trips} 的乘客。")
        print(f"篩選後剩下 {remaining_passenger_count} 位乘客進行後續分析。")
        
        processed_data, card_ids = prepare_features_for_clustering(user_features_df)
        
        use_pca = input("\n是否要使用 PCA 進行降維優化？ (y/n): ").lower()
        if use_pca == 'y':
            data_for_clustering = apply_pca(processed_data)
        else:
            print("跳過 PCA 步驟，使用原始核心特徵進行分群。")
            data_for_clustering = processed_data
            
        find_optimal_k(data_for_clustering)
        
        try:
            optimal_k = int(input("\n請根據評估圖表，輸入您選擇的最佳 K 值 (建議 4~8): "))
        except (ValueError, TypeError):
            print("輸入無效，將使用預設值 K=5。")
            optimal_k = 5
        
        clusters = apply_kmeans(data_for_clustering, k=optimal_k)
        
        clustered_users_df = user_features_df.copy()
        clustered_users_df['群組'] = clusters
        
        analyzed_df = analyze_and_visualize_clusters(clustered_users_df, clusters)
        integrate_tpass_data(analyzed_df)
        
        print("\n=== 全部分析流程已完成 ===")