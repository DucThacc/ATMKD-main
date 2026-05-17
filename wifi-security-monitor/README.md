# WiFi Security Monitor (Rogue AP + Deauth Detection)

## 1) Phan tich de tai (tom tat)

- Rogue AP: AP khong hop le tu y phat song trong he thong.
- Evil Twin: AP gia mao co SSID giong/gan giong AP that de lua client.
- Deauthentication Attack: gui nhieu frame deauth de cat ket noi client.
- WIDS: he thong giam sat khong day, phat hien bat thuong.
- Rogue AP Detection vs AP Localization: phat hien va canh bao khac voi dinh vi.
- Pham vi: chi phat hien va canh bao, khong dinh vi chinh xac AP gia.

## 2) Kien truc he thong (ASCII)

+----------------+ +-----------------+
| Legit AP | | Rogue/Evil Twin |
| SSID: legit | | SSID: legit |
+--------+-------+ +--------+--------+
| |
| Beacon/Deauth |
+-----------+-------------+
|
v
+----------------------------+
| Kali/Ubuntu Monitor Node |
| USB WiFi in monitor mode |
+-------------+--------------+
|
v
+----------------------------+
| Python Detection Engine |
| - Rogue AP detection |
| - Deauth detection |
+-------------+--------------+
|
v
+----------------------------+
| JSONL Log File |
| logs/wifi_alerts.jsonl |
+-------------+--------------+
|
v
+----------------------------+
| OpenSearch / ELK Dashboard |
+-------------+--------------+
|
v
+----------------------------+
| Alert Console / Telegram |
+----------------------------+

## 3) Cau hinh moi truong (lab)

### Cai dat co ban

- Ubuntu/Kali moi, co quyen sudo.
- USB WiFi ho tro monitor mode.

Lenh co ban:

```bash
sudo apt update && sudo apt -y upgrade
sudo apt -y install aircrack-ng iw wireless-tools python3 python3-pip python3-venv
```

Cai thu vien Python:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Neu gap loi thieu module nhu `yaml`, hay chac chan da cai dependency vao dung virtualenv:

```bash
.venv/bin/pip install -r requirements.txt
```

Kiem tra interface:

```bash
ip link
iw dev
```

Bat monitor mode:

```bash
sudo airmon-ng check kill
sudo airmon-ng start wlan0
iwconfig
```

Kiem tra bat goi:

```bash
sudo airodump-ng wlan0mon
```

Quet mang va chon AP de quet sau (loc theo BSSID + channel):

```bash
# Quet toan bo de lay SSID/BSSID/CHANNEL
sudo airodump-ng wlan0mon

# Quet tap trung mot AP cu the
sudo airodump-ng -c <CHANNEL> --bssid <AP_BSSID> wlan0mon
```

Luu y Kali VM:

- Bat USB passthrough cho adapter Wi-Fi trong VM settings.
- Dam bao interface nhan dien duoc trong `ip link` va `iw dev`.

## 4) Cau hinh whitelist

Chinh sua [config/whitelist.json](config/whitelist.json) theo AP that:

```json
[
  {
    "ssid": "Company-WiFi",
    "bssid": "AA:BB:CC:11:22:33",
    "channel": 6,
    "encryption": "WPA2"
  }
]
```

## 5) Chay tool

```bash
sudo .venv/bin/python -m detector.main
```

## 5.1) Web UI (FastAPI)

Chay web app (trong Kali):

```bash
sudo .venv/bin/python -m uvicorn webapp.app:app --host 0.0.0.0 --port 8000
```

Mo trinh duyet:

- http://localhost:8000

Chuc nang tren web:

- Scan AP va chon target
- Them/Sua/Xoa whitelist
- Start/Stop monitor
- Xem log realtime
- Loc/tim kiem SSID/BSSID trong bang
- Bieu do realtime (rogue/deauth)

Che do chon SSID/BSSID bang menu (interactive):

- Bat trong [config/config.yaml](config/config.yaml) bang `interactive_scan: true`.
- Tool se quet nhanh 8s, hien danh sach AP, nhap so thu tu de chon.
- De bo qua va quet tat ca, chi can bam Enter.

Log se duoc ghi vao [logs/wifi_alerts.jsonl](logs/wifi_alerts.jsonl).

## 6) Test Rogue AP / Evil Twin (lab only)

Cach 1 (hotspot dien thoai):

- Dat SSID giong AP that.
- Bat hotspot va quan sat canh bao.

Cach 2 (hostapd tren Kali):

```bash
sudo apt -y install hostapd
cat <<'EOF' > /tmp/fakeap.conf
interface=wlan0
ssid=Company-WiFi
hw_mode=g
channel=6
auth_algs=1
ignore_broadcast_ssid=0
EOF
sudo hostapd /tmp/fakeap.conf
```

## 7) Test Deauthentication (lab only)

```bash
sudo aireplay-ng --deauth 20 -a <AP_BSSID> wlan0mon
```

Kiem tra terminal va log.

## 8) OpenSearch (tuy chon)

```bash
docker compose up -d
```

- Dashboards: http://localhost:5601
- Index: wifi-security-logs

Cap nhat [config/config.yaml](config/config.yaml):

- `opensearch.enabled: true`
- `opensearch.endpoint: http://localhost:9200`

## 9) Legal

Chi thuc hien trong lab cua chinh minh. Khong tan cong he thong khong duoc phep.
