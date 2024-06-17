from discord import app_commands
from discord import File, Object, Member
from discord import Colour, Interaction
from discord.app_commands import Choice, Range, command, describe
from discord.ext import commands
from discord.ui import View
import requests
import interactions
import random


class codeforces(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="challenge")
    async def _challenge(
        self,
        interaction: Interaction,
        rating: int = 1200,
        hrs: int = 2,
        mins: int = 0,
        channel_id: str = "1251535031600550009",
        message: str = "The challenge is here!",
        tags: str = "",
    ):
        """A server challenge to grab the top spot in the leaderboard"""
        channel_id = int(channel_id)
        await interaction.response.defer()
        if (
            interaction.user.id != 497352662451224578
            and not interaction.user.permissions_in(interaction.channel).administrator
        ):
            return await interaction.response.send_message(
                "You do not have the required permissions to run this command"
            )
        url = "https://codeforces.com/api/problemset.problems"
        response = requests.get(url)
        data = response.json()
        problems = data["result"]["problems"]
        tagsReq = []
        tagsNotReq = []
        tags = tags.split(",")
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
        if len(problemSet) == 0:
            return await interaction.response.send_message(
                "No problems found with the given criteria"
            )
        else:
            problem = random.choice(problemSet)
            url = f"https://codeforces.com/problemset/problem/{problem['contestId']}/{problem['index']}"
            channel = self.bot.get_channel(channel_id)
            colours = [0xDC143C, 0xD35400, 0x48C9B0, 0x7FB3D5]
            color = random.choice(colours)
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
            await channel.send(embeds=[embeds], content=message)
            await channel.send(
                """
The Point of this challenge is simple,
First - `10 Points`
Second and Third - `5 Points`
Fourth to Tenth - `2 Points`
Eleventh to Twentieth - `1 Point`
"""
            )
            await interaction.followup.send("```Problem sent to the channel```")


async def setup(bot: commands.Bot):
    await bot.add_cog(codeforces(bot))
