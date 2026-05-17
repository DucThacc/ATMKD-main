# Test Cases - WiFi Security Monitor

| ID   | Muc tieu                               | Dieu kien dau vao            | Buoc thuc hien                       | Ket qua mong doi                | Ket qua thuc te | Trang thai |
| ---- | -------------------------------------- | ---------------------------- | ------------------------------------ | ------------------------------- | --------------- | ---------- |
| TC01 | Phat hien AP hop le                    | Whitelist co AP that         | Bat tool va de AP that phat song     | Khong canh bao                  |                 |            |
| TC02 | Phat hien Rogue AP SSID trung BSSID la | Co AP gia SSID trung         | Bat tool, bat AP gia                 | Canh bao rogue_ap_detected      |                 |            |
| TC03 | Phat hien Evil Twin                    | AP gia SSID trung/gan giong  | Bat tool, bat Evil Twin              | Canh bao rogue/suspicious       |                 |            |
| TC04 | Phat hien deauth attack                | Co AP that, co monitor iface | Chay deauth 20 frames/10s            | Canh bao deauth_attack_detected |                 |            |
| TC05 | Khong bao dong traffic binh thuong     | AP that, khong deauth        | Chay tool 5-10 phut                  | Khong canh bao                  |                 |            |
| TC06 | Log JSON dung dinh dang                | Tool dang chay               | Kiem tra file logs/wifi_alerts.jsonl | Log hop le JSONL                |                 |            |
| TC07 | Dashboard hien thi alert               | OpenSearch dang chay         | Gui log len index                    | Bieu do co du lieu              |                 |            |
