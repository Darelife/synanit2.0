import discord
import os
import aiohttp
import datetime
import json
from typing import Literal, Optional
from discord import Object
from discord.ext import commands
from discord.errors import HTTPException
from dotenv import load_dotenv

load_dotenv()

dev = False

if dev:
    # It's better to use environment variables or a config file that isn't hardcoded to a specific path if possible,
    # but I'll respect the original logic for now, just safer.
    try:
        with open("secrets.json") as f:
            secrets = json.load(f)
            token = secrets["TOKEN"]
    except FileNotFoundError:
        token = os.getenv("TOKEN")
else:
    token = os.getenv("TOKEN")


class Synanit(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix="?s",
            intents=intents,
            application_id=980733466968748122,
            status=discord.Status.idle,
            activity=discord.Game(name="with AlgoManiax's existence"),
        )
        self.session: aiohttp.ClientSession = None

    async def setup_hook(self):
        self.session = aiohttp.ClientSession()
        
        # Load extensions
        for filename in os.listdir("./Cogs"):
            if filename.endswith(".py"):
                try:
                    await self.load_extension(f"Cogs.{filename[:-3]}")
                    print(f"Loaded {filename}")
                except Exception as e:
                    print(f"Failed to load {filename}: {e}")

    async def close(self):
        if self.session:
            await self.session.close()
        await super().close()

    async def on_command_error(self, ctx, error):
        error = str(error).replace("`", "\\`")
        await ctx.send(f"An error occurred: ```{error}```")

    async def on_ready(self):
        print("Ready!")
        print(f"Logged in as {self.user.name} ({self.user.id})")
        
        MY_GUILD = Object(id=697493731611508737)
        ALGO_GUILD = Object(id=1246441351965446236)
        
        # It's generally better to sync globally or to specific guilds on demand, 
        # doing it on every startup can be rate limited.
        # But keeping original behavior for now.
        try:
             await self.tree.sync(guild=MY_GUILD)
             await self.tree.sync(guild=ALGO_GUILD)
             print("Tree synced.")
        except Exception as e:
             print(f"Failed to sync tree: {e}")

client = Synanit()

@client.event
async def on_member_join(member):
    role_id = 1263188323070119946
    role = member.guild.get_role(role_id)
    if role:
        await member.add_roles(role)

@client.event
async def on_presence_update(before, after):
    if after.status != before.status:
        # Reduced spam, keeping the print
        print(
            f"Status change: {before.name} went from {before.status} to {after.status} at {datetime.datetime.now()}"
        )

@client.command(name="sync")
@commands.is_owner()
async def _sync(
    ctx: commands.Context, guilds: commands.Greedy[Object], spec: Optional[Literal["~", "*"]] = None
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

if __name__ == "__main__":
    if token:
        client.run(token)
    else:
        print("No token found.")
