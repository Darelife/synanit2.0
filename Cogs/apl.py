from discord import app_commands, Interaction
from discord.ext import commands
from discord.ui import Button, View
import requests
import json
import os
import hashlib
import time
# from dotenv import load_dotenv
# # import random

# load_dotenv()
# KEY = os.getenv("KEY")
# SECRET = os.getenv("SECRET")
# KEY = ""
# SECRET = ""
# with open("secrets.json", "r") as f:
#     data = json.load(f)

KEY = os.getenv("KEY")
SECRET = os.getenv("SECRET")


class ButtonView(View):
    def __init__(self):
        super().__init__()
        # self.questionNumber = questionNumber
        self.add_item(
            Button(
                label="🔄️",
                custom_id="refreshTicTacToe",
            )
        )


def userStatus(handle: str):
    methodName = "user.status"
    URL = f"https://codeforces.com/api/{methodName}"
    currentTime = int(time.time())
    rand = 694200

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
    return json.loads(response.text)["result"]


def contestStandings(contestId: int):
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


def get_board_string(board: list[list[any]]):
    board_string = "```"
    cnt = 0
    for row in board:
        if cnt != 0:
            board_string += "" + "----|" * (len(row) - 1) + "----\n"
        board_string += " " + " | ".join(row) + "\n"
        cnt += 1
    board_string += "```"
    return board_string.strip()


def callForUpdate(
    id: str,
    problemsChosen: list[any],
    startTime: int,
):
    # url = f"https://codeforces.com/api/user.status?handle={id}&count=400"
    # response = requests.get(url)
    data = userStatus(id)
    result = []
    # with open("checkingTicTacToe.json", "w") as f:
    #     json.dump(data, f, indent=2)
    # with open("checkingTicTacToeProblems.json", "w") as f:
    #     json.dump(problemsChosen, f, indent=2)
    with open("checkingTicTacToeProblems.json", "w") as f:
        json.dump(data, f, indent=2)
    with open("checkingTicTacToeProblems2.json", "w") as f:
        json.dump(problemsChosen, f, indent=2)
    # time.sleep(5)
    for i in problemsChosen:
        solved = False
        time = 0
        for j in data:
            if (
                i["index"] == j["problem"]["index"]
                and i["contestId"] == j["problem"]["contestId"]
            ):
                print("Comeon!!!")
                print(i["index"], j["problem"]["index"])
                if ("verdict" in j) and ("creationTimeSeconds" in j):
                    if j["verdict"] == "OK":
                        if j["creationTimeSeconds"] > startTime:
                            print("FOUNDDDDD")
                            solved = True
                            time = j["creationTimeSeconds"]
                            break

        result.append((solved, time))
        # with open(f"user{id}.json", "w") as f:
        #     json.dump(result, f, indent=2)
    return result, data


