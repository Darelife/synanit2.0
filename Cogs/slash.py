from datetime import datetime, timedelta
from typing import Optional

from discord import app_commands
from discord import File, Object, Member
from discord import Colour, Interaction
from discord.app_commands import Choice, Range, command, describe
from discord.ext import commands
from discord.ui import View

class Slash(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = member.guild.system_channel
        if channel is not None:
            await channel.send(f'Welcome {member.mention}.')
    
    @commands.command()
    async def hello(self, ctx, *, member: Member = None):
        """Says hello"""
        await ctx.send(f'Hello {member.mention if member else ctx.author.mention}.')

    # Slash commands
    @app_commands.command(name="command-1")
    async def my_command(self, interaction: Interaction) -> None:
        """ /command-1 """
        await interaction.response.send_message("Hello from command 1!", ephemeral=True)
    @app_commands.command(name='char')
    async def _character(self, interaction: Interaction, text: str):
        """Writes the numbers of characters in the string"""
        await interaction.response.send_message(f'Your string has {len(text)} characters.')
    

async def setup(bot: commands.Bot):
    await bot.add_cog(Slash(bot))