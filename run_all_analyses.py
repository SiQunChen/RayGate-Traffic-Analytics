# 檔名: run_all_analyses.py (V6 - 公路客運流程更新)

import os
import subprocess
import sys
import time
import config # 匯入設定檔

# =============================================================================
#  輔助函式 (此部分不變)
# =============================================================================

def run_script(script_path):
    """
    在指定的路徑下執行一個 Python 腳本。
    """
    # 執行腳本時，暫時切換到腳本所在的目錄，以確保相對路徑讀取正確
    script_dir = os.path.dirname(script_path)
    script_name = os.path.basename(script_path)
    original_dir = os.getcwd()
    
    print(f"\n{'='*25}")
    print(f"  即將執行: {script_name}")
    print(f"  目標路徑: {os.path.abspath(script_path)}")
    print(f"{'='*25}")
    
    # 執行前切換工作目錄到腳本所在位置
    if script_dir:
        os.chdir(script_dir)
        
    try:
        # 執行時，不再需要傳遞路徑，因為已經在那個資料夾裡了
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
        print(f"❌ 錯誤：找不到腳本 '{script_name}'。")
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
        # 無論成功或失敗，都切換回原始的工作目錄
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
    
    # 取得 code 資料夾的路徑
    code_dir = config.CODE_BASE_DIR

    # # --- 流程 1: 市區公車分析 ---
    # print("\n--- [階段一：市區公車分析] ---")
    # run_script(os.path.join(code_dir, '市區公車', 'data_loader_市區公車.py'))
    # run_script(os.path.join(code_dir, '市區公車', 'main_analyze_市區公車.py'))
    # run_script(os.path.join(code_dir, '市區公車', 'analyze_定期票.py'))

    # # --- 流程 2: 乘客分群分析 ---
    # print("\n--- [階段二：乘客分群分析 (Cluster Analysis)] ---")
    # run_script(os.path.join(code_dir, 'cluster_analysis.py'))

    # --- 流程 3: 台鐵資料分析 ---
    print("\n--- [階段三：台鐵資料分析] ---")
    run_script(os.path.join(code_dir, '台鐵', 'main_analysis_台鐵.py'))
    
    # # --- 流程 4: 公路客運分析 ---
    # print("\n--- [階段四：公路客運分析] ---")
    # run_script(os.path.join(code_dir, '公路客運', 'data_loader_公路客運.py'))
    # run_script(os.path.join(code_dir, '公路客運', 'main_analyze_公路客運.py'))
    # run_script(os.path.join(code_dir, '公路客運', 'analyze_定期票.py'))
    
    # # --- 流程 5: 轉乘行為分析 (可選) ---
    # print("\n--- [階段五：轉乘行為分析] ---")
    # if config.BUS_TRANSFER_STATION or config.TRA_TRANSFER_STATION:
    #     print("偵測到已設定轉乘分析目標車站，即將開始分析...")
    #     if config.BUS_TRANSFER_STATION:
    #         run_script(os.path.join(code_dir, '市區公車', 'station_transfer_analyze.py'))
    #     if config.TRA_TRANSFER_STATION:
    #         run_script(os.path.join(code_dir, '台鐵', 'station_transfer_analyze.py'))
    # else:
    #     print("在 'config.py' 中未設定轉乘分析的目標車站。")
    #     print("已跳過此分析階段。")

    end_time = time.time()
    print("\n🎉🎉🎉 恭喜！所有分析流程已全部執行完畢！ 🎉🎉🎉")
    print(f"總耗時: {end_time - start_time:.2f} 秒")

if __name__ == '__main__':
    # 確保不論從哪裡執行此腳本，都能找到 config.py
    script_directory = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_directory)
    
    if not os.path.exists('config.py'):
        print("❌ 致命錯誤：找不到設定檔 'config.py'！")
        sys.exit("分析流程中止。")
        
    main()