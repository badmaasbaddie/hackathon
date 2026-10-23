import urllib.request
import json

payload = {
    "age": 45,
    "gender": "Female",
    "systolic_bp": 185,
    "diastolic_bp": 115,
    "heart_rate": 118,
    "hemoglobin": 6.8,
    "weight": 52,
    "spo2": 88,
    "temp": 102.4,
    "condition": "Severe Pneumonia with Acute Respiratory Distress & Severe Anemia",
    "village": "Kakori",
    "hub_hospital": "Apollo Medics Lucknow"
}

req = urllib.request.Request(
    "http://127.0.0.1:8000/api/ai/predict-care",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

res = urllib.request.urlopen(req)
result = json.loads(res.read().decode("utf-8"))
print("AI Critical Case Result:")
print(json.dumps(result, indent=2))
