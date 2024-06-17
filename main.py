import discord
from discord.ext import commands
import json
import os
import aiohttp
import datetime
import logging
from typing import Literal, Optional
from discord import Object
from discord.ext.commands import Context, Greedy, Bot
from discord.errors import HTTPException
from discord import app_commands
from discord.ui import Button, View
import keep_alive
import requests
import random
import interactions
import asyncio

# TODO : If you are running it locally, uncomment the below line and comment the one after that
# with open("E:\\Programming\\bots\\synanit2.0\\secrets.json") as f:
#     secrets = json.load(f)
#     token = secrets["TOKEN"]
token = os.getenv("TOKEN")


class Synanit(Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix="?s", intents=intents, application_id=980733466968748122
        )
        # self.initial_extensions = ["Cogs.Mod", "Cogs.Anime", "Cogs.Manga", "Cogs.Character"]
        self.initial_extensions = ["Cogs.slash", "Cogs.admin"]

    async def setup_hook(self):
        self.session = aiohttp.ClientSession()
        # self.pool = AsyncConnectionPool(conninfo=environ["DATABASE_URL"])
        for ext in self.initial_extensions:
            await self.load_extension(ext)

    async def close(self):
        await self.session.close()
        await super().close()

    async def on_command_error(self, ctx, error):
        error = str(error).replace("`", "\\`")
        await ctx.send(f"An error occurred: ```{error}```")

    async def on_ready(self):
        print("Ready!")
        MY_GUILD = Object(id=697493731611508737)
        await self.tree.sync(guild=MY_GUILD)


client = Synanit()


@client.event
async def on_ready():
    print("Ready!")


async def load():
    for filename in os.listdir("./Cogs"):
        if filename.endswith(".py"):
            await client.load_extension(f"Cogs.{filename[:-3]}")


@client.event
async def on_presence_update(before, after):
    if after.status != before.status:
        print(
            f"Status change: {before.name} went from {before.status} to {after.status} at {datetime.datetime.now()}"
        )
        # with open("./userlog.txt", "r") as f:
        #     data = f.readlines()
        # data.append(f"{after.name} is now {after.status}\n")
        # with open("./userlog.txt", "w") as f:
        #     f.writelines(data)
        # print(after)
    # if before.activity != after.activity:
    #     if before.status == discord.Status.offline:
    #         with open("./userlog.txt", "a") as f:
    #             f.write(f"{after.name} is now online\n")
    #     elif after.status == discord.Status.offline:
    #         with open("./userlog.txt", "a") as f:
    #             f.write(f"{after.name} is now offline\n")


@client.command()
async def test(ctx):
    await ctx.send("the bot seems to be working as of rn")


@client.command(name="sync")
async def _sync(
    ctx: Context, guilds: Greedy[Object], spec: Optional[Literal["~", "*"]] = None
) -> None:
    """Syncs the bot with the guilds.
    ?ssync -> global sync
    ?ssync ~ -> sync current guild
    ?ssync * -> copies all global app commands to current guild and syncs
    ?ssync id_1 id_2 -> syncs guilds with id 1 and 2"""
    if not guilds:
        if spec == "~":
            fmt = await client.tree.sync(guild=ctx.guild)

        elif spec == "*":
            client.tree.copy_global_to(guild=ctx.guild)
            fmt = await client.tree.sync(guild=ctx.guild)

        else:
            fmt = await client.tree.sync()

        await ctx.send(
            f"Synced {len(fmt)} commands {'globally' if spec is None else 'to the current guild.'}"
        )
        return

    fmt = 0
    for guild in guilds:
        try:
            await client.tree.sync(guild=guild)
        except HTTPException:
            pass
        else:
            fmt += 1

    await ctx.send(f"Synced the tree to {fmt}/{len(guilds)} guilds.")


# @client.tree.command(guild=Object(id=890890610339373106))
@client.tree.command()
async def yo(interaction: discord.Interaction, name: str):
    await interaction.response.send_message(f"Yo {name}", ephemeral=True)


# make it join a vc on command
@client.tree.command()
async def join(
    interaction: discord.Interaction,
    id: str,
    message_append: str = None,
    mute: bool = False,
    deafen: bool = False,
    say_hello: bool = False,
):
    id = int(id)
    await interaction.response.defer()
    voice_channel = client.get_channel(id)
    await voice_channel.connect()
    await interaction.response.send_message(
        f"Joined {voice_channel.name} {message_append}", ephemeral=False
    )
    if mute:
        await client.voice_clients[0].main_mute()
    if deafen:
        await client.voice_clients[0].main_deafen()


