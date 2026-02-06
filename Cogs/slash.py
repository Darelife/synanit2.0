from datetime import datetime
from typing import Optional
import os
import asyncio
from discord import app_commands
from discord import File, Interaction
from discord.app_commands import Choice
from discord.ext import commands
import io

# Updated import path to use utils
from utils.ContestGraphImageGenerator import ContestGraphImageGenerator

class Graphs(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def _is_authorized(self, interaction: Interaction) -> bool:
        # Only allow user with ID 497352662451224578
        return interaction.user.id == 497352662451224578

    @app_commands.command(name="char")
    async def character(self, interaction: Interaction, text: str):
        """Writes the numbers of characters in the string"""
        await interaction.response.send_message(
            f"Your string has {len(text)} characters."
        )

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
    async def contest_graph(
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
            return generator.generate() # Returns BytesIO
        
        try:
            loop = asyncio.get_running_loop()
            image_buffer = await loop.run_in_executor(None, generate_image)
            
            if image_buffer:
                discord_file = File(image_buffer, filename=f"{description}.png")
                await interaction.followup.send(
                    f"Contest graph generated for Contest ID: {contest_id}",
                    file=discord_file
                )
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
    async def quick_graphs(
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
            generated_buffers = []
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
                    buf = generator.generate()
                    generated_buffers.append((descText, buf))
                except Exception as e:
                    print(f"Error generating {descText}: {e}")
            return generated_buffers
        
        try:
            loop = asyncio.get_running_loop()
            generated_buffers = await loop.run_in_executor(None, generate_all_images)
            
            if generated_buffers:
                discord_files = []
                for desc, buf in generated_buffers:
                    discord_files.append(File(buf, filename=f"{desc}.png"))
                
                await interaction.followup.send(
                    f"📊 All contest graphs generated for Contest ID: {contest_id}",
                    files=discord_files
                )
                
            else:
                await interaction.followup.send(
                    "❌ Failed to generate any contest graphs. Please check the contest ID and try again."
                )
                
        except Exception as e:
            await interaction.followup.send(
                f"❌ An error occurred while generating the contest graphs: {str(e)}"
            )

    @app_commands.command(name="contestplot")
    async def contestplot(self, interaction: Interaction, contestid: int):
         try:
             # Updated import path to use utils
             from utils.postIdeaAlgo import plotStuff
             await interaction.response.defer()
             
             loop = asyncio.get_running_loop()
             buf = await loop.run_in_executor(None, plotStuff, contestid)
             
             if buf:
                 await interaction.followup.send(file=File(buf, filename="plot.png"), ephemeral=False)
             else:
                 await interaction.followup.send("Failed to generate plot.")
                 
         except ImportError:
             await interaction.response.send_message("Plotting module not found.", ephemeral=True)
         except Exception as e:
             await interaction.followup.send(f"Error: {e}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Graphs(bot))
