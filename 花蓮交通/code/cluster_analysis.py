# 檔名: cluster_analysis.py (V12 - 根據 data_loader_市區公車.py V2 進行重構)
# =============================================================================
# 雲林公車乘客 K-Means 分群完整流程 (自動化版本)
#
# 本腳本涵蓋以下步驟：
# 1. 環境設定與資料載入 (從 config.py 讀取設定)
# 2. 特徵工程 (使用已預處理好的欄位)
# 3. 根據總乘車次數篩選乘客 (從 config.py 讀取門檻)
# 4. 特徵準備
# 5. (固定執行) 使用 PCA 進行降維
# 6. 使用手肘法與輪廓係數自動尋找最佳 K 值
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
    # 從 code/ 回到根目錄
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
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

def load_and_preprocess_data(filepath):
    """
    V2版修改：大幅簡化預處理流程。
    - 移除 unify_ticket_type 函式，因為 data_loader 已處理。
    - 移除時間轉換與旅次時長計算，因為 data_loader 已提供 '旅次時長(分)'。
    - 直接使用 data_loader 產生的欄位。
    """
    print(f"步驟 1: 正在載入已預處理的資料 from '{filepath}'...")
    try:
        # data_loader 已處理大部分 Dtype，此處僅需讀取
        df = pd.read_csv(filepath, dtype={'路線': str, '卡號': str})
    except FileNotFoundError:
        print(f"錯誤：找不到檔案 '{filepath}'。請檢查 config.py 中的 CLUSTER_INPUT_FILE 設定，並確認 data_loader_市區公車.py 已執行。")
        return None
    
    # data_loader 已處理時間格式，此處僅需再次確認
    df['上車時間'] = pd.to_datetime(df['上車時間'], errors='coerce')
    
    # data_loader 已提供 '旅次是否完整' 欄位
    df = df[df['旅次是否完整'] == True].copy()
    
    # 移除 '無卡號' 的記錄，因為無法對其進行使用者分群
    df = df[df['卡號'] != '無卡號'].copy()

    print("持卡身分預覽：")
    print(df['持卡身分'].value_counts())
    print(f"資料載入完成，共計 {len(df)} 筆有效的持卡人旅次紀錄。")
    return df

# --- 步驟 2: 特徵工程 (與原版相同，但依賴的欄位已由 data_loader 產生) ---
def create_user_features(df):
    """
    以每個 '卡號' 為單位，建立使用者行為特徵。
    V2版修改：
    - 直接使用 '上車星期', '上車小時' 等已存在的欄位。
    - 使用 '旅次時長(分)' 取代手動計算的 '旅次時長'。
    - 使用 '持卡身分' 取代 '票種分類'。
    """
    print("\n步驟 2: 正在進行特徵工程...")
    
    # --- 時間相關特徵 ---
    df['是否平日'] = df['日期類型'] == '平日'
    df['是否尖峰'] = df['上車小時'].isin([7, 8, 17, 18]) # 上下班尖峰
    df['是否深夜清晨'] = df['上車小時'].isin([22, 23, 0, 1, 2, 3, 4, 5])
    
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
        平均旅次時長=('旅次時長(分)', 'mean'), # 使用新欄位
        平日乘車比例=('是否平日', lambda x: x.sum() / x.count()),
        尖峰時段乘車比例=('是否尖峰', lambda x: x.sum() / x.count()),
        深夜清晨乘車次數=('是否深夜清晨', 'sum'),
        旅次起終點熵=('OD對', calculate_entropy),
        搭乘路線數=('路線', 'nunique'),
        最常上車站點=('上車站名', safe_mode),
        最常下車站點=('下車站名', safe_mode),
        主要活動路線=('路線', safe_mode),
        主要持卡身分=('持卡身分', safe_mode), # 使用 '持卡身分'
        主要票種類型=('票種類型', safe_mode)  # 新增欄位，用於後續 Tpass 分析
    ).reset_index()
    
    user_features.replace([np.inf, -np.inf], 0, inplace=True)
    user_features.fillna(0, inplace=True)

    print(f"特徵工程完成，共建立 {len(user_features)} 位獨立乘客的特徵資料。")
    print("特徵預覽：")
    print(user_features.head())
    return user_features

# --- 步驟 3: 特徵準備 (已修改) ---
def prepare_features_for_clustering(features_df):
    """
    V2版修改：類別特徵改為 '主要持卡身分'
    """
    print("\n步驟 3: 正在準備特徵 (使用精簡版核心特徵)...")
    core_numerical_features = ['總乘車次數', '平均旅次時長', '平日乘車比例', '尖峰時段乘車比例', '旅次起終點熵']
    core_categorical_features = ['主要持卡身分', '最常上車站點', '最常下車站點'] # 更新特徵
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
    plt.close()
    print(f"PCA 解釋變異數圖已儲存至 '{pca_plot_path}'。")
    return pca_data

# --- 步驟 5: 尋找 K 值 (與原版相同) ---
def find_optimal_k(scaled_data):
    """
    修改後：除了繪圖，還會回傳最佳 K 值。
    """
    print("\n步驟 5: 正在使用手肘法與輪廓係數尋找最佳 K 值...")
    sse, silhouette_scores = [], []
    k_range = range(2, 11) # 縮小範圍以加速
    for k in k_range:
        print(f"  正在計算 K={k}...")
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(scaled_data)
        sse.append(kmeans.inertia_)
        # 對於大型資料集，抽樣計算輪廓係數以提高效率
        sample_size = 5000 if scaled_data.shape[0] > 5000 else None
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
    plt.savefig(plot_path)
    plt.close()
    print(f"評估圖表已儲存至 '{plot_path}'。")
    
    best_k_by_silhouette = k_range[np.argmax(silhouette_scores)]
    print(f"根據最高的輪廓係數，自動選擇的最佳 K 值為 {best_k_by_silhouette}。")
    return best_k_by_silhouette

