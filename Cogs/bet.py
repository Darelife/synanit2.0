from discord import app_commands
from discord import File, Object, Member
from discord import Colour, Interaction
from discord.app_commands import Choice, Range, command, describe
from discord.ext import commands
from discord.ui import View
import json
import asyncio


class bet(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="bet")
    async def _bet(
        self, interaction: Interaction, amount: int, option1: str, option2: str
    ):
        """Bets an amount of money"""
        await interaction.response.defer()
        with open("bets.json", "r") as f:
            data = json.load(f)
        bet_id = len(data) + 1
        message = await interaction.followup.send(
            f"Bet between {option1} and {option2} for {amount} coins -> `ID: {bet_id}`"
        )
        print(message.id)
        await message.add_reaction("🇦")
        await message.add_reaction("🇧")
        # wait for 60 seconds, and then lock the bet, and give the bet an ID -> store the bet in a json file
        await asyncio.sleep(10)
        await interaction.edit_original_response(
            content=f"Bet locked between {option1} and {option2} -> ID: {bet_id}"
        )
        message = await interaction.channel.fetch_message(message.id)

        reactions = message.reactions

        option1_people = [user async for user in reactions[0].users()]
        option2_people = [user async for user in reactions[1].users()]

        option1_people_ids = [user.id for user in option1_people]  # Extract user IDs
        option2_people_ids = [user.id for user in option2_people]

        data1 = {
            "id": bet_id,
            "amount": amount,
            "option1": option1,
            "option2": option2,
            "option1_reactions": option1_people_ids,  # Store user IDs instead of User objects
            "option2_reactions": option2_people_ids,
            "done": False,
        }
        # await ctx.send(data1)
        data.append(data1)
        # Now, data1 contains only serializable types
        with open("bets.json", "w") as f:
            json.dump(data, f, indent=2)
        t = "Option 1: "
        for i in data1["option1_reactions"]:
            t += f"<@!{i}> "
        t += "\nOption 2: "
        for i in data1["option2_reactions"]:
            t += f"<@!{i}> "
        t += f"\nAmount: {data1['amount']}"
        t += f"\nId: {data1['id']}"
        await interaction.edit_original_response(content=t)

    @app_commands.command(name="bet-info")
    async def _bet_info(self, interaction: Interaction, id: int):
        """Get information about a bet"""
        await interaction.response.defer()
        with open("bets.json", "r") as f:
            data = json.load(f)
        for i in data:
            if i["id"] == id:
                t = "Option 1: "
                for i in i["option1_reactions"]:
                    t += f"<@!{i}> "
                t += "\nOption 2: "
                for i in i["option2_reactions"]:
                    t += f"<@!{i}> "
                t += f"\nAmount: {i['amount']}"
                t += f"\nId: {i['id']}"
                await interaction.edit_original_response(content=t)
                return
        await interaction.edit_original_response(content="Bet not found")

    @app_commands.command(name="bet-clear")
    async def _bet_clear(self, interaction: Interaction):
        if interaction.user.id != 497352662451224578:
            await interaction.response.send_message(
                "You are not allowed to use this command", ephemeral=True
            )
            return
        """Clear all bets"""
        await interaction.response.defer()
        with open("bets.json", "w") as f:
            json.dump([], f)
        await interaction.edit_original_response(content="All Bets cleared")

    @app_commands.command(name="bet-done")
    async def _bet_done(self, interaction: Interaction, id: int, option: int):
        """End a bet"""
        # if not admin or owner
        if (
            interaction.user.id != 497352662451224578
            and not interaction.user.permissions_in(interaction.channel).administrator
        ):
            await interaction.response.send_message(
                "You are not allowed to use this command", ephemeral=True
            )
            return
        await interaction.response.defer()
        with open("bets.json", "r") as f:
            data = json.load(f)
        t = data[id - 1]
        result = str(option)
        if t["done"]:
            await interaction.followup.send("The bet has already been resolved")
            return
        if result == "1":
            t["result"] = t["option1"]
        elif result == "2":
            t["result"] = t["option2"]
        else:
            t["result"] = "draw"
        with open("betResults.json", "r") as f:
            data1 = json.load(f)
        d = {}
        if result == "1":
            for i in t["option1_reactions"]:
                if i not in d:
                    d[i] = t["amount"]
                else:
                    d[i] += t["amount"]
            for i in t["option2_reactions"]:
                if i not in d:
                    d[i] = -t["amount"]
                else:
                    d[i] -= t["amount"]
        elif result == "2":
            for i in t["option2_reactions"]:
                if i not in d:
                    d[i] = t["amount"]
                else:
                    d[i] += t["amount"]
            for i in t["option1_reactions"]:
                if i not in d:
                    d[i] = -t["amount"]
                else:
                    d[i] -= t["amount"]
        winners = []
        losers = []
        for key, value in d.items():
            if (value) > 0:
                winners.append(f"<@!{key}>")
            elif (value) < 0:
                losers.append(f"<@!{key}>")
            if str(key) in data1:
                data1[(str(key))] += value  # Update existing key with new value
            else:
                data1[(str(key))] = value  # Add new key-value pair
        res = ""
        if (len(winners) == 0) and (len(losers) == 0):
            res += "The bet was a draw"
        elif len(winners) == 0:
            if len(losers) == 1:
                res += f'{" ".join(losers)} has lost the bet'
            else:
                res += f'{" ".join(losers)} have lost the bet'
        elif len(losers) == 0:
            if len(winners) == 1:
                res += f'{" ".join(winners)} has won the bet'
            else:
                res += f'{" ".join(winners)} have won the bet'
        else:
            if (len(winners) == 1) and (len(losers) == 1):
                res += f'{" ".join(winners)} has won the bet, and {" ".join(losers)} has lost the bet'
            elif (len(winners) == 1) and (len(losers) > 1):
                res += f'{" ".join(winners)} has won the bet, and {" ".join(losers)} have lost the bet'
            elif (len(winners) > 1) and (len(losers) == 1):
                res += f'{" ".join(winners)} have won the bet, and {" ".join(losers)} has lost the bet'
            else:
                res += f'{" ".join(winners)} have won the bet, and {" ".join(losers)} have lost the bet'
        # await interaction.response.send(res)
        response = ""
        for key, value in d.items():
            if str(key) in data1:
                if d[key] > 0:
                    response += f"<@!{key}> : {value - d[key]} + {d[key]} = {value}\n"
                elif d[key] < 0:
                    response += f"<@!{key}> : {value - d[key]} - {-d[key]} = {value}\n"
                else:
                    response += f"<@!{key}> : {value}\n"
            else:
                response += f"<@!{key}> : {value}\n"
        res += "\n" + response
        with open("betResults.json", "w") as f:
            json.dump(data1, f, indent=2)
        data[id - 1]["done"] = True
        with open("bets.json", "w") as f:
            json.dump(data, f, indent=2)
        for key, value in data1.items():
            # get userName from ID
            id = int(key)
            user = await self.bot.fetch_user(id)
            nick = user.name
            if value < 0:  # If the user has lost money
                res += f"\n{nick} has lost {-value} coins"
            else:
                res += f"\n{nick} has won {value} coins"
        await interaction.followup.send(res)


async def setup(bot: commands.Bot):
    await bot.add_cog(bet(bot))