class ButtonView(View):
    def __init__(self, questionNumber=1):
        super().__init__()
        self.questionNumber = questionNumber
        self.add_item(
            Button(
                label=f"➡️ Next Question (Q{questionNumber})",
                custom_id="refreshCodeforceQuestion",
            )
        )


@client.tree.command()
async def qplz(interaction: discord.Interaction, tag: str = "", rating: int = 1500):
    await interaction.response.defer()
    colours = [0xDC143C, 0xD35400, 0x48C9B0, 0x7FB3D5]
    color = random.choice(colours)
    url = "https://codeforces.com/api/problemset.problems?tags=implementation"
    # json
    response = requests.get(url)
    data = response.json()
    problems = data["result"]["problems"]
    tagsReq = []
    tagsNotReq = []
    # split tags into words
    tags = tag.split(", ")
    for i in tags:
        if len(i) > 0:
            if i[0] == "-":
                tagsNotReq.append(i[1:].lower())
            else:
                tagsReq.append(i[1:].lower())

    problemSet = []
    for problem in problems:
        if "contestId" not in problem:
            continue
        if problem["contestId"] < 1286:
            continue
        problem["tags"] = [tag.lower() for tag in problem["tags"]]
        # check if there's a rating in problem
        if "rating" not in problem:
            continue
        if problem["rating"] == rating:
            if all(tag.lower() in problem["tags"] for tag in tagsReq) and all(
                tag.lower() not in problem["tags"] for tag in tagsNotReq
            ):
                problemSet.append(problem)
            # problemSet.append(problem)
    view = ButtonView()
    try:
        button_interaction = await client.wait_for("interaction", timeout=300)
        if problemSet:
            problem = random.choice(problemSet)
            problemName = f'{problem["index"]}. {problem["name"]}'
            problemLink = f"[{problemName}](<https://codeforces.com/contest/{problem['contestId']}/problem/{problem['index']}>)"
            embeds = interactions.Embed(
                title=problemName,
                description=f"Rating: `{problem['rating']}`",
                url=f"https://codeforces.com/contest/{problem['contestId']}/problem/{problem['index']}",
                color=color,
            )
            # embeds.add_field(name="Rating", value=f"`{problem['rating']}`", inline=False)
            embeds.add_field(
                name="Tags", value=f"`{', '.join(problem['tags'])}`", inline=False
            )

            await interaction.followup.send(
                # f"Problem: {problemLink}\nRating: {problem['rating']}\nTags: {", ".join(problem['tags'])}\n",
                embeds=[embeds],
                ephemeral=False,
                view=view,
            )
        else:
            await interaction.followup.send("No problems found", ephemeral=False)

        # now, wait for the button click
        questionNumber = 1
        while True:
            questionNumber += 1
            try:
                view2 = ButtonView(questionNumber)
                button_interaction = await client.wait_for("interaction", timeout=60)
                if button_interaction.data["custom_id"] == "refreshCodeforceQuestion":
                    await button_interaction.response.defer()
                    # print("Button clicked!")  # it works
                    problem = random.choice(problemSet)
                    problemName = f'{problem["index"]}. {problem["name"]}'
                    problemLink = f"[{problemName}](<https://codeforces.com/contest/{problem['contestId']}/problem/{problem['index']}>)"
                    embeds = interactions.Embed(
                        title=problemName,
                        description=f"Rating: `{problem['rating']}`",
                        url=f"https://codeforces.com/contest/{problem['contestId']}/problem/{problem['index']}",
                        color=color,
                    )
                    # embeds.add_field(
                    #     name="Rating", value=f"`{problem['rating']}`", inline=False
                    # )
                    embeds.add_field(
                        name="Tags",
                        value=f"`{', '.join(problem['tags'])}`",
                        inline=False,
                    )
                    await button_interaction.message.edit(embeds=[embeds], view=view2)

            # Do additional processing here
            except asyncio.TimeoutError:
                for item in view2.children:
                    if isinstance(item, discord.ui.Button):
                        item.disabled = True
                await button_interaction.message.edit(view=view2)
                break
    except asyncio.TimeoutError:
        for item in view.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
        await button_interaction.message.edit(view=view)


