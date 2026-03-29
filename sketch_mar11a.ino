#include <NintendoSwitchControlLibrary.h>

void setup() {
    // --- 【第0階段：初始化Serial控制】 ---
    Serial1.begin(9600);
    pinMode(LED_BUILTIN, OUTPUT);
    // --- 【第一階段：初始化連線與回歸遊戲】 ---

    pushButton(Button::A, 100, 3); 
    
    // 【關鍵】給系統足夠時間跑完「配對成功」動畫
    delay(2500); 

    // 2. B 退出「更改拿法」頁面
    pushButton(Button::B, 100); 
    // 給系統 1.5 秒反應時間回到「控制器」設定頁
    delay(1500); 

    // 3. B 退出「控制器」設定頁回到「Home 主畫面」
    pushButton(Button::B, 100); 
    delay(1500);
    
    // 4. 再補一個 B 作為保險（防止有殘留彈窗）
    pushButton(Button::B, 100); 
    delay(1500);

    // 4. 方向鍵導航：上 -> 左 -> 左 (回到遊戲圖示)
    pushHat(Hat::UP, 200);   delay(500);
    pushHat(Hat::LEFT, 200); delay(500);
    pushHat(Hat::LEFT, 200); delay(500);

    // 5. A 進入遊戲
    pushButton(Button::A, 500); 
    delay(3000); // 給遊戲 3 秒的時間恢復畫面
}

void loop() {
    if (Serial1.available() > 0) {
        if (Serial1.read() == 'S') {
            while(1) {
                TXLED1;
                RXLED1;
                delay(100);
                TXLED0;
                TXLED0;
                delay(100);
            }
        }
    }
    // --- 【第二階段：刷怪循環】 ---

    holdButton(Button::A | Button::B | Button::X | Button::Y, 500);

    delay(3000); // 重啟緩衝

    // 2. 啟動遊戲 (你的黃金秒數 6s + 6s)
    pushButton(Button::A, 200); delay(6000); 
    pushButton(Button::A, 200); delay(6000);

    // 3. 進入存檔並對話 (A 鍵 9 次) . 此為原地神獸版本, 視目標調整
    for (int i = 0; i < 10; i++) {
        pushButton(Button::A, 200);
        delay(1000);
    }

    // 4. 戰鬥動畫等待 (16s)
    delay(16000);


}