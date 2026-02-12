import os
import sys
import time
import json
import urllib.request

BASE_URL = os.getenv("TARGET_BASE_URL", "http://weather-api.weather.svc.cluster.local")
CITY = os.getenv("SYNTHETIC_CITY", "London")
TIMEOUT = float(os.getenv("SYNTHETIC_TIMEOUT_SECONDS", "5"))

url = f"{BASE_URL}/weather/{CITY}"
start = time.time()
try:
    with urllib.request.urlopen(url, timeout=TIMEOUT) as resp:
        body = resp.read().decode("utf-8")
        if resp.status != 200:
            print(f"FAIL status={resp.status} body={body}")
            sys.exit(2)
        obj = json.loads(body)
        for k in ("temperature", "conditions", "humidity", "wind_speed"):
            if k not in obj:
                print(f"FAIL missing_field={k} body={body}")
                sys.exit(2)
except Exception as e:
    print(f"FAIL exception={e}")
    sys.exit(2)

print(f"OK latency_ms={(time.time()-start)*1000:.1f}")