def checkForUpdates(
    board: list[list[any]],
    id1: str,
    id2: str,
    mashupId: int,
    startTime: int,
):
    # result1, data1 = callForUpdate(id1, problemsChosen, startTime)
    # result2, data2 = callForUpdate(id2, problemsChosen, startTime)

    # with open("cf1.json", "w") as f:
    #     json.dump(data1, f, indent=2)
    # with open("cf2.json", "w") as f:
    #     json.dump(data2, f, indent=2)
    # for i in range(len(board) * len(board)):
    #     one, two = False, False
    #     if result1[i][0]:
    #         one = True
    #     if result2[i][0]:
    #         two = True
    #     if one and two:
    #         if result1[i][1] < result2[i][1]:
    #             two = False
    #         else:
    #             one = False
    #     if one:
    #         board[i // len(board)][i % len(board)] = " X"
    #     elif two:
    #         board[i // len(board)][i % len(board)] = " O"

    # # board = get_board_string(board)
    # return board

    contestId = mashupId
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
    with open("ttt.json", "w") as f:
        json.dump(data, f, indent=2)
    # if "result" not in data:
    # return [], -1
    # return data["result"]["problems"], len(data["result"]["problems"])

    # data, n = contestStandings(mashupId)
    rows = data["result"]["rows"]
    cf1 = [-1] * 25
    cf2 = [-1] * 25
    print(startTime)
    for i in rows:
        if i["party"]["members"][0]["handle"].upper() == id1.upper():
            a = i["problemResults"]
            # print(type(a))
            for j in range(len(a)):
                if a[j]["points"] > 0:
                    # if startTime - 5 * 60 - 30 < a[j]["bestSubmissionTimeSeconds"]:
                    cf1[j] = a[j]["bestSubmissionTimeSeconds"]
        elif i["party"]["members"][0]["handle"].upper() == id2.upper():
            a = i["problemResults"]
            # print(type(a))
            for j in range(len(a)):
                if a[j]["points"] > 0:
                    # if startTime - 5 * 60 - 30 < a[j]["bestSubmissionTimeSeconds"]:
                    cf2[j] = a[j]["bestSubmissionTimeSeconds"]

    solve = [0] * 25
    for i in range(25):
        if (cf1[i] != -1) and (cf2[i] != -1):
            if cf1[i] < cf2[i]:
                solve[i] = 1
            else:
                solve[i] = 2
        elif cf1[i] != -1:
            solve[i] = 1
        elif cf2[i] != -1:
            solve[i] = 2

    for i in range(25):
        if solve[i] == 1:
            board[i // 5][i % 5] = " X"
        elif solve[i] == 2:
            board[i // 5][i % 5] = " O"

    with open("board.txt", "w") as f:
        f.write(str(board))
    return board


class apl(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="apl")
    async def _apl(
        self,
        interaction: Interaction,
        contest_id: int,
        codeforce_id_1: str,
        codeforce_id_2: str,
    ):
        if interaction.user.id != 497352662451224578:
            await interaction.response.send_message(
                "You are not allowed to use this command", ephemeral=True
            )
            return
        """Clear all bets"""
        await interaction.response.defer()

        problems, n = contestStandings(contest_id)

        if n == -1:
            await interaction.edit_original_response(content="Invalid contest id")
            return
        if n != 25:
            await interaction.edit_original_response(content=f"not 25 problems -> {n}")
            with open("checkingTicTacToeProblems.json", "w") as f:
                json.dump(problems, f, indent=2)
            return

        board_size = 5
        table = [
            [
                f"{str(i + j * (board_size) - board_size).zfill(2)}"
                for i in range(1, board_size + 1)
            ]
            for j in range(1, board_size + 1)
        ]
        problemsChosen = problems
        questions = []
        for i in range(25):
            questions.append(
                f"https://codeforces.com/gym/{contest_id}/problem/{problems[i]['index']}"
            )

        # random.shuffle(questions)

        text = ""
        textList = []

        for i in range(25):
            url = questions[i]
            text += f"[{str(i + 1).zfill(2)}]({questions[i]}) "
            if (i + 1) % board_size == 0:
                text += "\n"
            textList.append(f"[{str(i + 1).zfill(2)}]({url})")

        view = ButtonView()
        message = await interaction.followup.send(
            f"**Tic Tac Toe**\n{text}{get_board_string(table)}",
            view=view,
        )

        # print(problemsChosen)

        start = time.time()
        while (time.time() - start) < 5 * 60 * 60:
            # try:
            button_interaction = await self.bot.wait_for(
                "interaction",
                timeout=2000,  # 33 mins
            )
            if button_interaction.data["custom_id"] != "refreshTicTacToe":
                continue
            await button_interaction.response.defer()
            table = checkForUpdates(
                table, codeforce_id_1, codeforce_id_2, contest_id, start
            )
            for i in range(len(table)):
                for j in range(len(table[i])):
                    if table[i][j] == " X":
                        initialText = textList[i * len(table) + j]
                        url = initialText.split("(")[1].split(")")[0]
                        textList[i * len(table) + j] = f"[❌]({url})"
                    elif table[i][j] == " O":
                        initialText = textList[i * len(table) + j]
                        url = initialText.split("(")[1].split(")")[0]
                        textList[i * len(table) + j] = f"[⭕]({url})"
            # Create a string representation for display purposes only.
            board_display = get_board_string(table)
            text = ""
            for i in range(board_size * board_size):
                text += textList[i] + " "
                if (i + 1) % board_size == 0:
                    text += "\n"
            await button_interaction.message.edit(
                content=f"**Tic Tac Toe**\n{text}{board_display}"
            )
        # except:
        #     for item in view.children:
        #         if isinstance(item, Button):
        #             item.disabled = True
        #     await message.edit(view=view)
        #     break

        # await interaction.edit_original_response(content="All Bets cleared")


async def setup(bot: commands.Bot):
    await bot.add_cog(apl(bot))
    # Assuming `tree` is your app command tree instance
    # await bot.tree.sync(guild=Object(1246441351965446236))
