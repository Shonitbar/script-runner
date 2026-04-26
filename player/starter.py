import requests,time

session = requests.Session()
r = session.post("http://localhost:8000/mine")
print(r.json())
