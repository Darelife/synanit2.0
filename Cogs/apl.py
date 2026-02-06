from discord import app_commands, Interaction
from discord.ext import commands
from discord.ui import Button, View
import json
import os
import hashlib
import time
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()
KEY = os.getenv("KEY")
SECRET = os.getenv("SECRET")

class ButtonView(View):
    def __init__(self):
        super().__init__()
        self.add_item(
            Button(
                label="🔄️",
                custom_id="refreshTicTacToe",
            )
        )

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

class Apl(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def userStatus(self, handle: str):
        methodName = "user.status"
        URL = f"https://codeforces.com/api/{methodName}"
        currentTime = int(time.time())
        rand = 694200

        hashString = (
            f"{rand}/{methodName}?apiKey={KEY}&handle={handle}&time={currentTime}#{SECRET}"
        )
        apiSig = hashlib.sha512(hashString.encode()).hexdigest()

        params = {
            "handle": handle,
            "apiKey": KEY,
            "time": currentTime,
            "apiSig": f"{rand}{apiSig}",
        }
        
        async with self.bot.session.get(URL, params=params) as response:
             if response.status == 200:
                 return (await response.json())["result"]
             return None

    async def contestStandings(self, contestId: int):
        methodName = "contest.standings"
        URL = f"https://codeforces.com/api/{methodName}"
        currentTime = int(time.time())
        rand = 694200

        hashString = f"{rand}/{methodName}?apiKey={KEY}&contestId={contestId}&time={currentTime}#{SECRET}"
        apiSig = hashlib.sha512(hashString.encode()).hexdigest()

        params = {
            "contestId": contestId,
            "apiKey": KEY,
            "time": currentTime,
            "apiSig": f"{rand}{apiSig}",
        }
        
        async with self.bot.session.get(URL, params=params) as response:
             # print(response.url)
             if response.status != 200:
                 return [], -1
             data = await response.json()
             if "result" not in data:
                 return [], -1
             return data["result"]["problems"], len(data["result"]["problems"])

    async def fetch_contest_standings_data(self, contestId: int):
         # Needed for checkForUpdates logic which wants full data, not just problems
        methodName = "contest.standings"
        URL = f"https://codeforces.com/api/{methodName}"
        currentTime = int(time.time())
        rand = 694200

        hashString = f"{rand}/{methodName}?apiKey={KEY}&contestId={contestId}&time={currentTime}#{SECRET}"
        apiSig = hashlib.sha512(hashString.encode()).hexdigest()

        params = {
            "contestId": contestId,
            "apiKey": KEY,
            "time": currentTime,
            "apiSig": f"{rand}{apiSig}",
        }
        
        async with self.bot.session.get(URL, params=params) as response:
             if response.status != 200:
                  return None
             return await response.json()

    async def checkForUpdates(
        self,
        board: list[list[any]],
        id1: str,
        id2: str,
        mashupId: int,
        startTime: int,
    ):
        data = await self.fetch_contest_standings_data(mashupId)
        if not data:
             return board
             
        # Log to file as in original?
        # with open("ttt.json", "w") as f:
        #     json.dump(data, f, indent=2)

        rows = data["result"]["rows"]
        cf1 = [-1] * 25
        cf2 = [-1] * 25
        
        for i in rows:
            if i["party"]["members"][0]["handle"].upper() == id1.upper():
                a = i["problemResults"]
                for j in range(len(a)):
                    if a[j]["points"] > 0:
                        cf1[j] = a[j]["bestSubmissionTimeSeconds"]
            elif i["party"]["members"][0]["handle"].upper() == id2.upper():
                a = i["problemResults"]
                for j in range(len(a)):
                    if a[j]["points"] > 0:
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

        # with open("board.txt", "w") as f:
        #     f.write(str(board))
        return board

    @app_commands.command(name="apl")
    async def apl(
        self,
        interaction: Interaction,
        contest_id: int,
        codeforce_id_1: str,
        codeforce_id_2: str,
    ):
        """Clear all bets""" # Docstring mismatch in original code lol, keeping it
        if interaction.user.id != 497352662451224578:
            await interaction.response.send_message(
                "You are not allowed to use this command", ephemeral=True
            )
            return
            
        await interaction.response.defer()

        problems, n = await self.contestStandings(contest_id)

        if n == -1:
            await interaction.followup.send(content="Invalid contest id")
            return
        if n != 25:
            await interaction.followup.send(content=f"not 25 problems -> {n}")
            return

        board_size = 5
        table = [
            [
                f"{str(i + j * (board_size) - board_size).zfill(2)}"
                for i in range(1, board_size + 1)
            ]
            for j in range(1, board_size + 1)
        ]
        
        # questions = []
        # for i in range(25):
        #     questions.append(
        #         f"https://codeforces.com/gym/{contest_id}/problem/{problems[i]['index']}"
        #     )
        
        text = ""
        textList = []
        for i in range(25):
            # Assming gym link format from original code
            url = f"https://codeforces.com/gym/{contest_id}/problem/{problems[i]['index']}"
            text += f"[{str(i + 1).zfill(2)}]({url}) "
            if (i + 1) % board_size == 0:
                text += "\n"
            textList.append(f"[{str(i + 1).zfill(2)}]({url})")

        view = ButtonView()
        message = await interaction.followup.send(
            f"**Tic Tac Toe**\n{text}{get_board_string(table)}",
            view=view,
        )

        start = time.time()
        timeout = 5 * 60 * 60
        
        while (time.time() - start) < timeout:
             try:
                 remaining = timeout - (time.time() - start)
                 if remaining <= 0: break
                 
                 def check(i):
                      return (i.type == discord.InteractionType.component
                              and i.data.get("custom_id") == "refreshTicTacToe"
                              and i.message.id == message.id)
                 
                 button_interaction = await self.bot.wait_for(
                      "interaction", timeout=min(remaining, 2000), check=check
                 )
                 
                 await button_interaction.response.defer()
                 
                 table = await self.checkForUpdates(
                     table, codeforce_id_1, codeforce_id_2, contest_id, int(start)
                 )
                 
                 # visual update logic
                 temp_text_list = list(textList)
                 for i in range(len(table)):
                     for j in range(len(table[0])):
                         idx = i * len(table) + j
                         if table[i][j] == " X":
                             url = temp_text_list[idx].split("(")[1].split(")")[0]
                             temp_text_list[idx] = f"[❌]({url})"
                         elif table[i][j] == " O":
                             url = temp_text_list[idx].split("(")[1].split(")")[0]
                             temp_text_list[idx] = f"[⭕]({url})"
                             
                 board_display = get_board_string(table)
                 new_text = ""
                 for i in range(board_size * board_size):
                     new_text += temp_text_list[i] + " "
                     if (i + 1) % board_size == 0:
                         new_text += "\n"
                         
                 await button_interaction.message.edit(
                     content=f"**Tic Tac Toe**\n{new_text}{board_display}"
                 )
                 
             except asyncio.TimeoutError:
                 for item in view.children:
                     item.disabled = True
                 await message.edit(view=view)
                 break
             except Exception as e:
                 print(f"Error in apl loop: {e}")
                 break

async def setup(bot: commands.Bot):
    await bot.add_cog(Apl(bot))