# --- 步驟 6: K-Means (與原版相同) ---
def apply_kmeans(scaled_data, k):
    print(f"\n步驟 6: 正在以 K={k} 執行 K-Means 分群...")
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(scaled_data)
    print("K-Means 分群完成。")
    return clusters

# --- 步驟 7: 結果分析 (已修改) ---
def analyze_and_visualize_clusters(features_df, clusters):
    """
    V2版修改：使用 '主要持卡身分' 進行分析。
    """
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
        主要持卡身分=('主要持卡身分', safe_mode), 
        最常上車站點=('最常上車站點', safe_mode),
        最常下車站點=('最常下車站點', safe_mode), 
        主要活動路線=('主要活動路線', safe_mode)
    )
    print("\n各群組主要空間與身份特徵："); print(spatial_summary)
    spatial_summary_path = os.path.join(output_dir, 'cluster_spatial_summary.csv')
    spatial_summary.to_csv(spatial_summary_path, encoding='utf-8-sig')
    print(f"空間與身份特徵摘要已儲存至 '{spatial_summary_path}'。")
    
    numerical_summary.drop(columns='群組人數').plot(kind='bar', subplots=True, figsize=(16, 10), layout=(2, 4), legend=False, sharex=True, title='各群組數值特徵比較')
    plt.tight_layout()
    barchart_path = os.path.join(output_dir, 'cluster_feature_comparison.png')
    plt.savefig(barchart_path)
    plt.close()
    
    ticket_distribution = pd.crosstab(features_df['群組'], features_df['主要持卡身分'])
    ticket_distribution.plot(kind='bar', stacked=True, figsize=(12, 7), colormap='viridis')
    plt.title('各群組主要持卡身分分佈'); plt.xlabel('群組'); plt.ylabel('人數'); plt.xticks(rotation=0); plt.legend(title='主要持卡身分'); plt.tight_layout()
    ticket_plot_path = os.path.join(output_dir, 'cluster_ticket_distribution_plot.png')
    plt.savefig(ticket_plot_path)
    plt.close()
    return features_df

# --- 步驟 8: Tpass (已修改) ---
def integrate_tpass_data(clustered_users_df):
    """
    V2版修改：改用 '主要票種類型' 欄位來判斷是否為 Tpass 用戶。
    """
    print("\n步驟 8: 正在整合 Tpass 資料 (依據'主要票種類型'欄位)...")
    clustered_users_df['是否為Tpass用戶'] = (clustered_users_df['主要票種類型'] == '定期票')
    tpass_analysis = clustered_users_df.groupby('群組')['是否為Tpass用戶'].agg(['count', 'sum'])
    tpass_analysis.rename(columns={'count': '群組總人數', 'sum': 'Tpass用戶數'}, inplace=True)
    tpass_analysis['Tpass用戶比例'] = (tpass_analysis['Tpass用戶數'] / tpass_analysis['群組總人數']) * 100
    print("\n各群組 Tpass 用戶分析："); print(tpass_analysis)
    tpass_analysis_path = os.path.join(output_dir, 'tpass_analysis.csv')
    tpass_analysis.to_csv(tpass_analysis_path, encoding='utf-8-sig')
    print(f"Tpass 分析結果已儲存至 '{tpass_analysis_path}'。")
    plt.figure(figsize=(10, 6))
    sns.barplot(x=tpass_analysis.index, y=tpass_analysis['Tpass用戶比例'])
    plt.title('各群組 Tpass 用戶比例'); plt.xlabel('群組'); plt.ylabel('Tpass 用戶比例 (%)')
    tpass_plot_path = os.path.join(output_dir, 'tpass_user_ratio.png')
    plt.savefig(tpass_plot_path)
    plt.close()
    return clustered_users_df

# --- 主執行流程 (與原版相同) ---
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
        
        if remaining_passenger_count == 0:
            print("\n警告：沒有任何乘客的搭乘次數達到分析門檻。")
            print("乘客分群分析已跳過。")
            sys.exit(0)
            
        processed_data, card_ids = prepare_features_for_clustering(user_features_df)
        
        print("\n固定使用 PCA 進行降維優化...")
        data_for_clustering = apply_pca(processed_data)
            
        optimal_k = find_optimal_k(data_for_clustering)
        
        clusters = apply_kmeans(data_for_clustering, k=optimal_k)
        
        # 將群組標籤加回原始特徵 DataFrame
        # 確保索引對齊
        clustered_users_df = user_features_df.set_index('卡號')
        clustered_users_df['群組'] = clusters
        clustered_users_df.reset_index(inplace=True)

        analyzed_df = analyze_and_visualize_clusters(clustered_users_df.copy(), clusters)
        final_df = integrate_tpass_data(analyzed_df)
        
        # 儲存最終包含分群結果的使用者特徵檔
        final_output_path = os.path.join(output_dir, 'final_clustered_user_features.csv')
        final_df.to_csv(final_output_path, index=False, encoding='utf-8-sig')
        print(f"\n包含分群結果的完整使用者特徵資料已儲存至：{final_output_path}")

        print("\n=== 全部分析流程已完成 ===")