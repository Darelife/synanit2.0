from datetime import datetime, timedelta
from typing import Optional
import os
import asyncio
import threading
import time

from discord import app_commands
from discord import File, Object, Member
from discord import Colour, Interaction
from discord.app_commands import Choice, Range, command, describe
from discord.ext import commands
from discord.ui import View

from ContestGraphImageGenerator import ContestGraphImageGenerator


class Slash(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # @commands.Cog.listener()
    # async def on_member_join(self, member):
    #     channel = member.guild.system_channel
    #     if channel is not None:
    #         await channel.send(f'Welcome {member.mention}.')
    # Slash commands
    @app_commands.command(name="char")
    async def _character(self, interaction: Interaction, text: str):
        """Writes the numbers of characters in the string"""
        await interaction.response.send_message(
            f"Your string has {len(text)} characters."
        )

    def _is_authorized(self, interaction: Interaction) -> bool:
        # Only allow user with ID 497352662451224578
        return interaction.user.id == 497352662451224578

    @app_commands.command(name="contest_graph")
    @app_commands.describe(
        contest_id="The Codeforces contest ID",
        description="Description for the graph (e.g., 'TOP 5 - Overall')",
        image_style="Image style (0=dark, 1=brown, 2=purple, 3=blue)",
        batch_year="Filter by batch year (2022, 2023, 2024, or 'all' for all years)",
        contest_name="Override contest name (optional)"
    )
    @app_commands.choices(image_style=[
        Choice(name="Dark", value=0),
        Choice(name="Brown", value=1),
        Choice(name="Purple", value=2),
        Choice(name="Blue", value=3)
    ])
    @app_commands.choices(batch_year=[
        Choice(name="All Years", value="all"),
        Choice(name="2022", value="2022"),
        Choice(name="2023", value="2023"),
        Choice(name="2024", value="2024")
    ])
    async def _contest_graph(
        self, 
        interaction: Interaction, 
        contest_id: int,
        description: str = "Contest Graph",
        image_style: int = 0,
        batch_year: str = "all",
        contest_name: Optional[str] = None
    ):
        """Generate and send a contest graph showing student performance"""

        if not self._is_authorized(interaction):
            await interaction.response.send_message("❌ You are not authorized to use this command.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        if batch_year == "all":
            regex = r"^(2022|2023|2024).{9}$"
        else:
            regex = f"^({batch_year}).{{9}}$"
        
        def generate_image():
            generator = ContestGraphImageGenerator(
                contestId=contest_id,
                descText=description,
                imageSelected=image_style,
                regex=regex,
                overrideContestName=contest_name is not None,
                overrideText=contest_name or ""
            )
            generator.generate()
            return f"{description}.png"
        
        try:
            loop = asyncio.get_event_loop()
            image_path = await loop.run_in_executor(None, generate_image)
            
            if os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    discord_file = File(f, filename=image_path)
                    await interaction.followup.send(
                        f"Contest graph generated for Contest ID: {contest_id}",
                        file=discord_file
                    )
                try:
                    os.remove(image_path)
                except OSError:
                    pass
            else:
                await interaction.followup.send(
                    "❌ Failed to generate the contest graph. Please check the contest ID and try again."
                )
                
        except Exception as e:
            await interaction.followup.send(
                f"❌ An error occurred while generating the contest graph: {str(e)}"
            )

    @app_commands.command(name="quick_graphs")
    @app_commands.describe(
        contest_id="The Codeforces contest ID",
        contest_name="Override contest name (optional)"
    )
    async def _quick_graphs(
        self, 
        interaction: Interaction, 
        contest_id: int,
        contest_name: Optional[str] = None
    ):
        """Generate all standard contest graphs (Overall, 2023, 2022, 2024 batches)"""

        if not self._is_authorized(interaction):
            await interaction.response.send_message("❌ You are not authorized to use this command.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        params = [
            (contest_id, "TOP 5 - Overall", 0, r"^(2023|2024|2022).{9}$"),
            (contest_id, "TOP 5 - 2023 Batch", 2, r"^(2023).{9}$"),
            (contest_id, "TOP 5 - 2022 Batch", 3, r"^(2022).{9}$"),
            (contest_id, "TOP 5 - 2024 Batch", 1, r"^(2024).{9}$")
        ]
        
        def generate_all_images():
            generated_files = []
            for contestId, descText, imageSelected, regex in params:
                try:
                    generator = ContestGraphImageGenerator(
                        contestId=contestId,
                        descText=descText,
                        imageSelected=imageSelected,
                        regex=regex,
                        overrideContestName=contest_name is not None,
                        overrideText=contest_name or ""
                    )
                    generator.generate()
                    image_path = f"{descText}.png"
                    if os.path.exists(image_path):
                        generated_files.append(image_path)
                except Exception as e:
                    print(f"Error generating {descText}: {e}")
            return generated_files
        
        try:
            loop = asyncio.get_event_loop()
            generated_files = await loop.run_in_executor(None, generate_all_images)
            
            if generated_files:
                discord_files = []
                for image_path in generated_files:
                    with open(image_path, 'rb') as f:
                        discord_files.append(File(f, filename=os.path.basename(image_path)))
                
                await interaction.followup.send(
                    f"📊 All contest graphs generated for Contest ID: {contest_id}",
                    files=discord_files
                )
                
                for image_path in generated_files:
                    try:
                        os.remove(image_path)
                    except OSError:
                        pass
            else:
                await interaction.followup.send(
                    "❌ Failed to generate any contest graphs. Please check the contest ID and try again."
                )
                
        except Exception as e:
            await interaction.followup.send(
                f"❌ An error occurred while generating the contest graphs: {str(e)}"
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Slash(bot))
