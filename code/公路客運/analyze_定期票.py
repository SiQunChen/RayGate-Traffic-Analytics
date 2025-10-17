# 檔名: code/公路客運/analyze_定期票.py
# 功能: 分析公路客運資料，對定期票與非定期票用戶進行視覺化分析並儲存圖表。
# 說明: 此腳本的邏輯完全比照 analyze_定期票.py (市區公車版本)，
#       以確保分析標準的一致性。

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys

# --- 從 config.py 載入設定 ---
try:
    # 從目前的 code/公路客運/ 目錄往上兩層找到專案根目錄
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    import config
except ImportError:
    print("錯誤：無法找到 config.py。請確認您的專案結構。")
    sys.exit(1)

def setup_visualization():
    """
    設定 Matplotlib 的視覺化樣式與中文字體。
    """
    sns.set_style("whitegrid")
    font_name = None
    possible_fonts = ['Microsoft JhengHei', 'Heiti TC', 'PingFang TC', 'Arial Unicode MS']
    for font in possible_fonts:
        try:
            plt.rcParams['font.sans-serif'] = [font]
            plt.rcParams['axes.unicode_minus'] = False
            # 嘗試建立一個小圖來驗證字體是否有效
            plt.figure(figsize=(1,1)); plt.title("測試中文字體"); plt.close()
            font_name = font
            print(f"成功設定中文字體為: {font_name}")
            break
        except Exception:
            continue
    if font_name is None:
        print("警告：找不到可用的中文字體。圖表中的中文可能無法正常顯示。")


