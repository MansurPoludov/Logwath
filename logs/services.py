import re
from datetime import datetime
from dateutil import parser as date_parser
from django.utils import  timezone

# Список паттернов: (regex, groups: (timestamp_group_index, level_group_index, message_group_index))
PATTERNS = [
    (re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+(INFO|ERROR|WARNING|WARNINGS)\s+(.*)$"), (1,2,3)),
    (re.compile(r"^([A-Za-z]{3} \d{1,2} \d{2}:\d{2}:\d{2})\s+.*\s+(INFO|ERROR|WARNING):\s+(.*)$"), (1,2,3)),
    # example: 2025-11-27T09:00:00Z - ERROR - message
    (re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z?)\s*[-–—]\s*(INFO|ERROR|WARNING)\s*[-–—]\s*(.*)$"), (1, 2, 3)),


]

ANOMALY_KEYWORDS = ["failed", "error", "critical", "unauthorized", "denied", "exception"]


def parse_timestamp(ts_str):
    try:
        dt = date_parser.parse(ts_str, default=datetime.now())
        if dt.tzinfo is None:
            dt = timezone.make_aware(dt,timezone=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt
    except Exception:
        return None



def analyze_log(file_path):
    # Обновлённый шаблон

    entries = []
    try:
        with open(file_path, "r", encoding="utf-8" , errors='replace') as f:
            for line in f:
                line = line.strip()

                if not line:
                    continue
                parsed = False
                for pattern , groups in PATTERNS:
                    m = pattern.match(line)
                    if m:
                        ts_str = m.group(groups[0])
                        level = m.group(groups[1]).upper()
                        message = m.group(groups[2]).strip()
                        ts = parse_timestamp(ts_str)
                        is_anomaly = (level ==  "ERROR") or any (k in message.lower() for k in ANOMALY_KEYWORDS)
                        entries.append((ts or timezone.now() , level, message, is_anomaly))
                        parsed = True
                        break
                if not parsed:
                    try:
                        possible_date = None
                        tokens = line.split()
                        for t in tokens[:6]:
                            if any(ch.isdigit() for ch in t) and (':' in t or '-' in t or '/' in t):
                                possible_date = t
                                break
                        ts = parse_timestamp(possible_date) if possible_date else None
                    except Exception:
                        ts = None
                    level = "INFO"
                    message = line
                    is_anomaly = any(k in message.lower() for k in ANOMALY_KEYWORDS)
                    entries.append((ts or timezone.now(), level, message, is_anomaly))

    except FileNotFoundError:
        return []


    return entries
