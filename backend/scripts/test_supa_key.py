import yaml
import httpx
import os

with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

url = config["supabase"]["url"]
key = config["supabase"]["key"]

print(f"URL configured: {'yes' if url else 'no'}")
print(f"SUPABASE key configured: {'yes' if key else 'no'}")

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
}

res = httpx.get(f"{url}/rest/v1/ciclos?select=*", headers=headers)
print(f"Status: {res.status_code}")
print(f"Response: {res.text}")
