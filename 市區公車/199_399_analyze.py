import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

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

# --- 票種統一化函式 (使用者提供) ---

# 定義各類票種的集合，以提高查詢效率
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
    """
    根據詳細的票種列表，將票種名稱統一分類。
    """
    ticket_name_str = str(ticket_name).strip() # .strip() 移除前後空白

    if ticket_name_str in REGULAR_TICKETS:
        return '定期票'
    elif ticket_name_str in ORDINARY_TICKETS:
        return '普通'
    elif ticket_name_str in CONCESSIONARY_TICKETS:
        return '優待'
    elif ticket_name_str in STUDENT_TICKETS:
        return '學生'
    elif ticket_name_str in TOKEN_CARDS:
        return '代幣卡'
    else:
        return '其他'

def analyze_and_visualize_bus_data(file_path='unified_data.csv'):
    """
    分析雲林市區公車資料，對月票與非月票用戶進行視覺化分析並儲存圖表。
    """
    setup_visualization()
    output_dir = '199_399_charts'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"已建立資料夾: {output_dir}")

    try:
        df = pd.read_csv(file_path, dtype={'路線': str, '司機': str, '車號': str, '卡號': str})
        print(f"成功讀取資料，總共有 {len(df)} 筆記錄。")
    except FileNotFoundError:
        print(f"錯誤：找不到檔案 '{file_path}'。請確認檔案路徑是否正確。")
        return
    
    # --- 資料前處理 ---
    df['上車時間'] = pd.to_datetime(df['上車時間'], errors='coerce')
    df.dropna(subset=['上車時間'], inplace=True)
    df = df[df['上車時間'] >= '2024-07-01'].copy()
    print(f"篩選 2024-07-01 以後的資料，剩餘 {len(df)} 筆記錄。")
    if df.empty:
        print("警告：篩選後無資料可分析。")
        return
    df['月份'] = df['上車時間'].dt.month
    df['上車時段'] = df['上車時間'].dt.hour
    df['星期'] = df['上車時間'].dt.dayofweek
    df['日類型'] = np.where(df['星期'] < 5, '平日', '假日')

    # --- 使用者分類 (月票/非月票) ---
    tickets_199 = ['悠遊-雲林縣199', '一卡通-雲林縣199', '愛金卡-雲林縣199', '雲林縣內通勤', '雲林']
    tickets_399 = ['大雲林區', '雲嘉嘉', '一卡通-雲林縣399', '愛金卡-雲林縣399', '悠遊-雲林縣399']
    conditions = [df['票種名稱'].isin(tickets_199), df['票種名稱'].isin(tickets_399)]
    choices = ['199月票', '399月票']
    df['月票類型'] = np.select(conditions, choices, default='非月票')
    
    monthly_pass_users_df = df[df['月票類型'] != '非月票'].copy()
    non_monthly_pass_users_df = df[df['月票類型'] == '非月票'].copy()
    
    # 【新增】提示使用者即將開始輸出分析結果
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
        # *** 新增處：在分析前，統一化非月票用戶的票種名稱 ***
        print("正在統一化【非月票用戶】的票種名稱...")
        # 使用 .loc 避免 SettingWithCopyWarning 警告
        non_monthly_pass_users_df.loc[:, '票種名稱'] = non_monthly_pass_users_df['票種名稱'].apply(unify_ticket_type)
        print("票種名稱統一化完成。")

        # *** 新增處：移除票種為「優待」的資料 ***
        print(f"統一化後，非月票用戶共有 {len(non_monthly_pass_users_df)} 筆資料。")
        original_count = len(non_monthly_pass_users_df)
        non_monthly_pass_users_df = non_monthly_pass_users_df[non_monthly_pass_users_df['票種名稱'] != '優待'].copy()
        removed_count = original_count - len(non_monthly_pass_users_df)
        print(f"正在移除票種為「優待」的資料... 已移除 {removed_count} 筆。")
        print(f"移除後，剩餘 {len(non_monthly_pass_users_df)} 筆非月票用戶資料進行分析。")

        if non_monthly_pass_users_df.empty:
            print("警告：移除『優待』票種後，已無資料可供分析。")
            return
        
        # 1. 非月票用戶高額消費分析
        print("\n[圖表 1] 產生非月票用戶高額消費人數圖...")
        monthly_spending = non_monthly_pass_users_df.groupby(['月份', '卡號'])['消費扣款'].sum().reset_index()
        chart_data = []
        for month in sorted(monthly_spending['月份'].unique()):
            month_data = monthly_spending[monthly_spending['月份'] == month]
            spent_between_199_399 = month_data[(month_data['消費扣款'] > 199) & (month_data['消費扣款'] < 399)]['卡號'].nunique()
            spent_over_399 = month_data[month_data['消費扣款'] > 399]['卡號'].nunique()
            chart_data.append({'月份': month, '消費門檻': '199-399 元', '人數': spent_between_199_399})
            chart_data.append({'月份': month, '消費門檻': '> 399 元', '人數': spent_over_399})
        chart_df = pd.DataFrame(chart_data)
        
        # 【新增】印出分析結果
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
        
        # 【新增】印出分析結果
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
        
        # 【新增】印出分析結果
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
        hourly_usage_non_pass = non_monthly_pass_users_df.groupby(['日類型', '上車時段']).size().reset_index(name='搭乘次數')
        
        # 【新增】印出分析結果
        print("\n--- [分析結果 4] 非月票用戶平日與假日各時段搭乘次數分佈 ---")
        print(hourly_usage_non_pass.pivot(index='上車時段', columns='日類型', values='搭乘次數').fillna(0))
        print("------------------------------------------------------------\n")
        
        plt.figure(figsize=(12, 7))
        sns.lineplot(data=hourly_usage_non_pass, x='上車時段', y='搭乘次數', hue='日類型', marker='o', palette=['#1f77b4', '#ff7f0e'])
        plt.title('非月票用戶平日與假日各時段搭乘次數分佈', fontsize=16)
        plt.xlabel('小時 (24小時制)', fontsize=12); plt.ylabel('搭乘次數', fontsize=12)
        plt.xticks(np.arange(0, 24, 1)); plt.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.legend(title='日類型'); plt.tight_layout()
        plt.savefig(os.path.join(output_dir, '4_non_pass_hourly_usage_weekday_weekend.png'))
        plt.close(); print(" -> 圖表 4 已儲存。")

        # 5. 消費介於 199-399 元用戶的熱門 OD
        print("\n[圖表 5] 產生非月票高額消費(199-399元)用戶熱門OD圖...")
        cards_between_199_399 = monthly_spending[(monthly_spending['消費扣款'] > 199) & (monthly_spending['消費扣款'] < 399)]['卡號'].unique()
        high_spenders_199_df = non_monthly_pass_users_df[non_monthly_pass_users_df['卡號'].isin(cards_between_199_399)]
        if not high_spenders_199_df.empty:
            complete_trips_high_199 = high_spenders_199_df[high_spenders_199_df['旅次是否完整'] == True].copy()
            complete_trips_high_199['OD'] = complete_trips_high_199['上車站名'] + ' -> ' + complete_trips_high_199['下車站名']
            top_od_high_199 = complete_trips_high_199['OD'].value_counts().head(10)
            
            # 【新增】印出分析結果
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
            
            # 【新增】印出分析結果
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
        
        # 【新增】印出分析結果
        ticket_percentages = (ticket_type_counts / ticket_type_counts.sum() * 100).round(2)
        ticket_distribution_df = pd.DataFrame({'搭乘次數': ticket_type_counts, '佔比(%)': ticket_percentages})
        print("\n--- [分析結果 7] 非月票用戶票種分類佔比 ---")
        print(ticket_distribution_df)
        print("--------------------------------------------\n")
        
        main_tickets = ticket_type_counts # 顯示所有類別

        plt.figure(figsize=(12, 10))
        wedges, texts, autotexts = plt.pie(main_tickets, autopct='%1.1f%%', startangle=140, pctdistance=0.85)
        plt.legend(wedges, main_tickets.index, title="票種分類", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        plt.title('非月票用戶票種分類佔比', fontsize=16)
        plt.setp(autotexts, size=10, weight="bold")
        plt.axis('equal')
        plt.tight_layout()
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
    
    # 【新增】印出分析結果
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

    # 【新增】印出分析結果
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
    
    # 【新增】印出分析結果
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
    hourly_usage_pass = monthly_pass_users_df.groupby(['日類型', '上車時段']).size().reset_index(name='搭乘次數')

    # 【新增】印出分析結果
    print("\n--- [分析結果 11] 月票用戶平日與假日各時段搭乘次數分佈 ---")
    print(hourly_usage_pass.pivot(index='上車時段', columns='日類型', values='搭乘次數').fillna(0))
    print("------------------------------------------------------------\n")
    
    plt.figure(figsize=(12, 7))
    sns.lineplot(data=hourly_usage_pass, x='上車時段', y='搭乘次數', hue='日類型', marker='o', palette=['#1f77b4', '#ff7f0e'])
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
    
    # 【新增】印出分析結果
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
        user_hours = user_data['上車時段'].value_counts().sort_index()

        # 【新增】印出該用戶的詳細分析結果
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
            # 使用 ANSI escape code 顯示黃色警告
            print(f"\033[93m  -> [注意] 用戶 {masked_card_id} 有單日搭乘超過5次的情況：\033[0m")
            for ride_date, count in high_freq_days.items():
                print(f"\03f[93m     - 日期: {ride_date}, 搭乘次數: {count}\033[0m")


    print("\n所有分析與圖表產生完畢！")

if __name__ == '__main__':
    analyze_and_visualize_bus_data('unified_data.csv')