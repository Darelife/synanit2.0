from discord import app_commands
from discord import File, Object, Member
from discord import Colour, Interaction
from discord.app_commands import Choice, Range, command, describe
from discord.ext import commands
from discord.ui import View
import requests
import interactions
import random
import json


class codeforces(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="challenge")
    async def _challenge(
        self,
        interaction: Interaction,
        rating: int = 1200,
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

    @app_commands.command(name="challenge-update")
    async def _challenge_update(
        self,
        interaction: Interaction,
        message_id: str,
        channel_id: str,
    ):
        """Update the challenge message"""
        channel_id = int(channel_id)
        message_id = int(message_id)
        await interaction.response.defer()
        if (
            interaction.user.id != 497352662451224578
            and not interaction.user.permissions_in(interaction.channel).administrator
        ):
            return await interaction.response.send_message(
                "You do not have the required permissions to run this command"
            )
        channel = self.bot.get_channel(channel_id)
        message = await channel.fetch_message(message_id)
        url = message.embeds[0].url
        # await channel.send(url)
        url = url.split("/")
        contestId = url[-3]
        index = url[-1]
        url2 = (
            f"https://codeforces.com/api/contest.status?contestId={contestId}&count=200"
        )
        response = requests.get(url2)
        data = response.json()
        data = data["result"]
        # for i in data:
        with open("users.json", "r") as f:
            users = json.load(f)
        handleList = []
        for i in users:
            handleList.append(users[i])
        submissions = []
        for i in data:
            if i["verdict"] == "OK" and i["problem"]["index"] == index:
                if i["author"]["members"][0]["handle"] in handleList:
                    submissions.append(i["author"]["members"][0]["handle"])
        points = {}
        # reverse submissions
        submissions = list(set(submissions))
        submissions.sort(key=lambda x: submissions.count(x), reverse=True)
        for i in range(len(submissions)):
            if i == 0:
                points[submissions[i]] = 10
            elif i == 1 or i == 2:
                points[submissions[i]] = 5
            elif i >= 3 and i <= 9:
                points[submissions[i]] = 2
            elif i >= 10 and i <= 19:
                points[submissions[i]] = 1
        res = ""
        for key, value in points.items():
            res += f"{key} - {value}\n"
        await interaction.followup.send(res)

    @app_commands.command(name="challenge-end")
    async def _challenge_end(
        self,
        interaction: Interaction,
        message_id: str,
        channel_id: str,
    ):
        """End the challenge"""
        channel_id = int(channel_id)
        message_id = int(message_id)
        print("HELLO")
        await interaction.response.defer()
        if (
            interaction.user.id != 497352662451224578
            and not interaction.user.permissions_in(interaction.channel).administrator
        ):
            return await interaction.response.send_message(
                "You do not have the required permissions to run this command"
            )
        channel = self.bot.get_channel(channel_id)
        message = await channel.fetch_message(message_id)
        url = message.embeds[0].url
        # await channel.send(url)
        url = url.split("/")
        contestId = url[-3]
        index = url[-1]
        url2 = (
            f"https://codeforces.com/api/contest.status?contestId={contestId}&count=200"
        )
        response = requests.get(url2)
        data = response.json()
        data = data["result"]
        # for i in data:
        with open("users.json", "r") as f:
            users = json.load(f)
        handleList = []
        for i in users:
            handleList.append(users[i])
        submissions = []
        for i in data:
            if i["verdict"] == "OK" and i["problem"]["index"] == index:
                if i["author"]["members"][0]["handle"] in handleList:
                    submissions.append(i["author"]["members"][0]["handle"])
        points = {}
        # reverse submissions
        submissions = list(set(submissions))
        # submissions.sort(key=lambda x: submissions.count(x), reverse=True)
        for i in range(len(submissions)):
            if i == 0:
                points[submissions[i]] = 10
            elif i == 1 or i == 2:
                points[submissions[i]] = 5
            elif i >= 3 and i <= 9:
                points[submissions[i]] = 2
            elif i >= 10 and i <= 19:
                points[submissions[i]] = 1
        res = ""
        i = 1
        point = {}
        for key, value in points.items():
            res += f"{i}. {key} - {value}\n"
            point[key] = value
            i += 1
        await interaction.followup.send(res)
        # post it in the leaderboard channel
        #         await leaderboardChannel.send(
        #             f"""
        # # LEADERBOARD
        # ```
        # {res}
        # ```
        # """
        #         )
        # TODO : update the channel and message id
        channel = self.bot.get_channel(1251518237951131698)
        message = await channel.fetch_message(1252313189169758268)
        t = message.content.split("\n")
        print(t)
        t.pop(0)
        t.pop(0)
        t.pop(-1)
        # t.pop(-1)
        print(t)
        points = {}
        for i in t:
            try:
                j = i.split(". ")
                k = j[1].split(" - ")
                points[k[0]] = int(k[1])
            except:
                pass
            # j = i.split(". ")
            # k = j[1].split(" - ")
            # points[k[0]] = int(k[1])
        print(points)
        for i in point:
            if i in points:
                points[i] += point[i]
            else:
                points[i] = point[i]
        print(points)
        res = ""
        i = 1

        #         await message.edit(
        #             content=f"""LEADERBOARD
        # ```
        # 1. Darelife - 0
        # 2. prakharg11 - 0
        # 3. shrey71 - 0
        # 4. mathmath33 - 0
        # 5. unbased - 0
        # 6. harshb - 0
        # 7. acsde - 0
        # ```"""
        #         )

        for key, value in sorted(
            points.items(), key=lambda item: item[1], reverse=True
        ):
            print(key, value)
            res += f"{i}. {key} - {value}\n"
            i += 1
        await message.edit(
            content=f"""LEADERBOARD
```
{res}
```"""
        )
        print(res)

    @app_commands.command(name="challenge-leaderboard-reset")
    async def _challenge_leaderboard_reset(self, interaction: Interaction):
        """Reset the challenge"""
        channel_id = int(channel_id)
        await interaction.response.defer()
        if (
            interaction.user.id != 497352662451224578
            and not interaction.user.permissions_in(interaction.channel).administrator
        ):
            return await interaction.response.send_message(
                "You do not have the required permissions to run this command"
            )
        channel = self.bot.get_channel(1251518237951131698)
        message = await channel.fetch_message(1252313189169758268)
        await message.edit(
            content=f"""LEADERBOARD
```
1. Darelife - 0
2. prakharg11 - 0
3. shrey71 - 0
4. mathmath33 - 0
5. unbased - 0
6. harshb - 0
7. acsde - 0
```"""
        )
        await interaction.followup.send("```Leaderboard reset```")


async def setup(bot: commands.Bot):
    await bot.add_cog(codeforces(bot))
    # Assuming `tree` is your app command tree instance
    await bot.tree.sync(guild=Object(1246441351965446236))
