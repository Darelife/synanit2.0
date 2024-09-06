from discord import app_commands, TextChannel
from discord import File, Object, Member
from discord import Colour, Interaction
from discord.ext import commands
from discord.ui import Button, View
import time
import random
import requests


class ButtonView(View):
    def __init__(self):
        super().__init__()
        # self.questionNumber = questionNumber
        self.add_item(
            Button(
                label="🔄️ Refresh",
                custom_id="refreshCodeforceQuestion",
            )
        )


def get_board_string(board):
    board_string = "```"
    cnt = 0
    for row in board:
        if cnt != 0:
            board_string += "" + "----|" * (len(row) - 1) + "----\n"
        board_string += " " + " | ".join(row) + "\n"
        cnt += 1
    board_string += "```"
    return board_string.strip()


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
        message = await interaction.followup.send(
            f"**Tic Tac Toe**\n{get_board_string(table)}"
        )
        url = "https://codeforces.com/api/problemset.problems"
        response = requests.get(url)
        data = response.json()
        problems = data["result"]["problems"]
        problemSet = {}
        ratingDelta = 0
        # ratings = [average_rating, average_rating, average_rating, average_rating]
        ratings = []
        lowerBound = max(800, average_rating - 200)
        upperBound = min(2200, average_rating + 200)
        size = (upperBound - lowerBound) / 100 + 1
        rangee = []
        for i in range(int(size)):
            rangee.append(lowerBound + i * 100)
        for i in range(board_size * board_size):
            ratings.append(random.choice(rangee))

            # if i % 2 == 0:
            #     ratings.append(max(800, average_rating - ratingDelta))
            # else:
            #     ratings.append(min(2200, average_rating + ratingDelta))
            # if i % 4 == 0:
            #     ratingDelta += 100

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
        for i in range(board_size * board_size):
            index = random.randint(0, len(problemSet[ratings[i]]) - 1)
            problemsChosen.append(problemSet[ratings[i]].pop(index))
        text = ""
        for i in range(board_size * board_size):
            url = f"<https://codeforces.com/problemset/problem/{problemsChosen[i]['contestId']}/{problemsChosen[i]['index']}>"
            text += f"[{str(i+1).zfill(2)}]({url}) "
            if (i + 1) % board_size == 0:
                text += "\n"
        view = ButtonView()
        start = time.time()
        while (time.time() - start) < time_limit:
            table[0][0] = " X"
            await message.edit(
                content=f"**Tic Tac Toe**\n{text}{get_board_string(table)}"
            )
            break
        # print(message)


async def setup(bot: commands.Bot):
    await bot.add_cog(tictactoe(bot))
    # Assuming `tree` is your app command tree instance
    await bot.tree.sync(guild=Object(1246441351965446236))
