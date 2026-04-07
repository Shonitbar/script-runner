import requests,time

session = requests.Session()

while True:
    r = session.post("http://localhost:8000/mine")
    print(r.json())
    time.sleep(1)