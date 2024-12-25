import json
import requests
import time
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()
KEY = os.getenv("KEY")
SECRET = os.getenv("SECRET")

methodName = "user.status"
URL = f"https://codeforces.com/api/{methodName}"
currentTime = int(time.time())
rand = 694200
handle = "darelife"

hashString = (
    f"{rand}/{methodName}?apiKey={KEY}&handle={handle}&time={currentTime}#{SECRET}"
)
apiSig = hashlib.sha512(hashString.encode()).hexdigest()

response = requests.get(
    URL,
    params={
        "handle": handle,
        "apiKey": KEY,
        "time": currentTime,
        "apiSig": f"{rand}{apiSig}",
    },
)
data = json.loads(response.text)
# print(data["result"][0])


# https://codeforces.com/api/contest.standings?contestId=566&asManager=false&from=1&count=5&showUnofficial=true
methodName = "contest.standings"
URL = f"https://codeforces.com/api/{methodName}"
currentTime = int(time.time())
rand = 694200
contestId = 560164

hashString = f"{rand}/{methodName}?apiKey={KEY}&contestId={contestId}&time={currentTime}#{SECRET}"
apiSig = hashlib.sha512(hashString.encode()).hexdigest()

response = requests.get(
    URL,
    params={
        "contestId": contestId,
        "apiKey": KEY,
        "time": currentTime,
        "apiSig": f"{rand}{apiSig}",
    },
)

data = json.loads(response.text)
print(data["result"]["problems"])
