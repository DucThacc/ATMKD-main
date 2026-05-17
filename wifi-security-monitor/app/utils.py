from __future__ import annotations

import html
import json
import re
from difflib import SequenceMatcher
from typing import Any

DEFAULT_BASE_URL = "http://192.168.100.128:8000"
DEFAULT_THEME = "SOC Navy"

NAV_ITEMS = [
    ("dashboard", "Dashboard", "Executive Wi-Fi SOC overview"),
    ("monitor", "Monitor", "Scan airspace and control monitoring"),
    ("alert_center", "Alert Center", "Investigate live incidents"),
    ("whitelist", "Whitelist", "Trusted AP policy workspace"),
    ("logs", "Logs", "Raw JSONL forensic history"),
    ("statistics", "Statistics", "Operational trends and summaries"),
    ("settings", "Settings", "Remote config and local UI preferences"),
]

OUI_VENDOR_MAP = {
    "00:11:22": "Cisco",
    "04:92:26": "Aruba",
    "18:E8:29": "Ubiquiti",
    "28:80:88": "TP-Link",
    "3C:84:6A": "Ruckus",
    "4C:5E:0C": "MikroTik",
    "70:3A:CB": "Raspberry Pi",
    "9C:C7:A6": "Netgear",
    "A4:2B:B0": "Aruba",
    "C0:25:E9": "Huawei",
    "D4:CA:6D": "Apple",
    "F4:1A:79": "Ubiquiti",
}

_BSSID_PATTERN = re.compile(r"^[0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5}$")


def coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def format_timestamp(value: str) -> str:
    if not value:
        return "No timestamp"
    return value.replace("T", " ").replace("Z", " UTC")


def event_icon(event_type: str) -> str:
    if event_type == "rogue_ap_detected":
        return "ROGUE"
    if event_type == "deauth_attack_detected":
        return "DEAUTH"
    if event_type == "scan_completed":
        return "SCAN"
    return "EVENT"


def alert_key(alert: dict) -> str:
    return "|".join(
        [
            str(alert.get("timestamp", "")),
            str(alert.get("event_type", "")),
            str(alert.get("ssid", "")),
            str(alert.get("detected_bssid") or alert.get("target_bssid") or ""),
        ]
    )


def alert_severity(alert: dict) -> str:
    severity = str(alert.get("severity", "")).lower()
    if severity:
        return severity
    if alert.get("event_type") == "rogue_ap_detected":
        return "high"
    if alert.get("event_type") == "deauth_attack_detected":
        return "critical"
    return "info"


def severity_color(severity: str) -> str:
    normalized = severity.lower()
    if normalized == "critical":
        return "#ff6f86"
    if normalized == "high":
        return "#ff9b5d"
    if normalized in {"medium", "warning"}:
        return "#ffc766"
    if normalized == "low":
        return "#79c0ff"
    return "#66adff"


def alert_title(alert: dict) -> str:
    if alert.get("event_type") == "rogue_ap_detected":
        return "Rogue AP Detected"
    if alert.get("event_type") == "deauth_attack_detected":
        return "Deauth Attack Detected"
    if alert.get("event_type") == "scan_completed":
        return "Scan Completed"
    return "Security Event"


def alert_reason(alert: dict) -> str:
    if alert.get("event_type") == "rogue_ap_detected":
        similarity = alert.get("ssid_similarity", "N/A")
        return (
            f"SSID similarity {similarity} matched a legitimate AP, but the observed "
            "BSSID does not match the trusted whitelist entry."
        )
    if alert.get("event_type") == "deauth_attack_detected":
        return (
            f"{alert.get('frame_count', '?')} deauth frames exceeded the threshold of "
            f"{alert.get('threshold', '?')} within {alert.get('window_seconds', '?')} seconds."
        )
    if alert.get("event_type") == "scan_completed":
        return (
            f"Scan on {alert.get('interface', '-')} completed with "
            f"{alert.get('ap_count', 0)} access point(s) detected."
        )
    return alert.get("message", "No detection reason available.")


