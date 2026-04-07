import requests

session = requests.Session()
r = session.get("http://localhost:8000/mine")
print(r.json())
