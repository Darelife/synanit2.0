from discord import app_commands, Interaction
from discord.ext import commands
from discord.ui import Button, View
import time
import random
import requests
import asyncio
# import json
# from discord import File, TextChanel, Member, Colour, Object


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


def getRatings(average_rating, board_size):
    ratings = []
    lowerBound = max(800, average_rating - 200)
    upperBound = min(2200, average_rating + 200)
    size = (upperBound - lowerBound) / 100 + 1
    rangee = []
    for i in range(int(size)):
        rangee.append(lowerBound + i * 100)
    for i in range(board_size * board_size):
        ratings.append(random.choice(rangee))
    return ratings


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
    url = f"https://codeforces.com/api/user.status?handle={id}&count=200"
    response = requests.get(url)
    data = response.json()["result"]
    result = []
    # with open("checkingTicTacToe.json", "w") as f:
    #     json.dump(data, f, indent=2)
    # with open("checkingTicTacToeProblems.json", "w") as f:
    #     json.dump(problemsChosen, f, indent=2)
    for i in problemsChosen:
        solved = False
        time = 0
        for j in data:
            if (i["contestId"] == j["contestId"]) and (
                i["index"] == j["problem"]["index"]
            ):
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
    return result


def checkForUpdates(
    board: list[list[any]],
    id1: str,
    id2: str,
    problemsChosen: list[any],
    startTime: int,
):
    result1 = callForUpdate(id1, problemsChosen, startTime)
    result2 = callForUpdate(id2, problemsChosen, startTime)
    for i in range(len(board) * len(board)):
        one, two = False, False
        if result1[i][0]:
            one = True
        if result2[i][0]:
            two = True
        if one and two:
            if result1[i][1] < result2[i][1]:
                two = False
            else:
                one = False
        if one:
            board[i // len(board)][i % len(board)] = " X"
        elif two:
            board[i // len(board)][i % len(board)] = " O"

    # board = get_board_string(board)
    return board


class tictactoe(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="tictactoe")
    async def _tictactoe(
        self,
        interaction: Interaction,
        average_rating: int,
        board_size: int,
        codeforce_id_1: str,
        codeforce_id_2: str,
        time_limit: int = 7200,
    ):
        """Play a game of tic-tac-toe"""
        await interaction.response.defer()
        if (average_rating < 800) or (average_rating > 2200):
            await interaction.followup.send(
                "Average rating must be between 800 and 2200"
            )
            return
        table = [
            [
                f"{str(i+j*(board_size)-board_size).zfill(2)}"
                for i in range(1, board_size + 1)
            ]
            for j in range(1, board_size + 1)
        ]
        url = "https://codeforces.com/api/problemset.problems"
        response = requests.get(url)
        data = response.json()
        problems = data["result"]["problems"]
        problemSet = {}

        ratings = getRatings(average_rating, board_size)

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
                except KeyError:
                    problemSet[problem["rating"]] = [problem]

        problemsChosen = []
        for i in range(board_size * board_size):
            index = random.randint(0, len(problemSet[ratings[i]]) - 1)
            problemsChosen.append(problemSet[ratings[i]].pop(index))
        text = ""
        textList = []
        for i in range(board_size * board_size):
            url = f"<https://codeforces.com/problemset/problem/{problemsChosen[i]['contestId']}/{problemsChosen[i]['index']}>"
            text += f"[{str(i+1).zfill(2)}]({url}) "
            if (i + 1) % board_size == 0:
                text += "\n"
            textList.append(f"[{str(i+1).zfill(2)}]({url})")
        view = ButtonView()
        message = await interaction.followup.send(
            f"**Tic Tac Toe**\n{text}{get_board_string(table)}",
            view=view,
        )
        start = time.time()
        # lastRefresh = start
        while (time.time() - start) < time_limit:
            # table[0][0] = " X"
            # table = get_board_string(table)
            # table = checkForUpdates(
            #     table, codeforce_id_1, codeforce_id_2, problemsChosen
            # )
            # table = get_board_string(table)
            # await message.edit(content=f"**Tic Tac Toe**\n{text}{table}")
            # # time.sleep(90)
            # await asyncio.sleep(60)
            # Update the board in place without converting to a string.
            # await asyncio.sleep(300)
            # if time.time() - lastRefresh < 300:
            #     lastRefresh = time.time()
            #     continue
            try:
                button_interaction = await self.bot.wait_for(
                    "interaction", timeout=2000
                )
                if button_interaction.data["custom_id"] != "refreshTicTacToe":
                    continue
                await button_interaction.response.defer()
                table = checkForUpdates(
                    table, codeforce_id_1, codeforce_id_2, problemsChosen, start
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
            except asyncio.TimeoutError:
                for item in view.children:
                    if isinstance(item, Button):
                        item.disabled = True
                await message.edit(view=view)
                break
        # print(message)


async def setup(bot: commands.Bot):
    await bot.add_cog(tictactoe(bot))
    # Assuming `tree` is your app command tree instance
    # await bot.tree.sync(guild=Object(1246441351965446236))
