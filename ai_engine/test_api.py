import requests
import json

url = "http://localhost:5000/api/adaptive-query"
headers = {
    "X-Internal-API-Key": "hqVm1Oe9wtEt5QQFXPyHhVLH-m2f4Id4aKaEierRjBw",
    "Content-Type": "application/json"
}
payload = {
    "question": "What is the punishment for theft under IPC?",
    "use_llm": True
}

print(f"Sending request to {url}...")
try:
    response = requests.post(url, headers=headers, json=payload, timeout=120)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Response JSON:")
        print(json.dumps(response.json(), indent=2))
    else:
        print("Error Response:")
        print(response.text)
except Exception as e:
    print(f"Error: {e}")
