import discord
from discord import app_commands, Interaction, ButtonStyle
from discord.ext import commands
from discord.ui import View, Button
import time
import asyncio
from typing import Dict, List, Optional
from utils.codeforces import CodeforcesAPI

class DuelGame:
    def __init__(self, mode: str, host: discord.User, rating: int, problems: List[Dict]):
        self.mode = mode
        self.host = host
        self.opponent: Optional[discord.User] = None
        self.rating = rating
        self.problems = problems
        self.start_time: float = 0
        self.is_active = False
        self.is_finished = False
        self.winner: Optional[discord.User] = None
        
        # Game State
        # Classic: results[user_id] = True/False
        # TicTacToe: board 3x3
        # Lockout: scores[user_id] = points
        self.scores = {} 
        self.solved_status = {} # {problem_key: solved_by_user_id}
        
    def add_opponent(self, user: discord.User):
        self.opponent = user
        self.scores[self.host.id] = 0
        self.scores[self.opponent.id] = 0
        
    def start(self):
        self.is_active = True
        self.start_time = time.time() - 30 # gives 30s buffer? No, let's strictly use current time.
        self.start_time = time.time() 

class DuelView(View):
    def __init__(self, game: DuelGame, cog):
        super().__init__(timeout=None) # Persistent view handled by external loop timeout
        self.game = game
        self.cog = cog
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        
        if not self.game.is_active:
            # Join Button
            join_btn = Button(label="Join Duel", style=ButtonStyle.green, custom_id="join_duel")
            join_btn.callback = self.join_callback
            self.add_item(join_btn)
            
            # Cancel Button (Host only)
            cancel_btn = Button(label="Cancel", style=ButtonStyle.red, custom_id="cancel_duel")
            cancel_btn.callback = self.cancel_callback
            self.add_item(cancel_btn)
        else:
            # Refresh Button
            refresh_btn = Button(label="🔄 Refresh", style=ButtonStyle.blurple, custom_id="refresh_duel")
            refresh_btn.callback = self.refresh_callback
            self.add_item(refresh_btn)
            
            # Forfeit Button
            forfeit_btn = Button(label="🏳️ Forfeit", style=ButtonStyle.red, custom_id="forfeit_duel")
            forfeit_btn.callback = self.forfeit_callback
            self.add_item(forfeit_btn)

    async def join_callback(self, interaction: Interaction):
        if interaction.user == self.game.host:
            await interaction.response.send_message("You cannot play against yourself!", ephemeral=True)
            return
            
        if self.game.opponent:
            await interaction.response.send_message("Game is full!", ephemeral=True)
            return

        self.game.add_opponent(interaction.user)
        self.game.start()
        self.update_buttons()
        
        embed = self.cog.create_game_embed(self.game)
        await interaction.response.edit_message(content=f"Duel started! {self.game.host.mention} vs {self.game.opponent.mention}", embed=embed, view=self)
        
        # Start auto-refresh loop for this game
        self.cog.bot.loop.create_task(self.cog.game_loop(self.game, interaction.message))

    async def cancel_callback(self, interaction: Interaction):
        if interaction.user != self.game.host:
            await interaction.response.send_message("Only the host can cancel.", ephemeral=True)
            return
            
        self.game.is_finished = True # cleanup
        self.stop()
        await interaction.response.edit_message(content="Duel cancelled.", embed=None, view=None)

    async def refresh_callback(self, interaction: Interaction):
        await interaction.response.defer()
        await self.cog.update_game_state(self.game, interaction.message)

    async def forfeit_callback(self, interaction: Interaction):
        if interaction.user not in [self.game.host, self.game.opponent]:
            await interaction.response.send_message("You are not in this game.", ephemeral=True)
            return
            
        winner = self.game.host if interaction.user == self.game.opponent else self.game.opponent
        self.game.winner = winner
        self.game.is_finished = True
        self.game.is_active = False
        
        embed = self.cog.create_game_embed(self.game)
        self.clear_items()
        await interaction.response.edit_message(content=f"{interaction.user.mention} forfeited! {winner.mention} wins!", embed=embed, view=self)

