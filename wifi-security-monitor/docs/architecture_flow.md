# Architecture Flow

1. Adapter in monitor mode captures 802.11 frames
2. Python engine parses beacon/deauth frames
3. Compare SSID/BSSID with whitelist
4. Raise alerts for rogue/evil twin or deauth burst
5. Log JSONL to disk
6. Optional: send to OpenSearch or Telegram
