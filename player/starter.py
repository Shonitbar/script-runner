import requests,time

session = requests.Session()
for i in range(1000):
    r = session.post("http://localhost:8000/mine")
    r = session.get("http://localhost:8000/status")
    print(r.json())
    time.sleep(1)
    if r.json()[ "entropy" ] > 70:
        session.post("http://localhost:8000/compress")