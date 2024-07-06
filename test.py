import requests

url = "https://codeforces.com/api/contest.list?gym=true"
response = requests.get(url)
with open("debug.html", "w") as f:
    f.write(response.text)