def alert_summary(alert: dict) -> str:
    if alert.get("event_type") == "rogue_ap_detected":
        return (
            f"SSID {alert.get('ssid', '-')}"
            f" | legit {alert.get('legit_bssid', '-')}"
            f" | rogue {alert.get('detected_bssid', '-')}"
        )
    if alert.get("event_type") == "deauth_attack_detected":
        return (
            f"target {alert.get('target_bssid', '-')}"
            f" | {alert.get('frame_count', 0)} frame(s)"
            f" | src {alert.get('source_mac') or 'Unknown'}"
        )
    if alert.get("event_type") == "scan_completed":
        return (
            f"{alert.get('ap_count', 0)} AP(s) detected on "
            f"{alert.get('interface', '-')}"
        )
    return alert.get("message", "No summary")


def alert_details_html(alert: dict) -> str:
    if alert.get("event_type") == "rogue_ap_detected":
        return (
            f"<b>SSID</b>: {html.escape(str(alert.get('ssid', '-')))}<br>"
            f"<b>Legitimate BSSID</b>: <code>{html.escape(str(alert.get('legit_bssid', '-')))}</code><br>"
            f"<b>Rogue BSSID</b>: <code>{html.escape(str(alert.get('detected_bssid', '-')))}</code><br>"
            f"<b>Channel</b>: {html.escape(str(alert.get('channel', '-')))}<br>"
            f"<b>RSSI</b>: {html.escape(str(alert.get('rssi', '-')))} dBm<br>"
            f"<b>Reason</b>: {html.escape(alert_reason(alert))}"
        )
    if alert.get("event_type") == "deauth_attack_detected":
        return (
            f"<b>Target BSSID</b>: <code>{html.escape(str(alert.get('target_bssid', '-')))}</code><br>"
            f"<b>SSID</b>: {html.escape(str(alert.get('ssid') or 'Unknown'))}<br>"
            f"<b>Source MAC</b>: <code>{html.escape(str(alert.get('source_mac') or 'Unknown'))}</code><br>"
            f"<b>Frames</b>: {html.escape(str(alert.get('frame_count', '-')))}<br>"
            f"<b>Window</b>: {html.escape(str(alert.get('window_seconds', '-')))}s<br>"
            f"<b>Threshold</b>: {html.escape(str(alert.get('threshold', '-')))}<br>"
            f"<b>Reason</b>: {html.escape(alert_reason(alert))}"
        )
    if alert.get("event_type") == "scan_completed":
        top_results = alert.get("top_results", []) or []
        top_html = "No APs detected."
        if top_results:
            top_html = "<br>".join(
                (
                    f"&bull; <code>{html.escape(str(ap.get('bssid', '-')))}</code> | "
                    f"{html.escape(str(ap.get('ssid', '<Hidden>')))} | "
                    f"CH {html.escape(str(ap.get('channel', '-')))} | "
                    f"{html.escape(str(ap.get('rssi', '-')))} dBm"
                )
                for ap in top_results
            )
        return (
            f"<b>Interface</b>: {html.escape(str(alert.get('interface', '-')))}<br>"
            f"<b>AP Count</b>: {html.escape(str(alert.get('ap_count', 0)))}<br>"
            f"<b>Scan Duration</b>: {html.escape(str(alert.get('scan_seconds', '-')))}s<br>"
            f"<b>Reason</b>: {html.escape(alert_reason(alert))}<br>"
            f"<b>Top Results</b>:<br>{top_html}"
        )
    return html.escape(json.dumps(alert, indent=2, ensure_ascii=False))


def guess_vendor(bssid: str) -> str:
    prefix = (bssid or "").upper()[:8]
    if prefix in OUI_VENDOR_MAP:
        return OUI_VENDOR_MAP[prefix]
    return f"OUI {prefix}" if prefix else "Unknown"


def ssid_similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left.lower(), right.lower()).ratio()


def is_valid_bssid(value: str) -> bool:
    return bool(_BSSID_PATTERN.match((value or "").strip()))

