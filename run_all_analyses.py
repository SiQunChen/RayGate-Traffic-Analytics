# 檔名: run_all_analyses.py (V3 - 整合 config.py)
# 請將此檔案放在專案的根目錄下 (與 "市區公車", "台鐵" 等資料夾同層)

import os
import subprocess
import sys
import time

# =============================================================================
#  輔助函式
# =============================================================================

def run_script(script_path):
    """
    在指定的路徑下執行一個 Python 腳本。

    Args:
        script_path (str): 要執行的腳本的相對路徑。
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
        # 使用 errors='replace'，讓 subprocess 自動使用系統的預設編碼，
        # 如果遇到無法解碼的字元，會用 '?' 取代，而不是讓程式崩潰。
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
    run_script('市區公車/douliu_analyze_市區公車.py')
    run_script('市區公車/199_399_analyze.py')

    # # --- 流程 2: 乘客分群分析 ---
    # print("\n--- [階段二：乘客分群分析 (Cluster Analysis)] ---")
    # print("注意：此腳本可能需要使用者手動輸入 K 值，請留意終端機提示。")
    # run_script('cluster_analysis.py')

    # # --- 流程 3: 台鐵資料分析 ---
    # print("\n--- [階段三：台鐵資料分析] ---")
    # run_script('台鐵/main_analysis_台鐵.py')
    # run_script('台鐵/douliu_analyze_台鐵.py')
    
    # --- 流程 4: 公路客運分析 ---
    print("\n--- [階段四：公路客運分析] ---")
    run_script('公路客運/日統/analyze.py')
    run_script('公路客運/嘉義/analyze.py')

    end_time = time.time()
    print("\n🎉🎉🎉 恭喜！所有分析流程已全部執行完畢！ 🎉🎉🎉")
    print(f"總耗時: {end_time - start_time:.2f} 秒")

if __name__ == '__main__':
    # 確保當前工作目錄是此腳本所在的目錄
    script_directory = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_directory)
    
    # 檢查設定檔是否存在
    if not os.path.exists('config.py'):
        print("❌ 致命錯誤：找不到設定檔 'config.py'！")
        print("請確保您已經在專案根目錄下建立了這個檔案。")
        sys.exit("分析流程中止。")
        
    main()