import time
import hashlib
import requests
import json

with open("secrets.json", "r") as f:
    data = json.load(f)

KEY = data["KEY"]
SECRET = data["SECRET"]


def contestStandings(contestId: int = 560501):
    methodName = "contest.standings"
    URL = f"https://codeforces.com/api/{methodName}"
    currentTime = int(time.time())
    rand = 694200

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
    print(response.url)
    data = json.loads(response.text)
    if "result" not in data:
        return [], -1
    return data["result"]["problems"], len(data["result"]["problems"])


contestStandings()