class Duel(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.cf_api = CodeforcesAPI()
        self.active_games = [] 

    def get_problem_url(self, problem):
        return f"https://codeforces.com/problemset/problem/{problem['contestId']}/{problem['index']}"

    def create_game_embed(self, game: DuelGame):
        embed = discord.Embed(title=f"⚔️ Duel: {game.mode}", color=0xFFD700)
        
        if not game.is_active:
             embed.description = f"Waiting for opponent...\nRating: {game.rating}"
             return embed

        # Status field
        status = f"**{game.host.display_name}** vs **{game.opponent.display_name}**"
        embed.add_field(name="Matchup", value=status, inline=False)
        
        # Problem List
        problems_text = ""
        
        if game.mode == "Classic":
             p = game.problems[0]
             url = self.get_problem_url(p)
             # Check if solved
             solved_by = game.solved_status.get(f"{p['contestId']}{p['index']}")
             icon = "✅" if solved_by else "⬜"
             if solved_by:
                  solver = game.host if solved_by == game.host.id else game.opponent
                  icon = f"✅ ({solver.display_name})"
                  
             problems_text = f"**Problem**: [{p['name']}]({url}) - {p['rating']} {icon}"
             
        elif game.mode == "TicTacToe":
            # 3x3 Grid
            board_str = ""
            for i in range(3):
                row_str = ""
                for j in range(3):
                    idx = i * 3 + j
                    p = game.problems[idx]
                    url = self.get_problem_url(p)
                    
                    key = f"{p['contestId']}{p['index']}"
                    solved_by = game.solved_status.get(key)
                    
                    symbol = "⬜"
                    if solved_by == game.host.id: symbol = "❌"
                    elif solved_by == game.opponent.id: symbol = "⭕"
                    
                    # Markdown link with emoji is tricky
                    # Let's list problems below details
                    # Just show board here
                    row_str += f"{symbol} "
                board_str += row_str + "\n"
            
            embed.add_field(name="Board", value=board_str, inline=False)
            
            # List problems
            plist = ""
            for i, p in enumerate(game.problems):
                key = f"{p['contestId']}{p['index']}"
                solved_by = game.solved_status.get(key)
                status = "Unsolved"
                if solved_by == game.host.id: status = f"Solved by {game.host.display_name}"
                elif solved_by == game.opponent.id: status = f"Solved by {game.opponent.display_name}"
                
                url = self.get_problem_url(p)
                plist += f"{i+1}. [{p['name']}]({url}) ({p['rating']}) - {status}\n"
            problems_text = plist

        elif game.mode == "Lockout":
             # Race to solve most of 5
             p_text = ""
             for i, p in enumerate(game.problems):
                  key = f"{p['contestId']}{p['index']}"
                  solved_by = game.solved_status.get(key)
                  
                  icon = "⬜"
                  if solved_by == game.host.id: icon = f"✅ {game.host.display_name}"
                  elif solved_by == game.opponent.id: icon = f"✅ {game.opponent.display_name}"
                  
                  url = self.get_problem_url(p)
                  p_text += f"{i+1}. [{p['name']}]({url}) ({p['rating']}) - {icon}\n"
             
             score_text = f"{game.host.display_name}: {game.scores[game.host.id]} | {game.opponent.display_name}: {game.scores[game.opponent.id]}"
             embed.add_field(name="Score", value=score_text, inline=False)
             problems_text = p_text

        embed.description = problems_text
        
        if game.winner:
            embed.color = 0x00FF00
            embed.set_footer(text=f"Winner: {game.winner.display_name}")
            
        return embed

    async def update_game_state(self, game: DuelGame, message: discord.Message):
         if game.is_finished: return
         
         # Check solutions
         # We need CF handles. For this prototype, I'll assume users have linked handles or I'll just check their submissions if provided
         # Wait, userStatus checks specific handle.
         # For simplicity, we assume users have set their handle? 
         # Or we can ask them?
         # The original bot didn't seem to have a robust user linking system exposed in the shared files, except 'users.json' or 'database' in ImageGenerator.
         # BUT `tictactoe.py` required passing `codeforce_id` as arguments.
         # So for `/duel`, we should probably ask for handles OR assume mapped.
         # The user requirement didn't specify handles param. "1. A user creates it. 2. Some other user clicks...".
         # So we need to know who is who on CF.
         # I will assume for now we need to ask handles or use Discord name if not provided (risky).
         # Let's check `users.json` or just use the system from `apl.py`?
         # Actually `apl.py` and `tictactoe.py` took handles as args.
         # I'll implement a simple handle registry or just ask in the command for now?
         # "Command: `/duel [mode] [rating]`". No handle arg.
         # I should adds a `/link` command or something, OR just ask for handle in the join/create modal?
         # Modal is best for "Join".
         # But the user said "some other user clicks on a button to join". Simple click.
         # I'll add `cf_handle` as an optional arg to `/duel` for host, but for opponent?
         # Maybe I'll assume their nickname is their handle for now or add a mapping command later.
         # OR: Just add a `/register` or `/link` command in General.
         # Let's stick to the requested "Button based join".
         # I'll add a simplified check: search for handle = discord display_name? No that's bad.
         # I'll add a `handle` argument to the `/duel` command for the host.
         # And prompt a Modal for the joiner? 
         # Or better: Just use a hardcoded map for the known users (since whitelist was small) OR just fallback to `users.json`.
         # Keep it simple: Ask handle in command for host. For joiner, maybe a Modal?
         # Let's try to infer or require registration.
         # Since this is "agentic", I'll decide: I will add `handle` arg to `/duel`. For joiner, I will implement a Join Modal.
         pass
         
         # Actually, implementation below.
    
    async def check_win_condition(self, game: DuelGame):
        if game.mode == "Classic":
             for k, v in game.solved_status.items():
                  if v:
                       game.winner = game.host if v == game.host.id else game.opponent
                       game.is_finished = True
                       return

        elif game.mode == "TicTacToe":
             # Check rows, cols, diags
             # grid 3x3
             grid = [[None for _ in range(3)] for _ in range(3)]
             for i in range(9):
                  p = game.problems[i]
                  key = f"{p['contestId']}{p['index']}"
                  solved_by = game.solved_status.get(key)
                  grid[i//3][i%3] = solved_by
             
             # Check lines
             lines = []
             # Rows
             lines.extend([grid[i] for i in range(3)])
             # Cols
             lines.extend([[grid[r][c] for r in range(3)] for c in range(3)])
             # Diags
             lines.append([grid[i][i] for i in range(3)])
             lines.append([grid[i][2-i] for i in range(3)])
             
             for line in lines:
                 if line[0] and all(x == line[0] for x in line):
                     game.winner = game.host if line[0] == game.host.id else game.opponent
                     game.is_finished = True
                     return

        elif game.mode == "Lockout":
             # First to majority (3 out of 5)
             # Or if all solved, who has more
             h_score = game.scores[game.host.id]
             o_score = game.scores[game.opponent.id]
             total_solved = h_score + o_score
             
             if h_score >= 3:
                  game.winner = game.host
                  game.is_finished = True
             elif o_score >= 3:
                  game.winner = game.opponent
                  game.is_finished = True
             elif total_solved == 5:
                  if h_score > o_score: game.winner = game.host
                  elif o_score > h_score: game.winner = game.opponent
                  else: game.winner = None # Draw
                  game.is_finished = True


    async def game_loop(self, game: DuelGame, message: discord.Message):
         while game.is_active and not game.is_finished:
              await asyncio.sleep(120) # 2 mins
              if game.is_finished: break
              try:
                   await self.update_game_state(game, message)
              except Exception as e:
                   print(f"Error in game loop: {e}")

    @app_commands.command(name="duel")
    @app_commands.describe(
        mode="Game Mode",
        rating="Problem Rating",
        handle="Your Codeforces Handle"
    )
    @app_commands.choices(mode=[
        app_commands.Choice(name="Classic", value="Classic"),
        app_commands.Choice(name="TicTacToe", value="TicTacToe"),
        app_commands.Choice(name="Lockout", value="Lockout")
    ])
    async def duel(self, interaction: Interaction, mode: str, rating: int, handle: str):
        """Start a coding duel!"""
        
        # Problem Count
        count = 1
        if mode == "TicTacToe": count = 9
        elif mode == "Lockout": count = 5
        
        # Search Problems
        problems = await self.cf_api.search_problems(
             self.bot.session, 
             min_rating=rating, 
             max_rating=rating+200, # A small range
             count=count
        )
        
        if len(problems) < count:
             await interaction.response.send_message("Not enough problems found for this rating.", ephemeral=True)
             return

        # Store host handle mapping temporarily in game object or globally?
        # I'll store it in game object for now
        
        game = DuelGame(mode, interaction.user, rating, problems)
        game.handles = {interaction.user.id: handle}
        
        # Create Invite Embed
        embed = discord.Embed(title=f"⚔️ New Duel: {mode}", description=f"Rating: {rating}\nHost: {interaction.user.mention}\nWaiting for opponent...", color=0x00FFFF)
        
        view = DuelView(game, self)
        
        await interaction.response.send_message(embed=embed, view=view)
        
        # Hack to get the message object
        message = await interaction.original_response()
        # The game loop starts only after join, so we wait.

    # Handling Join with Handle Input
    # Since we can't easily pop a modal from a button in a persistent view logic without some setup, 
    # I'll implement the Join logic to just ask for handle via a followup or just use a stored handle.
    # PROPER WAY: Button -> Modal.
    # I will modify DuelView.join_callback to return a Modal.

    async def update_game_state(self, game: DuelGame, message: discord.Message):
         if game.is_finished: return
         
         # Check status for both users
         host_handle = game.handles.get(game.host.id)
         opp_handle = game.handles.get(game.opponent.id)
         
         if not host_handle or not opp_handle:
              return
         
         # Check host
         solved_h, times_h = await self.cf_api.check_solved(self.bot.session, host_handle, game.problems, game.start_time)
         
         # Check opponent
         solved_o, times_o = await self.cf_api.check_solved(self.bot.session, opp_handle, game.problems, game.start_time)
         
         # Update game state
         for i, p in enumerate(game.problems):
             key = f"{p['contestId']}{p['index']}"
             if game.solved_status.get(key): continue # Already solved
             
             # Check who solved first if both solved in this tick
             h_solved = solved_h[i]
             o_solved = solved_o[i]
             
             if h_solved and o_solved:
                  # Compare times
                  if times_h[i] <= times_o[i]:
                       game.solved_status[key] = game.host.id
                       game.scores[game.host.id] += 1
                  else:
                       game.solved_status[key] = game.opponent.id
                       game.scores[game.opponent.id] += 1
             elif h_solved:
                  game.solved_status[key] = game.host.id
                  game.scores[game.host.id] += 1
             elif o_solved:
                  game.solved_status[key] = game.opponent.id
                  game.scores[game.opponent.id] += 1
                  
         await self.check_win_condition(game)
         
         embed = self.create_game_embed(game)
         
         # If finished, remove view
         view = None if game.is_finished else DuelView(game, self)
         
         await message.edit(embed=embed, view=view)


# Update DuelView to handle Modal for Join
import discord.ui

class JoinModal(discord.ui.Modal, title="Enter CF Handle"):
    handle = discord.ui.TextInput(label="Codeforces Handle", placeholder="tourist")

    def __init__(self, view, interaction):
        super().__init__()
        self.view_ref = view
        self.original_interaction = interaction

    async def on_submit(self, interaction: Interaction):
        handle = self.handle.value
        game = self.view_ref.game
        
        if interaction.user == game.host:
             await interaction.response.send_message("You are the host!", ephemeral=True)
             return
             
        game.add_opponent(interaction.user)
        game.handles[interaction.user.id] = handle
        game.start()
        
        self.view_ref.update_buttons()
        embed = self.view_ref.cog.create_game_embed(game)
        
        await interaction.response.edit_message(content=f"Duel started! {game.host.mention} vs {game.opponent.mention}", embed=embed, view=self.view_ref)
        
        # Start loop
        self.view_ref.cog.bot.loop.create_task(self.view_ref.cog.game_loop(game, interaction.message))

# Monkey patch Join Callback to use Modal
async def join_callback_modal(self, interaction: Interaction):
    # Check if host
    if interaction.user == self.game.host:
        await interaction.response.send_message("You cannot play against yourself!", ephemeral=True)
        return
    if self.game.opponent:
         await interaction.response.send_message("Full!", ephemeral=True)
         return
         
    await interaction.response.send_modal(JoinModal(self, interaction))

DuelView.join_callback = join_callback_modal


async def setup(bot: commands.Bot):
    await bot.add_cog(Duel(bot))
