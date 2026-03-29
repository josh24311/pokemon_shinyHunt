import cv2
import numpy as np
import time
import serial
import requests

# --- 硬體與通訊設定 ---
SERIAL_PORT = 'COM8'  # 確定為 CP2102 所在的編號
BAUD_RATE = 9600
count = 0

# --- 偵測座標 (請依你的擷取卡畫面微調) ---
# 神獸區域 (ROI_2)
SHINY_X, SHINY_Y, SHINY_W, SHINY_H = 367, 8, 140, 180 
# 對話框區域 (ROI_1)
DIALOG_X, DIALOG_Y, DIALOG_W, DIALOG_H = 79, 347, 294, 93 

SHINY_THRESHOLD = 95.5   # 低於此值判定為色違
DIALOG_THRESHOLD = 97.0  # 高於此值觸發判定

# --- 預載模板 ---
def get_lab_avg(path, w, h):
    img = cv2.imread(path)
    img_resized = cv2.resize(img, (w, h))
    lab = cv2.cvtColor(img_resized, cv2.COLOR_BGR2Lab)
    return np.array(cv2.mean(lab)[:3])

avg_dialog = get_lab_avg('battle_ready.png', DIALOG_W, DIALOG_H)
avg_shiny = get_lab_avg('template.png', SHINY_W, SHINY_H)

# --- 初始化 Serial 連線 ---
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2) # 等待序列埠穩定
    print(f"✅ 已成功連線至 CP2102 ({SERIAL_PORT})")
except Exception as e:
    print(f"❌ 錯誤：無法開啟 {SERIAL_PORT}。請確認 CP2102 是否插好！")
    print(f"錯誤訊息: {e}")
    exit()

# [函式] Discord 發送
def send_discord_shiny(count, score, image_path):
    webhook_url = "YOUR_WEBHOOK_URL"
    message = f"**發現色違！**\n> 嘗試次數：第 `{count}` 次\n> 判定分數：`{score:.2f}`\n> 狀態：系統已物理煞車，請回家收成！"
    payload = {"content": message}
    try:
        with open(image_path, "rb") as f:
            files = {"file": (image_path, f, "image/png")}
            r = requests.post(webhook_url, data=payload, files=files)
            print(f"Discord 通知發送成功！ (嘗試次數: {count})")
    except Exception as e:
        print(f"發送失敗: {e}")

def main():
    global count
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    is_battle_confirmed = False
    
    print("--- 1/8192 全自動色違獵人系統：監控中 ---")
    while True:
        ret, frame = cap.read()
        if not ret: break

        # 1. 偵測對話框 (計算分數)
        roi_d = frame[DIALOG_Y:DIALOG_Y+DIALOG_H, DIALOG_X:DIALOG_X+DIALOG_W]
        lab_d = cv2.cvtColor(roi_d, cv2.COLOR_BGR2Lab)
        avg_d = np.array(cv2.mean(lab_d)[:3])
        score_d = max(0, 100 - np.linalg.norm(avg_dialog - avg_d))

        # 2. 觸發判定邏輯
        if score_d > DIALOG_THRESHOLD and not is_battle_confirmed:
            count += 1
            print(f"[{time.strftime('%H:%M:%S')}] 第 {count} 次嘗試.偵測到對話框，準備判定顏色...")
            # time.sleep(0.5) # 緩衝，確保畫面完全定格
            
            ret, frame_focus = cap.read()
            roi_s = frame_focus[SHINY_Y:SHINY_Y+SHINY_H, SHINY_X:SHINY_X+SHINY_W]
            lab_s = cv2.cvtColor(roi_s, cv2.COLOR_BGR2Lab)
            avg_s = np.array(cv2.mean(lab_s)[:3])
            score_s = max(0, 100 - np.linalg.norm(avg_shiny - avg_s))
            
            print(f" >> 神獸顏色分數: {score_s:.2f}")           
            if score_s < SHINY_THRESHOLD:
                # 1. 第一優先：發送物理煞車指令
                try:
                    ser.write(b'S') 
                    print("！！！發現色違！！！ 指令已發送，Pro Micro 已鎖死。")
                except Exception as e:
                    print(f"警告：Serial 指令發送失敗！{e}")

                # 2. 第二優先：本地存檔（這是不需要網路的，最穩）
                filename = f"SHINY_{int(time.time())}.png"
                cv2.imwrite(filename, frame_focus)
                print(f"已本地存檔：{filename}")

                # 3. 第三優先：遠端通知 (包在 try 裡面，失敗也不影響 break)
                try:
                    send_discord_shiny(count, score_s, filename)
                except Exception as e:
                    print(f"遠端通知失敗（但不影響停機）：{e}")

                # 4. 終極保險：無論如何都跳出迴圈，停止監控
                print("系統監控已停止。")
                break
            else:
                print(" >> 非色違，繼續循環。")
                is_battle_confirmed = True
        
        # 3. 重置監控 (當對話框消失時)
        elif score_d < (DIALOG_THRESHOLD - 10) and is_battle_confirmed:
            is_battle_confirmed = False

        # 顯示即時畫面 (Debug 用)
        cv2.rectangle(frame, (DIALOG_X, DIALOG_Y), (DIALOG_X+DIALOG_W, DIALOG_Y+DIALOG_H), (255,0,0), 2)
        cv2.rectangle(frame, (SHINY_X, SHINY_Y), (SHINY_X+SHINY_W, SHINY_Y+SHINY_H), (0,255,0), 2)
        cv2.imshow('Shiny Hunter Monitor', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    ser.close()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
