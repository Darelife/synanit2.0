import discord
from discord import app_commands, TextChannel
from discord.ext import commands
import random
import json
import asyncio
from typing import Optional

class ButtonView(discord.ui.View):
    def __init__(self, questionNumber=1):
        super().__init__(timeout=60)
        self.questionNumber = questionNumber
        self.add_item(
            discord.ui.Button(
                label=f"➡️ Next Question (Q{questionNumber})",
                custom_id="refreshCodeforceQuestion",
            )
        )
    
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        # Note: We can't edit the message easily here without storing it, 
        # so we rely on the command handling to disable it eventually or just let it fail silently.

class Codeforces(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def fetch_json(self, url: str, method="GET", json_data=None, headers=None):
        async with self.bot.session.request(method, url, json=json_data, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            return None

    @app_commands.command(name="randomproblem")
    @app_commands.describe(
        rating="800-2500. For a range, 1400:1800, and for union, |, 1400:1700|1800"
    )
    async def randomproblem(self, interaction: discord.Interaction, rating: str):
        await interaction.response.defer()
        colours = [0xDC143C, 0xD35400, 0x48C9B0, 0x7FB3D5]
        color = random.choice(colours)

        def parse_rating(rating_str):
            rating_str = rating_str.upper().replace(" ", "")
            rating_ranges = []
            for part in rating_str.split("|"):
                if part in ["E", "EASY"]:
                    rating_ranges.append(("leetcode", "EASY"))
                elif part in ["M", "MEDIUM"]:
                    rating_ranges.append(("leetcode", "MEDIUM"))
                elif part in ["H", "HARD"]:
                    rating_ranges.append(("leetcode", "HARD"))
                elif ":" in part:
                    try:
                        low, high = map(int, part.split(":"))
                        rating_ranges.append(("codeforces", (low, high)))
                    except Exception:
                        pass
                else:
                    try:
                        val = int(part)
                        rating_ranges.append(("codeforces", (val, val)))
                    except Exception:
                        pass
            return rating_ranges

        rating_ranges = parse_rating(rating)

        cf_problems = []
        try:
            cf_data = await self.fetch_json("https://codeforces.com/api/problemset.problems")
            if cf_data and cf_data["status"] == "OK":
                for typ, val in rating_ranges:
                    if typ != "codeforces":
                        continue
                    low, high = val
                    for p in cf_data["result"]["problems"]:
                        if "rating" in p and low <= p["rating"] <= high and "contestId" in p:
                            cf_problems.append(p)
        except Exception:
            pass

        lc_difficulties = [v for t, v in rating_ranges if t == "leetcode"]
        lc_problem = None
        if lc_difficulties:
            try:
                # Use LeetCode unofficial API
                query = """
                        query randomQuestion($difficulty: Difficulty) {
                          randomQuestion(difficulty: $difficulty) {
                            titleSlug
                            title
                            difficulty
                            questionFrontendId
                          }
                        }
                        """
                data = await self.fetch_json(
                    "https://leetcode.com/graphql",
                    method="POST",
                    json_data={
                        "query": query,
                        "variables": {"difficulty": random.choice(lc_difficulties)},
                    },
                    headers={"Content-Type": "application/json"}
                )
                
                if data and "data" in data and data["data"]["randomQuestion"]:
                    lc_problem = data["data"]["randomQuestion"]
            except Exception:
                pass

        sources = []
        if cf_problems:
            sources.append("codeforces")
        if lc_problem:
            sources.append("leetcode")

        if not sources:
            await interaction.followup.send("No problems found for the given rating.", ephemeral=True)
            return

        chosen = random.choice(sources)
        if chosen == "codeforces":
            problem = random.choice(cf_problems)
            embed = discord.Embed(
                title=f"{problem['index']}. {problem['name']}",
                description=f"Rating: `{problem['rating']}`",
                url=f"https://codeforces.com/contest/{problem['contestId']}/problem/{problem['index']}",
                color=color,
            )
            await interaction.followup.send(embed=embed, ephemeral=False)
        else:
            embed = discord.Embed(
                title=f"{lc_problem['questionFrontendId']}. {lc_problem['title']}",
                description=f"Difficulty: `{lc_problem['difficulty']}`",
                url=f"https://leetcode.com/problems/{lc_problem['titleSlug']}/",
                color=color,
            )
            await interaction.followup.send(embed=embed, ephemeral=False)

    @app_commands.command(name="qplz")
    @app_commands.describe(
        rating="The rating of the problem",
        tag="The tags of the problem : Format : +binary search, -dp",
    )
    async def qplz(self, interaction: discord.Interaction, rating: int = 1500, tag: str = ""):
        await interaction.response.defer()
        colours = [0xDC143C, 0xD35400, 0x48C9B0, 0x7FB3D5]
        color = random.choice(colours)
        
        data = await self.fetch_json("https://codeforces.com/api/problemset.problems")
        if not data or data["status"] != "OK":
             await interaction.followup.send("Failed to fetch problems from Codeforces.")
             return

        problems = data["result"]["problems"]
        tagsReq = []
        tagsNotReq = []
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
            if "rating" not in problem:
                continue
            if problem["rating"] == rating:
                if all(tag.lower() in problem["tags"] for tag in tagsReq) and all(
                    tag.lower() not in problem["tags"] for tag in tagsNotReq
                ):
                    problemSet.append(problem)
        
        view = ButtonView()
        
        if not problemSet:
             await interaction.followup.send("No problems found", ephemeral=False)
             return

        async def send_new_problem(interaction_or_message, current_view):
            problem = random.choice(problemSet)
            problemName = f"{problem['index']}. {problem['name']}"
            embed = discord.Embed(
                title=problemName,
                description=f"Rating: `{problem['rating']}`",
                url=f"https://codeforces.com/contest/{problem['contestId']}/problem/{problem['index']}",
                color=color,
            )
            embed.add_field(
                name="Tags", value=f"`{', '.join(problem['tags'])}`", inline=False
            )
            
            if isinstance(interaction_or_message, discord.Interaction):
                 # Initial send
                 msg = await interaction_or_message.followup.send(
                    embed=embed,
                    ephemeral=False,
                    view=current_view,
                )
                 return msg
            else:
                 # Update existing
                 await interaction_or_message.edit(embed=embed, view=current_view)

        # Initial message
        message = await send_new_problem(interaction, view)

        questionNumber = 1
        current_view = view
        
        while True:
            questionNumber += 1
            try:
                next_view = ButtonView(questionNumber)
                
                # Wait for button click
                def check(i):
                     return (i.type == discord.InteractionType.component 
                             and i.data.get("custom_id") == "refreshCodeforceQuestion" 
                             and i.message.id == message.id 
                             and i.user.id == interaction.user.id)

                button_interaction = await self.bot.wait_for(
                    "interaction",
                    timeout=60,
                    check=check
                )
                
                # Disable old view
                for item in current_view.children:
                    item.disabled = True
                
                # We need to defer the button interaction update
                await button_interaction.response.defer()
                
                # Update message with new problem and new view
                await send_new_problem(message, next_view)
                
                current_view = next_view
                
            except asyncio.TimeoutError:
                for item in current_view.children:
                    item.disabled = True
                await message.edit(view=current_view)
                break
            except Exception as e:
                print(f"Error in qplz loop: {e}")
                break

    @app_commands.command(name="challenge")
    async def challenge(
        self,
        interaction: discord.Interaction,
        channel_name: TextChannel,
        rating: int = 1200,
        message: str = "The challenge is here!",
        tags: str = "",
    ):
        """A server challenge to grab the top spot in the leaderboard"""
        channel_id = channel_name.id
        await interaction.response.defer()
        
        try:
             with open("whitelist.json", "r") as f:
                whitelist = json.load(f)
        except FileNotFoundError:
             whitelist = []

        if (
            interaction.user.id != 497352662451224578
            and interaction.user.id not in whitelist
        ):
            return await interaction.followup.send(
                "You do not have the required permissions to run this command"
            )
            
        data = await self.fetch_json("https://codeforces.com/api/problemset.problems")
        if not data:
             return await interaction.followup.send("Failed to fetch Codeforces problems.")

        problems = data["result"]["problems"]
        tagsReq = []
        tagsNotReq = []
        tags_list = tags.split(",")
        for i in tags_list:
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
            if "rating" not in problem:
                continue
            if problem["rating"] == rating:
                if all(tag.lower() in problem["tags"] for tag in tagsReq) and all(
                    tag.lower() not in problem["tags"] for tag in tagsNotReq
                ):
                    problemSet.append(problem)
                    
        if not problemSet:
            return await interaction.followup.send(
                "No problems found with the given criteria"
            )
        else:
            problem = random.choice(problemSet)
            # Re-roll as in original code? (it did random.choice twice)
            problem = random.choice(problemSet)

            colours = [0xDC143C, 0xD35400, 0x48C9B0, 0x7FB3D5]
            color = random.choice(colours)
            problemName = f'{problem["index"]}. {problem["name"]}'
            
            embed = discord.Embed(
                title=problemName,
                description=f"Rating: `{problem['rating']}`",
                url=f"https://codeforces.com/contest/{problem['contestId']}/problem/{problem['index']}",
                color=color,
            )
            embed.add_field(
                name="Tags", value=f"`{', '.join(problem['tags'])}`", inline=False
            )
            
            target_channel = self.bot.get_channel(channel_id)
            if target_channel:
                await target_channel.send(embed=embed, content=message)
                await target_channel.send(
                    """
The Point of this challenge is simple,
First - `10 Points`
Second and Third - `5 Points`
Fourth to Tenth - `2 Points`
Eleventh to Twentieth - `1 Point`
"""
                )
                await interaction.followup.send("```Problem sent to the channel```")
            else:
                await interaction.followup.send("Could not find the target channel.")

    @app_commands.command(name="challenge-update")
    async def challenge_update(
        self,
        interaction: discord.Interaction,
        message_id: str,
        channel_name: TextChannel,
    ):
        """Update the challenge message"""
        channel_id = channel_name.id
        try:
             message_id = int(message_id)
        except ValueError:
             await interaction.response.send_message("Invalid message ID")
             return

        await interaction.response.defer()
        
        try:
             with open("whitelist.json", "r") as f:
                whitelist = json.load(f)
        except FileNotFoundError:
             whitelist = []

        if (
            interaction.user.id != 497352662451224578
            and interaction.user.id not in whitelist
        ):
            return await interaction.followup.send(
                "You do not have the required permissions to run this command"
            )
            
        channel = self.bot.get_channel(channel_id)
        if not channel:
             return await interaction.followup.send("Channel not found.")
             
        try:
            message = await channel.fetch_message(message_id)
        except discord.NotFound:
            return await interaction.followup.send("Message not found.")

        if not message.embeds:
             return await interaction.followup.send("Message has no embeds.")

        url = message.embeds[0].url
        url_parts = url.split("/")
        # Expected format: https://codeforces.com/contest/{contestId}/problem/{index}
        try:
             contestId = url_parts[-3]
             index = url_parts[-1]
        except IndexError:
             return await interaction.followup.send("Could not parse problem URL.")

        url2 = f"https://codeforces.com/api/contest.status?contestId={contestId}&count=200"
        data = await self.fetch_json(url2)
        if not data or data["status"] != "OK":
             return await interaction.followup.send("Failed to fetch contest status.")

        results = data["result"]
        
        try:
            with open("users.json", "r") as f:
                users = json.load(f)
        except FileNotFoundError:
            return await interaction.followup.send("users.json not found.")

        handleList = list(users.values())
        
        submissions = []
        for i in results:
            if i.get("verdict") == "OK" and i["problem"]["index"] == index:
                # Check for author handle
                if "members" in i["author"] and i["author"]["members"]:
                    handle = i["author"]["members"][0]["handle"]
                    if handle in handleList:
                        submissions.append((handle, i["creationTimeSeconds"]))

        submissions.sort(key=lambda x: x[1])
        
        # Deduplicate, keeping earliest
        unique_submissions = []
        seen = set()
        for sub in submissions:
             if sub[0] not in seen:
                  seen.add(sub[0])
                  unique_submissions.append(sub[0]) # Just handle name
        
        submissions = unique_submissions
        
        points = {}
        for i, handle in enumerate(submissions):
            if i == 0:
                points[handle] = 10
            elif i == 1 or i == 2:
                points[handle] = 5
            elif 3 <= i <= 9:
                points[handle] = 2
            elif 10 <= i <= 19:
                points[handle] = 1
                
        res = ""
        for i, (key, value) in enumerate(points.items(), 1):
            res += f"{i}. {key} - {value}\n"
            
        await interaction.followup.send(res if res else "No valid submissions found yet.")

    @app_commands.command(name="challenge-end")
    async def challenge_end(
        self,
        interaction: discord.Interaction,
        message_id: str,
        channel_name: TextChannel,
    ):
        """End the challenge"""
        # Logic is very similar to update but also updates leaderboard
        # For brevity, I will implement a simplified version or replicate the logic carefully.
        # Since the original code had hardcoded message IDs for the leaderboard update, 
        # I should be careful. 
        # logic: calculate points -> print -> update hardcoded leaderboard message.
        
        channel_id = channel_name.id
        try:
             message_id = int(message_id)
        except ValueError:
             await interaction.response.send_message("Invalid message ID")
             return

        await interaction.response.defer()
        
        try:
             with open("whitelist.json", "r") as f:
                whitelist = json.load(f)
        except FileNotFoundError:
             whitelist = []

        if (
            interaction.user.id != 497352662451224578
            and interaction.user.id not in whitelist
        ):
            return await interaction.followup.send(
                "You do not have the required permissions to run this command"
            )

        channel = self.bot.get_channel(channel_id)
        try:
            message = await channel.fetch_message(message_id)
        except Exception:
            return await interaction.followup.send("Could not fetch challenge message.")
            
        url = message.embeds[0].url
        url_parts = url.split("/")
        contestId = url_parts[-3]
        index = url_parts[-1]
        
        url2 = f"https://codeforces.com/api/contest.status?contestId={contestId}&count=200"
        data = await self.fetch_json(url2)
        if not data: return await interaction.followup.send("Failed to get status.")
        
        results = data["result"]
        with open("users.json", "r") as f:
            users = json.load(f)
        handleList = list(users.values())
        
        submissions = []
        for i in results:
            if i.get("verdict") == "OK" and i["problem"]["index"] == index:
                 if "members" in i["author"] and i["author"]["members"]:
                    handle = i["author"]["members"][0]["handle"]
                    if handle in handleList:
                        submissions.append((handle, i["creationTimeSeconds"]))
                        
        submissions.sort(key=lambda x: x[1])
        unique_submissions = []
        seen = set()
        for sub in submissions:
             if sub[0] not in seen:
                  seen.add(sub[0])
                  unique_submissions.append(sub[0])
        submissions = unique_submissions
        
        points = {}
        for i, handle in enumerate(submissions):
            if i == 0: points[handle] = 10
            elif i in [1, 2]: points[handle] = 5
            elif 3 <= i <= 9: points[handle] = 2
            elif 10 <= i <= 19: points[handle] = 1
            
        res = ""
        for i, (key, value) in enumerate(points.items(), 1):
            res += f"{i}. {key} - {value}\n"
        
        await interaction.followup.send(res if res else "No submissions.")
        
        # Leaderboard update logic (Hardcoded IDs from original)
        lb_channel = self.bot.get_channel(1251518237951131698)
        if lb_channel:
            try:
                lb_message = await lb_channel.fetch_message(1252313189169758268)
                content_lines = lb_message.content.split("\n")
                # Attempt to parse existing leaderboard
                # Filter out code block markers and header
                filtered_lines = [l for l in content_lines if "-" in l and "." in l]
                
                lb_points = {}
                for line in filtered_lines:
                    try:
                        # expected: "1. Name - Score"
                        parts = line.split(". ")
                        if len(parts) > 1:
                            sub_parts = parts[1].split(" - ")
                            if len(sub_parts) > 1:
                                name = sub_parts[0]
                                score = int(sub_parts[1])
                                lb_points[name] = score
                    except Exception:
                        pass
                
                # Update points
                for handle, score in points.items():
                    lb_points[handle] = lb_points.get(handle, 0) + score
                
                # Reconstruct
                sorted_lb = sorted(lb_points.items(), key=lambda item: item[1], reverse=True)
                new_res = ""
                for i, (handle, score) in enumerate(sorted_lb, 1):
                    new_res += f"{i}. {handle} - {score}\n"
                
                new_content = f"LEADERBOARD\n```\n{new_res}```"
                await lb_message.edit(content=new_content)
                await interaction.followup.send(f"Leaderboard updated.\n{res}")
                
            except Exception as e:
                await interaction.followup.send(f"Failed to update leaderboard: {e}")

    @app_commands.command(name="challenge-leaderboard-reset")
    async def challenge_leaderboard_reset(self, interaction: discord.Interaction):
        """Reset the challenge"""
        await interaction.response.defer()
        
        try:
             with open("whitelist.json", "r") as f:
                whitelist = json.load(f)
        except FileNotFoundError:
             whitelist = []

        if (
            interaction.user.id != 497352662451224578
            and interaction.user.id not in whitelist
        ):
            return await interaction.followup.send(
                "You do not have the required permissions to run this command"
            )

        channel = self.bot.get_channel(1251518237951131698)
        if channel:
            try:
                message = await channel.fetch_message(1252313189169758268)
                # Hardcoded list from original
                reset_content = """LEADERBOARD
```
1. Darelife - 0
2. prakharg11 - 0
3. shrey71 - 0
4. mathmath33 - 0
5. unbased - 0
6. harshb - 0
7. acsde - 0
```"""
                await message.edit(content=reset_content)
                await interaction.followup.send("```Leaderboard reset```")
            except Exception as e:
                await interaction.followup.send(f"Failed to reset: {e}")
        else:
             await interaction.followup.send("Leaderboard channel not found.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Codeforces(bot))
