import requests

r = requests.post("http://localhost:8000/mine")
print(r.json())
