from contextlib import redirect_stdout
from io import StringIO
from os import remove
from textwrap import indent
from traceback import format_exc
from typing import Literal, Optional

import discord
from discord import File, Object
from discord.errors import HTTPException
from discord.ext.commands import (
    Bot,
    Cog,
    Context,
    ExtensionError,
    Greedy,
    command,
    group,
    is_owner,
)


class Mod(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self._last_result = None

    @command(hidden=True)
    @is_owner()
    async def load(self, ctx: Context, *, module: str) -> None:
        """Loads a module."""
        try:
            await self.bot.load_extension(module)

        except ExtensionError as e:
            await ctx.send(f"{e.__class__.__name__}: {e}")

        else:
            await ctx.send("\N{OK HAND SIGN}")

    @command(hidden=True)
    @is_owner()
    async def unload(self, ctx: Context, *, module: str) -> None:
        """Unloads a module."""
        try:
            await self.bot.unload_extension(module)

        except ExtensionError as e:
            await ctx.send(f"{e.__class__.__name__}: {e}")

        else:
            await ctx.send("\N{OK HAND SIGN}")

    @group(name="reload", hidden=True, invoke_without_command=True)
    @is_owner()
    async def _reload(self, ctx: Context, *, module: str) -> None:
        """Reloads a module."""
        try:
            await self.bot.reload_extension(module)

        except ExtensionError as e:
            await ctx.send(f"{e.__class__.__name__}: {e}")

        else:
            await ctx.send("\N{OK HAND SIGN}")

    @command(name="sync2", hidden=False)
    @is_owner()
    async def _sync(
        self,
        ctx: Context,
        guilds: Greedy[Object],
        spec: Optional[Literal["~", "*"]] = None,
    ) -> None:
        """Syncs the bot with the guilds.
        ,sync -> global sync
        ,sync ~ -> sync current guild
        ,sync * -> copies all global app commands to current guild and syncs
        ,sync id_1 id_2 -> syncs guilds with id 1 and 2"""
        if not guilds:
            if spec == "~":
                fmt = await self.bot.tree.sync(guild=ctx.guild)

            elif spec == "*":
                self.bot.tree.copy_global_to(guild=ctx.guild)
                fmt = await self.bot.tree.sync(guild=ctx.guild)

            else:
                fmt = await self.bot.tree.sync()

            await ctx.send(
                f"Synced {len(fmt)} commands {'globally' if spec is None else 'to the current guild.'}"
            )
            return

        fmt = 0
        for guild in guilds:
            try:
                await self.bot.tree.sync(guild=guild)
            except HTTPException:
                pass
            else:
                fmt += 1

        await ctx.send(f"Synced the tree to {fmt}/{len(guilds)} guilds.")

    @staticmethod
    def cleanup_code(content: str) -> str:
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        # content = content.replace("```", "\n```")
        content = content.replace("```python", "\n```")
        content = content.replace("```py", "\n```")
        if content.startswith("```") and content.endswith("```"):
            return "\n".join(content.split("\n")[1:-1])

        return content.strip("` \n")

    @command(name="eval", aliases=["e"])
    @is_owner()
    async def _eval(self, ctx: Context, *, body: str) -> None:
        """Evaluates a code"""
        env = {
            "client": self.bot,
            "ctx": ctx,
            "channel": ctx.channel,
            "author": ctx.author,
            "guild": ctx.guild,
            "message": ctx.message,
            "_": self._last_result,
        }

        env.update(globals())

        body = self.cleanup_code(body)
        stdout = StringIO()

        to_compile = f'async def func():\n{indent(body, "  ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(f"```py\n{e.__class__.__name__}: {e}\n```")

        func = env["func"]
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            await ctx.send(f"```py\n{value}{format_exc()}\n```")
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction("\u2705")
            except:
                pass

            try:
                if ret is None:
                    if value:
                        await ctx.send(f"```py\n{value}\n```")
                else:
                    self._last_result = ret
                    await ctx.send(f"```py\n{value}{ret}\n```")
            except HTTPException:
                with open("result.txt", "w") as f:
                    f.write(f"{value}{ret}")
                remove("result.txt")

    @command(hidden=True, name="close", aliases=["shutdown"])
    @is_owner()
    async def _close(self, ctx: Context) -> None:
        """Closes the bot."""
        await ctx.send("Closing...")
        await self.bot.close()


async def setup(bot):
    await bot.add_cog(Mod(bot))
