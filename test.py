import requests
import random

average_rating = 1500
url = "https://codeforces.com/api/problemset.problems"
response = requests.get(url)
data = response.json()
problems = data["result"]["problems"]
problemSet = {}
ratingDelta = 0
ratings = [average_rating, average_rating, average_rating, average_rating]
for i in range(21):
    if i % 2 == 0:
        ratings.append(average_rating - ratingDelta)
    else:
        ratings.append(average_rating + ratingDelta)
    if i % 4 == 0:
        ratingDelta += 100

for problem in problems:
    if "contestId" not in problem:
        continue
    if problem["contestId"] < 1286:
        continue
    if "rating" not in problem:
        continue
    if problem["rating"] in ratings:
        try:
            problemSet[problem["rating"]].append(problem)
        except:
            problemSet[problem["rating"]] = [problem]

problemsChosen = []
for i in range(25):
    index = random.randint(0, len(problemSet[ratings[i]]) - 1)
    problemsChosen.append(problemSet[ratings[i]].pop(index))
text = ""
for i in range(25):
    url = f"<https://codeforces.com/problemset/problem/{problemsChosen[i]['contestId']}/{problemsChosen[i]['index']}>"
    text += f"[{i+1} ]({url})"
    if (i + 1) % 5 == 0:
        text += "\n\n"

print(text)


"""
1-4: avg_rating
5,7,9,11: max(800, avg_rating - 100)
6,8,10,12: min(2200, avg_rating + 100)
13,15,17,19: max(800, avg_rating - 200)
14,16,18,20: min(2200, avg_rating + 200)
21,23,25: max(800, avg_rating - 300)
22,24: min(2200, avg_rating + 300)
"""
