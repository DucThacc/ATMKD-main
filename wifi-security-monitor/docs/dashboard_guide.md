# OpenSearch Quick Guide

1. Start services

```bash
docker compose up -d
```

2. Create index

```bash
curl -XPUT http://localhost:9200/wifi-security-logs
```

3. Enable log shipping in config

- Set opensearch.enabled: true in config/config.yaml

4. Open Dashboard

- http://localhost:5601
- Create index pattern: wifi-security-logs

5. Suggested visuals

- Count of rogue_ap_detected by time
- Count of deauth_attack_detected by time
- Top detected_bssid
- Severity distribution
