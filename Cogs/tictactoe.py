from discord import app_commands, Interaction
from discord.ext import commands
from discord.ui import Button, View
import time
import random
import asyncio
import aiohttp

class ButtonView(View):
    def __init__(self):
        super().__init__()
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

def get_board_string(board: list[list[str]]):
    board_string = "```"
    cnt = 0
    for row in board:
        if cnt != 0:
            board_string += "" + "----|" * (len(row) - 1) + "----\n"
        board_string += " " + " | ".join(row) + "\n"
        cnt += 1
    board_string += "```"
    return board_string.strip()

class TicTacToe(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # In-memory storage for active games?
        # Actually, the command logic holds the state in local variables within the async function.
        # So as long as the async function is running, the state is preserved in RAM context.
        # The while loop keeps the game alive.
        # We don't necessarily need a global dict unless we want to access it from outside the command.
        # The user asked to "make it all work in the RAM", implying removing file dependency.
        # The previous code was writing board.txt and json files for some reason (maybe debugging or persistence).
        # By removing those file writes, we are satisfying "all work in RAM".
        # However, to be extra "good", I should ensure I didn't leave any file writes.
        pass

    async def fetch_user_status(self, handle: str, count: int = 200):
        url = f"https://codeforces.com/api/user.status?handle={handle}&count={count}"
        async with self.bot.session.get(url) as response:
             if response.status == 200:
                 return await response.json()
             return None

    async def callForUpdate(self, id: str, problemsChosen: list, startTime: int):
        data_json = await self.fetch_user_status(id)
        if not data_json or "result" not in data_json:
            return []
            
        data = data_json["result"]
        result = []
        for i in problemsChosen:
            solved = False
            time_solved = 0
            for j in data:
                if (i["contestId"] == j.get("contestId")) and (
                    i["index"] == j.get("problem", {}).get("index")
                ):
                    if ("verdict" in j) and ("creationTimeSeconds" in j):
                        if j["verdict"] == "OK":
                            if j["creationTimeSeconds"] > startTime:
                                solved = True
                                time_solved = j["creationTimeSeconds"]
                                break
            result.append((solved, time_solved))
        return result

    async def checkForUpdates(
        self,
        board: list[list[str]],
        id1: str,
        id2: str,
        problemsChosen: list,
        startTime: int,
    ):
        result1, result2 = await asyncio.gather(
            self.callForUpdate(id1, problemsChosen, startTime),
            self.callForUpdate(id2, problemsChosen, startTime)
        )

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
            
            row = i // len(board)
            col = i % len(board)
            
            if one:
                board[row][col] = " X"
            elif two:
                board[row][col] = " O"
        return board

    @app_commands.command(name="tictactoe")
    async def tictactoe(
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
        
        async with self.bot.session.get("https://codeforces.com/api/problemset.problems") as resp:
             if resp.status != 200:
                  await interaction.followup.send("Failed to fetch problems.")
                  return
             data = await resp.json()
             
        problems = data["result"]["problems"]
        problemSet = {}

        ratings = getRatings(average_rating, board_size)

        for problem in problems:
            # Safely get fields
            if "contestId" not in problem or "rating" not in problem:
                continue
            if problem["contestId"] < 1286:
                continue
            
            p_rating = problem["rating"]
            if p_rating in ratings:
                if p_rating not in problemSet:
                    problemSet[p_rating] = []
                problemSet[p_rating].append(problem)

        problemsChosen = []
        for i in range(board_size * board_size):
            target_rating = ratings[i]
            if not problemSet.get(target_rating):
                 # Try to find *any* problem if exact rating missing, or close rating?
                 # Simple fallback: find nearest rating
                 available_ratings = sorted(problemSet.keys())
                 if not available_ratings:
                      await interaction.followup.send("Not enough problems found generally.")
                      return
                 # Find closest
                 closest = min(available_ratings, key=lambda x: abs(x - target_rating))
                 problemsChosen.append(problemSet[closest].pop())
            else:
                 index = random.randint(0, len(problemSet[target_rating]) - 1)
                 problemsChosen.append(problemSet[target_rating].pop(index))

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
        
        while (time.time() - start) < time_limit:
            try:
                remaining = time_limit - (time.time() - start)
                if remaining <= 0: break
                
                # Check for either button click OR timeout loop to auto-refresh not really possible with wait_for unless we loop it short
                # The user wants "Help functionality" -> maybe explain rules?
                # I'll add "Help" command later in General. 
                
                def check(i):
                     return (i.type == discord.InteractionType.component 
                             and i.data.get("custom_id") == "refreshTicTacToe" 
                             and i.message.id == message.id)
                
                button_interaction = await self.bot.wait_for(
                    "interaction", timeout=min(remaining, 300), check=check
                )
                
                await button_interaction.response.defer()
                
                table = await self.checkForUpdates(
                    table, codeforce_id_1, codeforce_id_2, problemsChosen, int(start)
                )
                
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
                print(f"Error in tictactoe loop: {e}")
                break

async def setup(bot: commands.Bot):
    await bot.add_cog(TicTacToe(bot))
