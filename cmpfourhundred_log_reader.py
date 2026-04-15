import os
from collections import defaultdict
from datetime import datetime, timedelta

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cmpfourhundred_session.log")

if not os.path.exists(LOG_FILE):
    print(f"Log file not found: {LOG_FILE}")
    input("\nPress Enter to exit...")
    exit()

counts = defaultdict(int)
crashes = defaultdict(int)
session_start = None
durations = []

with open(LOG_FILE, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        parts = line.split("|", 2)
        if len(parts) < 2:
            continue
        ts_str, event = parts[0], parts[1]
        detail = parts[2] if len(parts) == 3 else ""

        try:
            ts = datetime.fromisoformat(ts_str)
        except ValueError:
            ts = None

        counts[event] += 1

        if event == "SESSION_START":
            session_start = ts
        elif event == "SESSION_END" and session_start and ts:
            durations.append(ts - session_start)
            session_start = None
        elif event == "CRASH":
            crashes[detail.strip() or "unknown"] += 1

total_time = sum(durations, timedelta())
avg_time = total_time / len(durations) if durations else timedelta()

def fmt(td):
    s = int(td.total_seconds())
    h, r = divmod(s, 3600)
    m, s = divmod(r, 60)
    return f"{h}h {m}m {s}s" if h else f"{m}m {s}s" if m else f"{s}s"

print("=" * 40)
print("       CMP400 SESSION STATS")
print("=" * 40)
print(f"  Sessions          {counts['SESSION_START']}")
print(f"  Collisions        {counts['CRASH']}") # renamed this bc I realised it could be confusing otherwise for the user when answering the survey data as the survey uses the term "collisions"
print(f"  Resets            {counts['RESET']}")
print(f"  Teleports         {counts['TELEPORT']}")
print(f"  Waypoints hit     {counts['WAYPOINT_HIT']}")
print(f"  AI Interventions  {counts['INTERVENTION_START']}")
print(f"  Mode changes      {counts['MODE_CHANGE']}")
print("-" * 40)
print(f"  Total runtime     {fmt(total_time)}")
print(f"  Avg session       {fmt(avg_time)}")

if crashes:
    print("-" * 40)
    print("  CRASHES")
    for obj, n in sorted(crashes.items(), key=lambda x: -x[1]):
        print(f"    {n:>3}x  {obj}")

print("=" * 40)
input("\nPress Enter to exit...")