def analyze_and_visualize_highway_bus_data(file_path=config.HIGHWAY_BUS_UNIFIED_DATA_FILE):
    """
    分析公路客運資料，對定期票與非定期票用戶進行視覺化分析並儲存圖表。
    """
    setup_visualization()
    # *** 核心修改：使用公路客運的輸出資料夾 ***
    output_dir = os.path.join('..', '..', config.HIGHWAY_BUS_OUTPUT_DIR, 'tpass_analysis')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"已建立資料夾: {output_dir}")

    try:
        df = pd.read_csv(file_path, dtype={'路線': str, '卡號': str})
        print(f"成功讀取公路客運資料，總共有 {len(df)} 筆記錄。")
    except FileNotFoundError:
        # *** 核心修改：更新錯誤訊息 ***
        print(f"錯誤：找不到檔案 '{file_path}'。請確認檔案路徑是否正確，並已執行 data_loader_公路客運.py。")
        return
    
    # --- 資料前處理 ---
    df['上車時間'] = pd.to_datetime(df['上車時間'], errors='coerce')
    df.dropna(subset=['上車時間'], inplace=True)
    if df.empty:
        print("警告：無資料可分析。")
        return
    
    # --- 使用者分類 (定期票/非定期票) ---
    df['使用者類型'] = np.where(df['票種類型'] == '定期票', '定期票用戶', '非定期票用戶')
    
    pass_users_df = df[df['使用者類型'] == '定期票用戶'].copy()
    non_pass_users_df = df[df['使用者類型'] == '非定期票用戶'].copy()
    
    print("\n==============================================")
    print("      開始輸出公路客運各項分析結果      ")
    print("==============================================\n")

    # ==============================================================================
    # --- 非定期票用戶分析 ---
    # ==============================================================================
    print("\n--- 開始進行【非定期票用戶】分析 ---")
    if non_pass_users_df.empty:
        print("警告：沒有非定期票用戶資料，將跳過此區塊的分析。")
    else:
        print(f"非定期票用戶共有 {len(non_pass_users_df)} 筆資料。")

        # 1. 非定期票用戶高額消費分析
        print("\n[圖表 1] 產生非定期票用戶高額消費人數圖...")
        monthly_spending = non_pass_users_df.groupby(['上車月份', '卡號'])['消費扣款'].sum().reset_index()
        chart_data = []
        for month in sorted(monthly_spending['上車月份'].dropna().astype(int).unique()):
            month_data = monthly_spending[monthly_spending['上車月份'] == month]
            # 公路客運的月票價格可能不同，但這裡暫時沿用199元作為一個觀察基準
            spent_over_199 = month_data[month_data['消費扣款'] >= 199]['卡號'].nunique()
            chart_data.append({'月份': month, '消費門檻': '>= 199 元', '人數': spent_over_199})
        chart_df = pd.DataFrame(chart_data)
        
        print("\n--- [分析結果 1] 各月份非定期票用戶高額消費人數 (月消費>=199元) ---")
        print(chart_df.pivot(index='月份', columns='消費門檻', values='人數').fillna(0))
        print("--------------------------------------------------\n")
        
        plt.figure(figsize=(10, 6))
        sns.barplot(data=chart_df, x='月份', y='人數', hue='消費門檻')
        plt.title('公路客運-各月份非定期票用戶高額消費人數 (月消費>=199元)', fontsize=16)
        plt.xlabel('月份', fontsize=12); plt.ylabel('潛在定期票轉換用戶數', fontsize=12)
        plt.savefig(os.path.join(output_dir, '1_non_pass_high_spending_counts.png'))
        plt.close(); print(" -> 圖表 1 已儲存。")
        
        print("\n -> [註] 因非定期票用戶多為非電子票證，缺乏站牌資料，已跳過熱門站點與OD分析。")

        # 2. 非定期票用戶搭車時段分佈
        print("\n[圖表 2] 產生非定期票用戶平日與假日搭車時段分佈圖...")
        hourly_usage_non_pass = non_pass_users_df.groupby(['日期類型', '上車小時']).size().reset_index(name='搭乘次數')
        
        print("\n--- [分析結果 2] 非定期票用戶平日與假日各時段搭乘次數分佈 ---")
        print(hourly_usage_non_pass.pivot(index='上車小時', columns='日期類型', values='搭乘次數').fillna(0))
        print("------------------------------------------------------------\n")
        
        plt.figure(figsize=(12, 7))
        sns.lineplot(data=hourly_usage_non_pass, x='上車小時', y='搭乘次數', hue='日期類型', marker='o', palette=['#1f77b4', '#ff7f0e'])
        plt.title('公路客運-非定期票用戶平日與假日各時段搭乘次數分佈', fontsize=16)
        plt.xlabel('小時 (24小時制)', fontsize=12); plt.ylabel('搭乘次數', fontsize=12)
        plt.xticks(np.arange(0, 24, 1)); plt.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.legend(title='日期類型'); plt.tight_layout()
        plt.savefig(os.path.join(output_dir, '2_non_pass_hourly_usage_weekday_weekend.png'))
        plt.close(); print(" -> 圖表 2 已儲存。")
        
        # 3. 非定期票用戶持卡身分佔比
        print("\n[圖表 3] 產生非定期票用戶持卡身分佔比圖...")
        filtered_non_pass = non_pass_users_df[~non_pass_users_df['持卡身分'].isin(['未提供', '無法區別'])]
        ticket_type_counts = filtered_non_pass['持卡身分'].value_counts()
        
        ticket_percentages = (ticket_type_counts / ticket_type_counts.sum() * 100).round(2)
        ticket_distribution_df = pd.DataFrame({'搭乘次數': ticket_type_counts, '佔比(%)': ticket_percentages})
        print("\n--- [分析結果 3] 非定期票用戶持卡身分佔比 ---")
        print(ticket_distribution_df)
        print("--------------------------------------------\n")
        
        plt.figure(figsize=(12, 10))
        wedges, texts, autotexts = plt.pie(ticket_type_counts, autopct='%1.1f%%', startangle=140, pctdistance=0.85)
        plt.legend(wedges, ticket_type_counts.index, title="持卡身分", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        plt.title('公路客運-非定期票用戶持卡身分佔比', fontsize=16)
        plt.setp(autotexts, size=10, weight="bold")
        plt.axis('equal'); plt.tight_layout()
        plt.savefig(os.path.join(output_dir, '3_non_pass_holder_type_distribution.png'))
        plt.close(); print(" -> 圖表 3 已儲存。")


    # ==============================================================================
    # --- 定期票用戶分析 ---
    # ==============================================================================
    print("\n--- 開始進行【定期票用戶】分析 ---")
    if pass_users_df.empty:
        print("警告：沒有定期票用戶資料，將跳過此區塊的分析。")
        # 如果沒有定期票用戶，就直接結束函式
        return

    # 4. 定期票用戶最常上車站點
    print("\n[圖表 4] 產生定期票用戶最常上車站點圖...")
    top_boarding_pass = pass_users_df['上車站名'].value_counts().head(10)
    
    print("\n--- [分析結果 4] 定期票用戶最常上車的 10 個站點 ---")
    print(top_boarding_pass)
    print("--------------------------------------------------\n")
    
    plt.figure(figsize=(10, 8))
    sns.barplot(y=top_boarding_pass.index, x=top_boarding_pass.values, hue=top_boarding_pass.index, palette='viridis', orient='h', legend=False)
    plt.title('公路客運-定期票用戶最常上車的 10 個站點', fontsize=16)
    plt.xlabel('搭乘次數', fontsize=12); plt.ylabel('上車站名', fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '4_pass_top_boarding_stations.png'))
    plt.close(); print(" -> 圖表 4 已儲存。")

    # 5. 定期票用戶最常下車站點
    print("\n[圖表 5] 產生定期票用戶最常下車站點圖...")
    top_alighting_pass = pass_users_df['下車站名'].value_counts().head(10)

    print("\n--- [分析結果 5] 定期票用戶最常下車的 10 個站點 ---")
    print(top_alighting_pass)
    print("--------------------------------------------------\n")
    
    plt.figure(figsize=(10, 8))
    sns.barplot(y=top_alighting_pass.index, x=top_alighting_pass.values, hue=top_alighting_pass.index, palette='plasma', orient='h', legend=False)
    plt.title('公路客運-定期票用戶最常下車的 10 個站點', fontsize=16)
    plt.xlabel('搭乘次數', fontsize=12); plt.ylabel('下車站名', fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '5_pass_top_alighting_stations.png'))
    plt.close(); print(" -> 圖表 5 已儲存。")

    # 6. 定期票用戶最常搭乘OD
    print("\n[圖表 6] 產生定期票用戶最常搭乘OD圖...")
    complete_trips = pass_users_df[pass_users_df['旅次是否完整'] == True].copy()
    complete_trips['OD'] = complete_trips['上車站名'] + ' -> ' + complete_trips['下車站名']
    top_od = complete_trips['OD'].value_counts().head(10)
    
    print("\n--- [分析結果 6] 定期票用戶最常搭乘的 10 個 OD ---")
    print(top_od)
    print("---------------------------------------------------\n")
    
    plt.figure(figsize=(12, 8))
    sns.barplot(y=top_od.index, x=top_od.values, hue=top_od.index, palette='magma', orient='h', legend=False)
    plt.title('公路客運-定期票用戶最常搭乘的 10 個 OD (起迄點)', fontsize=16)
    plt.xlabel('搭乘次數', fontsize=12); plt.ylabel('起迄點 (OD)', fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '6_pass_top_10_od_pairs.png'))
    plt.close(); print(" -> 圖表 6 已儲存。")

    # 7. 定期票用戶搭車時段分佈
    print("\n[圖表 7] 產生定期票用戶平日與假日搭車時段分佈圖...")
    hourly_usage_pass = pass_users_df.groupby(['日期類型', '上車小時']).size().reset_index(name='搭乘次數')

    print("\n--- [分析結果 7] 定期票用戶平日與假日各時段搭乘次數分佈 ---")
    print(hourly_usage_pass.pivot(index='上車小時', columns='日期類型', values='搭乘次數').fillna(0))
    print("------------------------------------------------------------\n")
    
    plt.figure(figsize=(12, 7))
    sns.lineplot(data=hourly_usage_pass, x='上車小時', y='搭乘次數', hue='日期類型', marker='o', palette=['#1f77b4', '#ff7f0e'])
    plt.title('公路客運-定期票用戶平日與假日各時段搭乘次數分佈', fontsize=16)
    plt.xlabel('小時 (24小時制)', fontsize=12); plt.ylabel('搭乘次數', fontsize=12)
    plt.xticks(np.arange(0, 24, 1)); plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.legend(title='日期類型'); plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '7_pass_hourly_usage_weekday_weekend.png'))
    plt.close(); print(" -> 圖表 7 已儲存。")
    
    # 8. Top 20 高頻率定期票用戶排行
    print("\n[圖表 8] 產生高頻率定期票用戶排行圖...")
    top_20_users_series = pass_users_df['卡號'].value_counts().head(20)
    masked_card_ids = [f"...{cid[-4:]}" for cid in top_20_users_series.index]
    
    top_20_df_display = pd.DataFrame({
        '卡號 (末四碼)': masked_card_ids, 
        '總搭乘次數': top_20_users_series.values
    }).set_index('卡號 (末四碼)')
    print("\n--- [分析結果 8] 搭乘次數最高的前 20 名定期票用戶 ---")
    print(top_20_df_display)
    print("------------------------------------------------------\n")
    
    plt.figure(figsize=(12, 10))
    sns.barplot(y=masked_card_ids, x=top_20_users_series.values, hue=masked_card_ids, palette='coolwarm', orient='h', legend=False)
    plt.title('公路客運-搭乘次數最高的前 20 名定期票用戶', fontsize=16)
    plt.xlabel('總搭乘次數', fontsize=12); plt.ylabel('卡號 (末四碼)', fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '8_pass_top_20_users.png'))
    plt.close(); print(" -> 圖表 8 已儲存。")

    print("\n所有公路客運分析與圖表產生完畢！")

if __name__ == '__main__':
    analyze_and_visualize_highway_bus_data()