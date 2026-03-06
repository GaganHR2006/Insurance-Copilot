import json
from datetime import datetime

def log(tag: str, data):
    print(f"\n{'='*50}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] DEBUG: {tag}")
    if isinstance(data, (dict, list)):
        print(json.dumps(data, indent=2, default=str)[:1000])
    else:
        print(str(data)[:500])
    print('='*50)
