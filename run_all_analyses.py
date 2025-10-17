# 檔名: run_all_analyses.py (V4 - 整合轉乘分析)
# 請將此檔案放在專案的根目錄下 (與 "市區公車", "台鐵" 等資料夾同層)

import os
import subprocess
import sys
import time
import config # 匯入設定檔以檢查轉乘分析設定

# =============================================================================
#  輔助函式
# =============================================================================

def run_script(script_path):
    """
    在指定的路徑下執行一個 Python 腳本。
    """
    script_dir = os.path.dirname(script_path)
    script_name = os.path.basename(script_path)
    original_dir = os.getcwd()
    
    print(f"\n{'='*25}")
    print(f"  即將執行: {script_name}")
    print(f"  目標路徑: {os.path.abspath(script_dir)}")
    print(f"{'='*25}")
    
    if script_dir:
        os.chdir(script_dir)
        
    try:
        process = subprocess.run(
            [sys.executable, script_name], 
            check=True, 
            capture_output=True, 
            text=True,
            errors='replace'
        )
        print("--- [腳本輸出] ---")
        if process.stdout:
            print(process.stdout)
        else:
            print("(此腳本無標準輸出)")
        print("--- [輸出結束] ---")
        print(f"✅ {script_name} 執行成功！")
        
    except FileNotFoundError:
        print(f"❌ 錯誤：找不到腳本 '{script_name}' 於路徑 '{script_dir}'。")
    except subprocess.CalledProcessError as e:
        print(f"❌ 錯誤：執行 {script_name} 時發生問題。")
        print("--- [錯誤訊息] ---")
        if e.stderr:
            print(e.stderr)
        if e.stdout:
            print("--- [錯誤發生前的輸出] ---")
            print(e.stdout)
        print("--- [錯誤結束] ---")
        sys.exit(f"由於上述錯誤，分析流程已中止。")
    except Exception as e:
        print(f"❌ 發生未預期的錯誤: {e}")
        sys.exit(f"分析流程已中止。")
    finally:
        os.chdir(original_dir)
        time.sleep(1)

# =============================================================================
#  主執行流程
# =============================================================================

def main():
    """
    定義所有分析腳本的執行順序。
    """
    start_time = time.time()
    print("🚀 開始執行全部分析流程...")
    print("將會依據 'config.py' 的設定進行分析。")

    # --- 流程 1: 市區公車分析 ---
    print("\n--- [階段一：市區公車分析] ---")
    run_script('市區公車/unify_data.py')
    run_script('市區公車/main_analyze_市區公車.py')
    run_script('市區公車/199_399_analyze.py')

    # --- 流程 2: 乘客分群分析 ---
    print("\n--- [階段二：乘客分群分析 (Cluster Analysis)] ---")
    run_script('cluster_analysis.py')

    # --- 流程 3: 台鐵資料分析 ---
    print("\n--- [階段三：台鐵資料分析] ---")
    run_script('台鐵/main_analysis_台鐵.py')
    
    # --- 流程 4: 公路客運分析 ---
    print("\n--- [階段四：公路客運分析] ---")
    run_script('公路客運/日統/analyze.py')
    run_script('公路客運/嘉義/analyze.py')
    
    # --- 流程 5: 轉乘行為分析 (可選) ---
    print("\n--- [階段五：轉乘行為分析] ---")
    if config.BUS_TRANSFER_STATION and config.TRA_TRANSFER_STATION:
        print("偵測到已設定轉乘分析目標車站，即將開始分析...")
        run_script('市區公車/station_transfer_analyze.py')
        run_script('台鐵/station_transfer_analyze.py')
    else:
        print("在 'config.py' 中未設定轉乘分析的目標車站 (BUS_TRANSFER_STATION 或 TRA_TRANSFER_STATION)。")
        print("已跳過此分析階段。")


    end_time = time.time()
    print("\n🎉🎉🎉 恭喜！所有分析流程已全部執行完畢！ 🎉🎉🎉")
    print(f"總耗時: {end_time - start_time:.2f} 秒")

if __name__ == '__main__':
    script_directory = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_directory)
    
    if not os.path.exists('config.py'):
        print("❌ 致命錯誤：找不到設定檔 'config.py'！")
        sys.exit("分析流程中止。")
        
    main()