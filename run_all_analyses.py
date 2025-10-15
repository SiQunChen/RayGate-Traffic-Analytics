# run_all_analyses.py (最終更新版)
import os
import sys
import argparse
from datetime import datetime

# --- 將專案內的子資料夾加入 Python 的搜尋路徑 ---
sys.path.append(os.path.abspath('city_bus'))
sys.path.append(os.path.abspath('tra'))
sys.path.append(os.path.abspath('intercity_bus/chiayi'))
sys.path.append(os.path.abspath('intercity_bus/jitong'))

# --- 匯入模組 ---
import unify_data
import main_analyze_市區公車 as main_analyze_city_bus
import station_analyzer as city_bus_station_analyzer
import main_analysis_台鐵 as main_analysis_tra
import station_analyzer as tra_station_analyzer
import analyze as analyze_chiayi
import analyze as analyze_jitong

def run_city_bus_analysis(station_name, perform_station_analysis):
    """
    執行所有市區公車相關的分析。
    Args:
        station_name (str): 要深度分析的車站名稱。
        perform_station_analysis (bool): 是否執行特定車站的深度分析。
    """
    print("\n" + "="*50)
    print("  🚌 開始執行【市區公車】(city_bus)資料分析流程...")
    print("="*50)

    # 步驟 1: 整合原始 Excel 檔
    print("\n--- 步驟 1: 整合與清洗原始資料 ---")
    unify_data.main(input_dir='source_data/city_bus', output_file='city_bus/unified_data.csv')

    # 步驟 2: 執行主要分析
    print("\n--- 步驟 2: 執行主要運量分析 ---")
    main_analyze_city_bus.run_analysis(filepath='city_bus/unified_data.csv')

    # 步驟 3: 【修改點】根據參數決定是否執行深度分析
    if perform_station_analysis:
        print(f"\n--- 步驟 3: 執行 {station_name} 深度分析 ---")
        city_bus_station_analyzer.run_analysis(filepath='city_bus/unified_data.csv', station_name=station_name)
    else:
        print("\n--- 步驟 3: 已跳過特定車站深度分析 (可使用 --station-analysis 旗標來啟用) ---")

    print("\n✅ 【市區公車】(city_bus)分析完成！")

def run_tra_analysis(station_name, perform_station_analysis):
    """
    執行所有台鐵相關的分析。
    Args:
        station_name (str): 要深度分析的車站名稱。
        perform_station_analysis (bool): 是否執行特定車站的深度分析。
    """
    print("\n" + "="*50)
    print("  🚆 開始執行【台鐵】(tra)資料分析流程...")
    print("="*50)

    # 步驟 1: 載入並清理台鐵資料
    print("\n--- 步驟 1: 載入與清洗原始資料 ---")
    os.system(f"python tra/data_loader.py --data_dir source_data/tra --output_file tra/cleaned_tra_data.csv")

    # 步驟 2: 執行主要分析
    print("\n--- 步驟 2: 執行彰化-嘉義區間整體分析 ---")
    main_analysis_tra.run_analysis(data_path='tra/cleaned_tra_data.csv')
    
    # 步驟 3: 【修改點】根據參數決定是否執行深度分析
    if perform_station_analysis:
        print(f"\n--- 步驟 3: 執行 {station_name} 車站深度分析 ---")
        tra_station_analyzer.run_analysis(data_path='tra/cleaned_tra_data.csv', station_name=station_name)
    else:
        print("\n--- 步驟 3: 已跳過特定車站深度分析 (可使用 --station-analysis 旗標來啟用) ---")
    
    print("\n✅ 【台鐵】(tra)分析完成！")


def run_intercity_bus_analysis():
    """執行所有公路客運相關的分析"""
    print("\n" + "="*50)
    print("  🚍 開始執行【公路客運】(intercity_bus)資料分析流程...")
    print("="*50)

    # 執行嘉義客運分析
    print("\n--- 正在分析【嘉義客運】 ---")
    analyze_chiayi.main(data_folder='source_data/intercity_bus/chiayi')

    # 執行日統客運分析
    print("\n--- 正在分析【日統客運】 ---")
    analyze_jitong.main(data_folder='source_data/intercity_bus/jitong')
    
    print("\n✅ 【公路客運】(intercity_bus)分析完成！")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="一鍵執行交通數據分析專案",
        formatter_class=argparse.RawTextHelpFormatter # 美化 help 訊息的排版
    )
    parser.add_argument(
        'analysis_type',
        nargs='?',
        default='all',
        choices=['all', 'city_bus', 'tra', 'intercity_bus'],
        help="選擇要執行的分析類型:\n"
             "  'city_bus'      - 僅執行市區公車分析\n"
             "  'tra'           - 僅執行台鐵分析\n"
             "  'intercity_bus' - 僅執行公路客運分析\n"
             "  'all'           - (預設) 執行所有分析"
    )
    # 【新增參數】
    parser.add_argument(
        '--station-analysis',
        action='store_true',  # 這會讓參數變為一個開關，不需要接 true/false
        help="啟用針對特定車站的深度轉乘分析。若不加此參數，則預設為關閉。"
    )
    parser.add_argument(
        '--city-bus-station',
        type=str,
        default='斗六火車站',
        help="指定市區公車要深度分析的站點名稱 (需搭配 --station-analysis)。\n預設: '斗六火車站'"
    )
    parser.add_argument(
        '--tra-station',
        type=str,
        default='斗六',
        help="指定台鐵要深度分析的車站名稱 (需搭配 --station-analysis)。\n預設: '斗六'"
    )
    args = parser.parse_args()

    start_time = datetime.now()
    print(f"🚀 分析開始時間: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if args.analysis_type == 'all' or args.analysis_type == 'city_bus':
        # 【修改點】傳入新的參數
        run_city_bus_analysis(
            station_name=args.city_bus_station,
            perform_station_analysis=args.station_analysis
        )
        
    if args.analysis_type == 'all' or args.analysis_type == 'tra':
        # 【修改點】傳入新的參數
        run_tra_analysis(
            station_name=args.tra_station,
            perform_station_analysis=args.station_analysis
        )

    if args.analysis_type == 'all' or args.analysis_type == 'intercity_bus':
        run_intercity_bus_analysis()

    end_time = datetime.now()
    print(f"\n🎉 全部分析結束時間: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️ 總耗時: {end_time - start_time}")