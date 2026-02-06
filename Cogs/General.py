import discord
from discord import app_commands
from discord.ext import commands
from discord import Object

class General(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="yo")
    async def yo(self, interaction: discord.Interaction, name: str):
        """Say yo to someone"""
        await interaction.response.send_message(f"Yo {name}", ephemeral=True)

    @app_commands.command(name="join")
    async def join(
        self,
        interaction: discord.Interaction,
        channel_name: discord.VoiceChannel = None,
        message_append: str = None,
        mute: bool = False,
        deafen: bool = False,
    ):
        """Join a voice channel"""
        if not channel_name:
             if interaction.user.voice:
                channel_name = interaction.user.voice.channel
             else:
                 await interaction.response.send_message("You are not in a voice channel and didn't specify one.", ephemeral=True)
                 return

        await interaction.response.defer()
        
        # Check if already connected
        if interaction.guild.voice_client:
             if interaction.guild.voice_client.channel.id == channel_name.id:
                  await interaction.followup.send("Already in that channel.")
                  return
             else:
                  await interaction.guild.voice_client.move_to(channel_name)
        else:
             await channel_name.connect()
        
        msg = f"Joined {channel_name.name}"
        if message_append:
            msg += f" {message_append}"
            
        await interaction.followup.send(msg, ephemeral=False)

        if interaction.guild.voice_client:
            if mute:
                await interaction.guild.voice_client.mute()
            if deafen:
                await interaction.guild.voice_client.deafen()

    @app_commands.command(name="invite")
    async def invite(self, interaction: discord.Interaction):
        """Get the bot invite link"""
        await interaction.response.send_message(
            "https://discord.com/oauth2/authorize?client_id=980733466968748122&permissions=18015352965184&integration_type=0&scope=applications.commands+bot",
            ephemeral=False,
        )

    @app_commands.command(name="test")
    async def test(self, interaction: discord.Interaction):
        """Test if the bot is working"""
        await interaction.response.send_message("the bot seems to be working as of rn")

    @app_commands.command(name="help")
    async def help(self, interaction: discord.Interaction):
        """List available commands and their descriptions"""
        embed = discord.Embed(title="Synanit 2.0 Help", description="List of available commands:", color=0x00ff00)
        
        # Iterate through all cogs and their commands
        for cog_name, cog in self.bot.cogs.items():
            # Get app commands from the cog
            commands_list = []
            for command in cog.walk_app_commands():
                commands_list.append(f"**/{command.name}**: {command.description}")
            
            if commands_list:
                embed.add_field(name=cog_name, value="\n".join(commands_list), inline=False)
                
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))
