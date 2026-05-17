# Log Format

## Rogue AP

{
"timestamp": "2026-05-09T12:00:00Z",
"event_type": "rogue_ap_detected",
"ssid": "Company-WiFi",
"legit_bssid": "AA:BB:CC:11:22:33",
"detected_bssid": "66:77:88:99:AA:BB",
"channel": 6,
"rssi": -42,
"severity": "high",
"message": "SSID matches legitimate AP but BSSID is unknown"
}

## Deauth

{
"timestamp": "2026-05-09T12:05:00Z",
"event_type": "deauth_attack_detected",
"source_mac": "11:22:33:44:55:66",
"destination_mac": "ff:ff:ff:ff:ff:ff",
"ap_bssid": "AA:BB:CC:11:22:33",
"count": 35,
"window_seconds": 10,
"severity": "high"
}
