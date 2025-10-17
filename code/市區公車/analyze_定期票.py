# 檔名: analyze_定期票.py (V2 - 已與 data_loader_市區公車.py V2 同步)
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys

# --- 從 config.py 載入設定 ---
try:
    # 假設 config.py 在上層目錄
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
            plt.figure(figsize=(1,1)); plt.title("測試中文字體"); plt.close()
            font_name = font
            print(f"成功設定中文字體為: {font_name}")
            break
        except Exception:
            continue
    if font_name is None:
        print("警告：找不到可用的中文字體。圖表中的中文可能無法正常顯示。")


def analyze_and_visualize_bus_data(file_path=config.BUS_UNIFIED_DATA_FILE):
    """
    分析雲林市區公車資料，對月票與非月票用戶進行視覺化分析並儲存圖表。
    V2 版：已適配 data_loader_市區公車.py 產生的新欄位。
    """
    setup_visualization()
    # 使用 config.py 中定義的輸出資料夾
    output_dir = os.path.join('..', '..', config.BUS_OUTPUT_DIR, '199_399_analysis')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"已建立資料夾: {output_dir}")

    try:
        # 【V2 修改】data_loader 已處理 DtypeWarning，此處可簡化
        df = pd.read_csv(file_path, dtype={'路線': str, '卡號': str})
        print(f"成功讀取資料，總共有 {len(df)} 筆記錄。")
    except FileNotFoundError:
        print(f"錯誤：找不到檔案 '{file_path}'。請確認您已執行 data_loader_市區公車.py。")
        return
    
    # --- 【V2 修改】資料前處理簡化 ---
    # data_loader 已將時間轉為 datetime 物件，並建立了所需的時間特徵欄位
    # 此處僅需確認 '上車時間' 欄位存在且無空值即可
    df['上車時間'] = pd.to_datetime(df['上車時間'], errors='coerce')
    df.dropna(subset=['上車時間'], inplace=True)
    if df.empty:
        print("警告：無資料可分析。")
        return

    # --- 使用者分類 (月票/非月票) ---
    # 這部分的邏輯保持不變，因為這是此分析腳本的核心
    tickets_199 = ['悠遊-雲林縣199', '一卡通-雲林縣199', '愛金卡-雲林縣199', '雲林縣內通勤', '雲林']
    tickets_399 = ['大雲林區', '雲嘉嘉', '一卡通-雲林縣399', '愛金卡-雲林縣399', '悠遊-雲林縣399']
    conditions = [df['票種名稱'].isin(tickets_199), df['票種名稱'].isin(tickets_399)]
    choices = ['199月票', '399月票']
    df['月票類型'] = np.select(conditions, choices, default='非月票')
    
    monthly_pass_users_df = df[df['月票類型'] != '非月票'].copy()
    non_monthly_pass_users_df = df[df['月票類型'] == '非月票'].copy()
    
    print("\n==============================================")
    print("          開始輸出各項分析結果          ")
    print("==============================================\n")

    # ==============================================================================
    # --- 非月票用戶分析 ---
    # ==============================================================================
    print("\n--- 開始進行【非月票用戶】分析 ---")
    if non_monthly_pass_users_df.empty:
        print("警告：沒有非月票用戶資料，將跳過此區塊的分析。")
    else:
        # *** 移除票種為「優待」的資料 (邏輯保留) ***
        print(f"統一化後，非月票用戶共有 {len(non_monthly_pass_users_df)} 筆資料。")
        original_count = len(non_monthly_pass_users_df)
        # 假設 '優待' 票種在 data_loader 清理後依然可能存在
        non_monthly_pass_users_df = non_monthly_pass_users_df[non_monthly_pass_users_df['票種名稱'] != '優待'].copy()
        removed_count = original_count - len(non_monthly_pass_users_df)
        print(f"正在移除票種為「優待」的資料... 已移除 {removed_count} 筆。")
        print(f"移除後，剩餘 {len(non_monthly_pass_users_df)} 筆非月票用戶資料進行分析。")

        if non_monthly_pass_users_df.empty:
            print("警告：移除『優待』票種後，已無資料可供分析。")
            return
        
        # 1. 非月票用戶高額消費分析
        print("\n[圖表 1] 產生非月票用戶高額消費人數圖...")
        # 【V2 修改】使用 data_loader 產生的 '上車月份' 欄位
        monthly_spending = non_monthly_pass_users_df.groupby(['上車月份', '卡號'])['消費扣款'].sum().reset_index()
        chart_data = []
        for month in sorted(monthly_spending['上車月份'].unique()):
            month_data = monthly_spending[monthly_spending['上車月份'] == month]
            spent_between_199_399 = month_data[(month_data['消費扣款'] > 199) & (month_data['消費扣款'] < 399)]['卡號'].nunique()
            spent_over_399 = month_data[month_data['消費扣款'] > 399]['卡號'].nunique()
            chart_data.append({'月份': month, '消費門檻': '199-399 元', '人數': spent_between_199_399})
            chart_data.append({'月份': month, '消費門檻': '> 399 元', '人數': spent_over_399})
        chart_df = pd.DataFrame(chart_data)
        
        print("\n--- [分析結果 1] 各月份非月票用戶高額消費人數 ---")
        print(chart_df.pivot(index='月份', columns='消費門檻', values='人數').fillna(0))
        print("--------------------------------------------------\n")
        
        plt.figure(figsize=(10, 6))
        sns.barplot(data=chart_df, x='月份', y='人數', hue='消費門檻')
        plt.title('各月份非月票用戶高額消費人數', fontsize=16)
        plt.xlabel('月份', fontsize=12); plt.ylabel('人數', fontsize=12)
        plt.savefig(os.path.join(output_dir, '1_non_pass_high_spending_counts.png'))
        plt.close(); print(" -> 圖表 1 已儲存。")

        # 2. 非月票用戶最常上車站點
        print("\n[圖表 2] 產生非月票用戶最常上車站點圖...")
        top_boarding = non_monthly_pass_users_df['上車站名'].value_counts().head(10)
        
        print("\n--- [分析結果 2] 非月票用戶最常上車的 10 個站點 ---")
        print(top_boarding)
        print("--------------------------------------------------\n")
        
        plt.figure(figsize=(10, 8))
        sns.barplot(y=top_boarding.index, x=top_boarding.values, hue=top_boarding.index, palette='viridis', orient='h', legend=False)
        plt.title('非月票用戶最常上車的 10 個站點', fontsize=16)
        plt.xlabel('搭乘次數', fontsize=12); plt.ylabel('上車站名', fontsize=12)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, '2_non_pass_top_boarding_stations.png'))
        plt.close(); print(" -> 圖表 2 已儲存。")

        # 3. 非月票用戶最常下車站點
        print("\n[圖表 3] 產生非月票用戶最常下車站點圖...")
        top_alighting = non_monthly_pass_users_df['下車站名'].value_counts().head(10)
        
        print("\n--- [分析結果 3] 非月票用戶最常下車的 10 個站點 ---")
        print(top_alighting)
        print("--------------------------------------------------\n")
        
        plt.figure(figsize=(10, 8))
        sns.barplot(y=top_alighting.index, x=top_alighting.values, hue=top_alighting.index, palette='plasma', orient='h', legend=False)
        plt.title('非月票用戶最常下車的 10 個站點', fontsize=16)
        plt.xlabel('搭乘次數', fontsize=12); plt.ylabel('下車站名', fontsize=12)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, '3_non_pass_top_alighting_stations.png'))
        plt.close(); print(" -> 圖表 3 已儲存。")
        
        # 4. 非月票用戶搭車時段分佈 (平日/假日折線圖)
        print("\n[圖表 4] 產生非月票用戶平日與假日搭車時段分佈圖...")
        # 【V2 修改】直接使用 '日期類型' 和 '上車小時'
        hourly_usage_non_pass = non_monthly_pass_users_df.groupby(['日期類型', '上車小時']).size().reset_index(name='搭乘次數')
        
        print("\n--- [分析結果 4] 非月票用戶平日與假日各時段搭乘次數分佈 ---")
        print(hourly_usage_non_pass.pivot(index='上車小時', columns='日期類型', values='搭乘次數').fillna(0))
        print("------------------------------------------------------------\n")
        
        plt.figure(figsize=(12, 7))
        sns.lineplot(data=hourly_usage_non_pass, x='上車小時', y='搭乘次數', hue='日期類型', marker='o', palette=['#1f77b4', '#ff7f0e'])
        plt.title('非月票用戶平日與假日各時段搭乘次數分佈', fontsize=16)
        plt.xlabel('小時 (24小時制)', fontsize=12); plt.ylabel('搭乘次數', fontsize=12)
        plt.xticks(np.arange(0, 24, 1)); plt.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.legend(title='日類型'); plt.tight_layout()
        plt.savefig(os.path.join(output_dir, '4_non_pass_hourly_usage_weekday_weekend.png'))
        plt.close(); print(" -> 圖表 4 已儲存。")

        # 5. 消費介於 199-399 元用戶的熱門 OD
        print("\n[圖表 5] 產生非月票高額消費(199-399元)用戶熱門OD圖...")
        # 【V2 修改】使用 '上車月份' 進行分組
        monthly_spending = non_monthly_pass_users_df.groupby(['上車月份', '卡號'])['消費扣款'].sum().reset_index()
        cards_between_199_399 = monthly_spending[(monthly_spending['消費扣款'] > 199) & (monthly_spending['消費扣款'] < 399)]['卡號'].unique()
        high_spenders_199_df = non_monthly_pass_users_df[non_monthly_pass_users_df['卡號'].isin(cards_between_199_399)]
        if not high_spenders_199_df.empty:
            complete_trips_high_199 = high_spenders_199_df[high_spenders_199_df['旅次是否完整'] == True].copy()
            complete_trips_high_199['OD'] = complete_trips_high_199['上車站名'] + ' -> ' + complete_trips_high_199['下車站名']
            top_od_high_199 = complete_trips_high_199['OD'].value_counts().head(10)
            
            print("\n--- [分析結果 5] 非月票用戶(月消費 199-399元)最常搭乘的 10 個 OD ---")
            print(top_od_high_199)
            print("--------------------------------------------------------------------\n")
            
            plt.figure(figsize=(12, 8))
            sns.barplot(y=top_od_high_199.index, x=top_od_high_199.values, hue=top_od_high_199.index, palette='magma', orient='h', legend=False)
            plt.title('非月票用戶(月消費 199-399元)最常搭乘的 10 個 OD', fontsize=16)
            plt.xlabel('搭乘次數', fontsize=12); plt.ylabel('起迄點 (OD)', fontsize=12)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, '5_non_pass_high_spending_199_top_od.png'))
            plt.close(); print(" -> 圖表 5 已儲存。")
        else:
            print(" -> 找不到月消費介於 199-399 元的非月票用戶，跳過此圖表。")

        # 6. 消費 > 399 元用戶的熱門 OD
        print("\n[圖表 6] 產生非月票高額消費(>399)用戶熱門OD圖...")
        cards_over_399 = monthly_spending[monthly_spending['消費扣款'] > 399]['卡號'].unique()
        high_spenders_399_df = non_monthly_pass_users_df[non_monthly_pass_users_df['卡號'].isin(cards_over_399)]
        if not high_spenders_399_df.empty:
            complete_trips_high_399 = high_spenders_399_df[high_spenders_399_df['旅次是否完整'] == True].copy()
            complete_trips_high_399['OD'] = complete_trips_high_399['上車站名'] + ' -> ' + complete_trips_high_399['下車站名']
            top_od_high_399 = complete_trips_high_399['OD'].value_counts().head(10)
            
            print("\n--- [分析結果 6] 非月票用戶(月消費 > 399元)最常搭乘的 10 個 OD ---")
            print(top_od_high_399)
            print("------------------------------------------------------------------\n")
            
            plt.figure(figsize=(12, 8))
            sns.barplot(y=top_od_high_399.index, x=top_od_high_399.values, hue=top_od_high_399.index, palette='cividis', orient='h', legend=False)
            plt.title('非月票用戶(月消費>399元)最常搭乘的 10 個 OD', fontsize=16)
            plt.xlabel('搭乘次數', fontsize=12); plt.ylabel('起迄點 (OD)', fontsize=12)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, '6_non_pass_high_spending_399_top_od.png'))
            plt.close(); print(" -> 圖表 6 已儲存。")
        else:
            print(" -> 找不到月消費 > 399 的非月票用戶，跳過此圖表。")

        # 7. 非月票用戶票種佔比
        print("\n[圖表 7] 產生非月票用戶票種佔比圖...")
        ticket_type_counts = non_monthly_pass_users_df['票種名稱'].value_counts()
        
        ticket_percentages = (ticket_type_counts / ticket_type_counts.sum() * 100).round(2)
        ticket_distribution_df = pd.DataFrame({'搭乘次數': ticket_type_counts, '佔比(%)': ticket_percentages})
        print("\n--- [分析結果 7] 非月票用戶票種分類佔比 ---")
        print(ticket_distribution_df)
        print("--------------------------------------------\n")
        
        plt.figure(figsize=(12, 10))
        wedges, texts, autotexts = plt.pie(ticket_type_counts, autopct='%1.1f%%', startangle=140, pctdistance=0.85)
        plt.legend(wedges, ticket_type_counts.index, title="票種分類", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        plt.title('非月票用戶票種分類佔比', fontsize=16)
        plt.setp(autotexts, size=10, weight="bold")
        plt.axis('equal'); plt.tight_layout()
        plt.savefig(os.path.join(output_dir, '7_non_pass_ticket_type_distribution.png'))
        plt.close(); print(" -> 圖表 7 已儲存。")


    # ==============================================================================
    # --- 月票用戶分析 ---
    # ==============================================================================
    print("\n--- 開始進行【月票用戶】分析 ---")
    if monthly_pass_users_df.empty:
        print("警告：沒有月票用戶資料，將跳過此區塊的分析。")
        return

    # 8. 月票用戶最常上車站點
    print("\n[圖表 8] 產生月票用戶最常上車站點圖...")
    top_boarding_pass = monthly_pass_users_df['上車站名'].value_counts().head(10)
    
    print("\n--- [分析結果 8] 月票用戶最常上車的 10 個站點 ---")
    print(top_boarding_pass)
    print("--------------------------------------------------\n")
    
    plt.figure(figsize=(10, 8))
    sns.barplot(y=top_boarding_pass.index, x=top_boarding_pass.values, hue=top_boarding_pass.index, palette='viridis', orient='h', legend=False)
    plt.title('月票用戶最常上車的 10 個站點', fontsize=16)
    plt.xlabel('搭乘次數', fontsize=12); plt.ylabel('上車站名', fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '8_monthly_pass_top_boarding_stations.png'))
    plt.close(); print(" -> 圖表 8 已儲存。")

    # 9. 月票用戶最常下車站點
    print("\n[圖表 9] 產生月票用戶最常下車站點圖...")
    top_alighting_pass = monthly_pass_users_df['下車站名'].value_counts().head(10)

    print("\n--- [分析結果 9] 月票用戶最常下車的 10 個站點 ---")
    print(top_alighting_pass)
    print("--------------------------------------------------\n")
    
    plt.figure(figsize=(10, 8))
    sns.barplot(y=top_alighting_pass.index, x=top_alighting_pass.values, hue=top_alighting_pass.index, palette='plasma', orient='h', legend=False)
    plt.title('月票用戶最常下車的 10 個站點', fontsize=16)
    plt.xlabel('搭乘次數', fontsize=12); plt.ylabel('下車站名', fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '9_monthly_pass_top_alighting_stations.png'))
    plt.close(); print(" -> 圖表 9 已儲存。")

    # 10. 月票用戶最常搭乘OD
    print("\n[圖表 10] 產生月票用戶最常搭乘OD圖...")
    complete_trips = monthly_pass_users_df[monthly_pass_users_df['旅次是否完整'] == True].copy()
    complete_trips['OD'] = complete_trips['上車站名'] + ' -> ' + complete_trips['下車站名']
    top_od = complete_trips['OD'].value_counts().head(10)
    
    print("\n--- [分析結果 10] 月票用戶最常搭乘的 10 個 OD ---")
    print(top_od)
    print("---------------------------------------------------\n")
    
    plt.figure(figsize=(12, 8))
    sns.barplot(y=top_od.index, x=top_od.values, hue=top_od.index, palette='magma', orient='h', legend=False)
    plt.title('月票用戶最常搭乘的 10 個 OD (起迄點)', fontsize=16)
    plt.xlabel('搭乘次數', fontsize=12); plt.ylabel('起迄點 (OD)', fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '10_monthly_pass_top_10_od_pairs.png'))
    plt.close(); print(" -> 圖表 10 已儲存。")

    # 11. 月票用戶搭車時段分佈 (平日/假日折線圖)
    print("\n[圖表 11] 產生月票用戶平日與假日搭車時段分佈圖...")
    # 【V2 修改】直接使用 '日期類型' 和 '上車小時'
    hourly_usage_pass = monthly_pass_users_df.groupby(['日期類型', '上車小時']).size().reset_index(name='搭乘次數')

    print("\n--- [分析結果 11] 月票用戶平日與假日各時段搭乘次數分佈 ---")
    print(hourly_usage_pass.pivot(index='上車小時', columns='日期類型', values='搭乘次數').fillna(0))
    print("------------------------------------------------------------\n")
    
    plt.figure(figsize=(12, 7))
    sns.lineplot(data=hourly_usage_pass, x='上車小時', y='搭乘次數', hue='日期類型', marker='o', palette=['#1f77b4', '#ff7f0e'])
    plt.title('月票用戶平日與假日各時段搭乘次數分佈', fontsize=16)
    plt.xlabel('小時 (24小時制)', fontsize=12); plt.ylabel('搭乘次數', fontsize=12)
    plt.xticks(np.arange(0, 24, 1)); plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.legend(title='日類型'); plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '11_monthly_pass_hourly_usage_weekday_weekend.png'))
    plt.close(); print(" -> 圖表 11 已儲存。")
    
    # 12. Top 20 高頻率月票用戶排行
    print("\n[圖表 12] 產生高頻率月票用戶排行圖...")
    top_20_users_series = monthly_pass_users_df['卡號'].value_counts().head(20)
    masked_card_ids = [f"...{cid[-4:]}" for cid in top_20_users_series.index]
    
    top_20_df_display = pd.DataFrame({
        '卡號 (末四碼)': masked_card_ids, 
        '總搭乘次數': top_20_users_series.values
    }).set_index('卡號 (末四碼)')
    print("\n--- [分析結果 12] 搭乘次數最高的前 20 名月票用戶 ---")
    print(top_20_df_display)
    print("------------------------------------------------------\n")
    
    plt.figure(figsize=(12, 10))
    sns.barplot(y=masked_card_ids, x=top_20_users_series.values, hue=masked_card_ids, palette='coolwarm', orient='h', legend=False)
    plt.title('搭乘次數最高的前 20 名月票用戶', fontsize=16)
    plt.xlabel('總搭乘次數', fontsize=12); plt.ylabel('卡號 (末四碼)', fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '12_monthly_pass_top_20_users.png'))
    plt.close(); print(" -> 圖表 12 已儲存。")

    # 13. 高頻率月票用戶深度分析
    print("\n--- [區塊 13] 高頻率月票用戶深度分析 ---")
    
    top_20_users_df = top_20_users_series.reset_index()
    top_20_users_df.columns = ['卡號', '總搭乘次數']
    
    user_charts_dir = os.path.join(output_dir, 'top_20_user_profiles')
    os.makedirs(user_charts_dir, exist_ok=True)
    print(f"個人化用戶圖表將儲存於: {user_charts_dir}")

    for index, user in top_20_users_df.iterrows():
        card_id = user['卡號']
        masked_card_id = f"...{card_id[-4:]}"
        user_data = monthly_pass_users_df[monthly_pass_users_df['卡號'] == card_id].copy()
        
        user_data['OD'] = user_data['上車站名'] + ' -> ' + user_data['下車站名']
        most_common_od = user_data['OD'].mode()[0] if not user_data['OD'].mode().empty else "無"
        routes_summary = user_data['路線'].value_counts()
        # 【V2 修改】使用 '上車小時'
        user_hours = user_data['上車小時'].value_counts().sort_index()

        print(f"\n--- [用戶分析] {masked_card_id} ---")
        print(f"總搭乘次數: {user['總搭乘次數']}")
        print(f"最常搭乘 OD: {most_common_od}")
        print("\n常用路線及次數:")
        print(routes_summary)
        print("\n各時段搭乘分佈:")
        print(user_hours)
        print("-" * 30)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7), gridspec_kw={'width_ratios': [1, 2]})
        
        ax1.axis('off')
        title_text = f"高頻率用戶分析: {masked_card_id}"
        od_text = f"最常搭乘OD: {most_common_od}"
        routes_text = "常用路線及次數:\n"
        for route, count in routes_summary.items():
            routes_text += f"  - 路線 {route}: {count} 次\n"
        
        full_text = f"{title_text}\n\n{od_text}\n\n{routes_text}"
        ax1.text(0.05, 0.95, full_text, transform=ax1.transAxes,
                 fontsize=14, verticalalignment='top', family='sans-serif', wrap=True)

        sns.barplot(x=user_hours.index, y=user_hours.values, color='coral', ax=ax2)
        ax2.set_title('各時段搭乘分佈', fontsize=16)
        ax2.set_xlabel('小時 (24小時制)')
        ax2.set_ylabel('搭乘次數')

        fig.tight_layout()
        plt.savefig(os.path.join(user_charts_dir, f'user_{masked_card_id}.png'))
        plt.close(fig)
        
        print(f"  -> 已儲存用戶 {masked_card_id} 的個人化合併分析圖表。")
        
        # 檢查單日搭乘是否超過5次
        user_data['上車日期'] = user_data['上車時間'].dt.date
        daily_rides = user_data.groupby('上車日期').size()
        high_freq_days = daily_rides[daily_rides > 5]
        
        if not high_freq_days.empty:
            print(f"\033[93m  -> [注意] 用戶 {masked_card_id} 有單日搭乘超過5次的情況：\033[0m")
            for ride_date, count in high_freq_days.items():
                print(f"\033[93m     - 日期: {ride_date}, 搭乘次數: {count}\033[0m")


    print("\n所有分析與圖表產生完畢！")

if __name__ == '__main__':
    analyze_and_visualize_bus_data()