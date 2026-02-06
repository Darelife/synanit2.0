from discord import app_commands
from discord import File, Object, Member
from discord import Colour, Interaction
from discord.app_commands import Choice, Range, command, describe
from discord.ext import commands
from discord.ui import View
import asyncio
import time

class Bet(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.bets = [] # In-memory list of bets
        self.bet_results = {} # In-memory results (persistent across current session)

    @app_commands.command(name="bet")
    async def _bet(
        self, interaction: Interaction, amount: int, option1: str, option2: str
    ):
        """Bets an amount of money"""
        await interaction.response.defer()
        
        bet_id = len(self.bets) + 1
        
        message = await interaction.followup.send(
            f"# Bet!\nOption A : {option1}\nOption B : {option2}\nAmount : {amount} coins\n`Bet ID : {bet_id}`"
        )
        
        await message.add_reaction("🇦")
        await message.add_reaction("🇧")
        
        currentTime = time.time()
        targetTime = currentTime + 60
        
        # Lock bet after 60s
        await asyncio.sleep(60)
        
        await interaction.edit_original_response(
            content=f"# Bet Locked \nOption A : {option1}\nOption B : {option2}\n`Bet ID: {bet_id}`\nTime Left : <t:{int(targetTime)}:R>"
        )
        
        message = await interaction.channel.fetch_message(message.id)
        reactions = message.reactions
        
        option1_people = []
        option2_people = []
        
        # Async iterator for reactions
        async for user in reactions[0].users():
             if user.id != self.bot.user.id:
                  option1_people.append(user.id)
                  
        async for user in reactions[1].users():
             if user.id != self.bot.user.id:
                  option2_people.append(user.id)
        
        bet_data = {
            "id": bet_id,
            "amount": amount,
            "option1": option1,
            "option2": option2,
            "option1_reactions": option1_people,
            "option2_reactions": option2_people,
            "done": False,
            "result": None,
        }
        
        self.bets.append(bet_data)
        
        # Display participants
        t = "Option 1: "
        for uid in bet_data["option1_reactions"]:
            t += f"<@!{uid}> "
        t += "\nOption 2: "
        if not bet_data["option2_reactions"]:
            t += "No one"
        else:
            for uid in bet_data["option2_reactions"]:
                t += f"<@!{uid}> "
        t += f"\nAmount: {bet_data['amount']}\n`Bet Id: {bet_data['id']}`"
        
        await interaction.edit_original_response(content=t)

    @app_commands.command(name="bet-info")
    async def _bet_info(self, interaction: Interaction, id: int):
        """Get information about a bet"""
        await interaction.response.defer()
        
        bet_data = next((b for b in self.bets if b["id"] == id), None)
        
        if bet_data:
            t = "Option 1: "
            for uid in bet_data["option1_reactions"]:
                t += f"<@!{uid}> "
            t += "\nOption 2: "
            for uid in bet_data["option2_reactions"]:
                t += f"<@!{uid}> "
            t += f"\nAmount: {bet_data['amount']}"
            t += f"\nId: {bet_data['id']}"
            await interaction.followup.send(content=t)
        else:
            await interaction.followup.send(content="Bet not found")

    @app_commands.command(name="bet-clear")
    async def _bet_clear(self, interaction: Interaction):
        if interaction.user.id != 497352662451224578:
            await interaction.response.send_message(
                "You are not allowed to use this command", ephemeral=True
            )
            return
        """Clear all bets"""
        await interaction.response.defer()
        self.bets = []
        await interaction.followup.send(content="All Bets cleared")

    @app_commands.command(name="bet-done")
    async def _bet_done(self, interaction: Interaction, id: int, option: int):
        """End a bet"""
        is_admin = (interaction.user.id == 497352662451224578 or 
                   (interaction.channel and interaction.user.permissions_in(interaction.channel).administrator))
        
        if not is_admin:
            await interaction.response.send_message(
                "You are not allowed to use this command", ephemeral=True
            )
            return
            
        await interaction.response.defer()
        
        bet_data = next((b for b in self.bets if b["id"] == id), None)
        if not bet_data:
             await interaction.followup.send("Bet ID not found.")
             return
             
        if bet_data["done"]:
            await interaction.followup.send("The bet has already been resolved")
            return
            
        result = str(option)
        if result == "1":
            bet_data["result"] = bet_data["option1"]
        elif result == "2":
            bet_data["result"] = bet_data["option2"]
        else:
            bet_data["result"] = "draw"
            
        # Calculate wins/losses
        d = {}
        amount = bet_data["amount"]
        
        if result == "1":
            for uid in bet_data["option1_reactions"]:
                d[uid] = d.get(uid, 0) + amount
            for uid in bet_data["option2_reactions"]:
                d[uid] = d.get(uid, 0) - amount
        elif result == "2":
             for uid in bet_data["option1_reactions"]:
                d[uid] = d.get(uid, 0) - amount
             for uid in bet_data["option2_reactions"]:
                d[uid] = d.get(uid, 0) + amount
        
        winners = [f"<@!{k}>" for k, v in d.items() if v > 0]
        losers = [f"<@!{k}>" for k, v in d.items() if v < 0]
        
        # Update persistent results
        for k, v in d.items():
             self.bet_results[str(k)] = self.bet_results.get(str(k), 0) + v
             
        res = ""
        if not winners and not losers:
            res += "The bet was a draw"
        elif not winners:
            res += f'{" ".join(losers)} lost the bet'
        elif not losers:
             res += f'{" ".join(winners)} won the bet'
        else:
             res += f'{" ".join(winners)} won, and {" ".join(losers)} lost'
             
        # Detailed stats
        response = ""
        for key, value in d.items():
            if value > 0:
                 response += f"<@!{key}> : +{value}\n"
            elif value < 0:
                 response += f"<@!{key}> : {value}\n"
            else:
                 response += f"<@!{key}> : 0\n"
        
        res += "\n" + response
        
        bet_data["done"] = True
        
        # DM Owner logic preserved
        # user = await self.bot.fetch_user(497352662451224578)
        # await user.send(self.bet_results)
        
        await interaction.followup.send(res)

async def setup(bot: commands.Bot):
    await bot.add_cog(Bet(bot))
