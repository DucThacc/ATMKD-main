# Common Issues and Fixes

## 1) No interface in monitor mode

- Check adapter supports monitor mode.
- Run: sudo airmon-ng check kill
- Start: sudo airmon-ng start wlan0
- If using VM, enable USB passthrough for the Wi-Fi adapter.

## 2) No packets captured

- Ensure correct interface (wlan0mon).
- Move closer to AP.
- Verify: sudo airodump-ng wlan0mon

## 3) Permission error

- Run sniff with sudo.
- Ensure venv is activated.

## 3.1) ModuleNotFoundError: No module named 'yaml'

- Install dependencies into the project venv: `.venv/bin/pip install -r requirements.txt`
- If you created the venv but did not install requirements, PyYAML will be missing.

## 3.2) `uvicorn: command not found`

- Use module invocation instead of the binary: `sudo .venv/bin/python -m uvicorn webapp.app:app --host 0.0.0.0 --port 8000`
- If that still fails, reinstall requirements inside the venv.

## 4) Scapy not seeing RSSI

- Not all adapters expose dBm_AntSignal.
- RSSI can be None, this is normal.

## 5) OpenSearch not reachable

- Check docker compose status.
- Confirm endpoint: http://localhost:9200

## 6) Telegram alert not sent

- Validate bot token and chat id.
- Ensure internet access from host.
