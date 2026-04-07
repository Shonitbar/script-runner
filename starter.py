import requests,time

r = requests.post("http://localhost:8000/mine")
print(r.json())

while(1):
    r = requests.post("http://localhost:8000/mine")
    time.sleep(1)
    print(r.json())