# @client.event
# async def on_interaction(interaction: discord.Interaction):
#     if interaction.type == discord.InteractionType.component:
#         if interaction.data["custom_id"] == "refreshCodeforceQuestion":
#             # Check if the bot has already responded to the interaction
#             if not interaction.response.is_done():
#                 # If not, send an initial response
#                 # await interaction.response.send_message("Processing...")
#                 pass
#             # Then, edit the original response
#             await interaction.edit_original_response(content="Button clicked!")


@client.tree.command()
async def invite(interaction: discord.Interaction):
    await interaction.response.send_message(
        "https://discord.com/oauth2/authorize?client_id=980733466968748122&permissions=18015352965184&integration_type=0&scope=applications.commands+bot",
        ephemeral=False,
    )


@client.tree.command()
async def bet(
    interaction: discord.Interaction, amount: int, option1: str, option2: str
):
    # add reaction to the message
    await interaction.response.defer()
    with open("bets.json", "r") as f:
        data = json.load(f)
    bet_id = len(data) + 1
    message = await interaction.followup.send(
        f"Bet between {option1} and {option2} for {amount} coins -> `ID: {bet_id}`"
    )
    await message.add_reaction("🇦")
    await message.add_reaction("🇧")
    # wait for 60 seconds, and then lock the bet, and give the bet an ID -> store the bet in a json file
    await asyncio.sleep(60)
    await message.edit(content=f"Bet locked between {option1} and {option2}")
    # check the reactions and store the data
    reactions = await message.reactions
    option1_reactions = reactions[0].count
    option2_reactions = reactions[1].count

    data1 = {
        "id": bet_id,
        "amount": amount,
        "option1": option1,
        "option2": option2,
        "option1_reactions": option1_reactions,
        "option2_reactions": option2_reactions,
    }
    data.append(data1)
    with open("bets.json", "w") as f:
        json.dump(data, f)


# logger = logging.getLogger('discord')
# logger.setLevel(logging.DEBUG)
# logging.getLogger('discord.http').setLevel(logging.INFO)
# handler = logging.StreamHandler()
# dt_fmt = '%Y-%m-%d %H:%M:%S'
# formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
# handler.setFormatter(formatter)
# logger.addHandler(handler)
@client.command()
async def bbet(ctx, amount: int, option1: str, option2: str):
    with open("bets.json", "r") as f:
        data = json.load(f)
    bet_id = len(data) + 1
    message = await ctx.send(
        f"Bet between {option1} and {option2} for {amount} coins -> `ID: {bet_id}`"
    )
    await message.add_reaction("🇦")
    await message.add_reaction("🇧")
    # wait for 60 seconds, and then lock the bet, and give the bet an ID -> store the bet in a json file
    await asyncio.sleep(10)
    await message.edit(
        content=f"Bet locked between {option1} and {option2} -> ID: {bet_id}"
    )
    # check the reactions and store the data
    message = await message.channel.fetch_message(message.id)
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
    await ctx.send("Bet stored successfully")
    await ctx.send("Option 1 people: ")
    t = ""
    for i in data1["option1_reactions"]:
        t += f"<@!{i}> "
    await ctx.send(t)
    t = ""
    await ctx.send("Option 2 people: ")
    for i in data1["option2_reactions"]:
        t += f"<@!{i}> "
    await ctx.send(t)


@client.command()
async def betresult(ctx, id: int, result: str):
    with open("bets.json", "r") as f:
        data = json.load(f)
    t = data[id - 1]
    if t["done"]:
        await ctx.send("The bet has already been resolved")
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
    await ctx.send(res)
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
    await ctx.send(response)
    with open("betResults.json", "w") as f:
        json.dump(data1, f, indent=2)
    data[id - 1]["done"] = True
    with open("bets.json", "w") as f:
        json.dump(data, f, indent=2)
    for key, value in data1.items():
        # get userName from ID
        id = int(key)
        user = await client.fetch_user(id)
        nick = user.name
        if value < 0:  # If the user has lost money
            await ctx.send(f"{nick} has lost {-value} coins")
        else:
            await ctx.send(f"{nick} has won {value} coins")


handler = logging.StreamHandler()

keep_alive.keep_alive()

client.run(token)
