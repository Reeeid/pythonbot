
import discord
from discord.commands import slash_command, Option
from discord.ext import commands

# This is a template for a basic cog.
# Cogs are used to organize your commands, listeners, and other functionality.
# To use this template, you would copy this file to your `src/cogs` directory
# and rename it. Then, you would load the cog in your `main.py` file.

class BasicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # A simple slash command that sends a "Hello!" message.
    # The @slash_command decorator registers this method as a slash command.
    @slash_command(name="hello", description="Sends a friendly greeting.")
    async def hello(self, ctx: discord.ApplicationContext):
        """Sends a friendly greeting."""
        await ctx.respond("Hello!")

    # A slash command that takes a required argument.
    # The @slash_command decorator is used again, but this time with an Option.
    # The Option defines an argument that the user must provide.
    @slash_command(name="echo", description="Repeats what you say.")
    async def echo(
        self,
        ctx: discord.ApplicationContext,
        message: Option(str, "The message to repeat.")
    ):
        """Repeats what you say."""
        await ctx.respond(f"You said: {message}")

# The setup function is required for the bot to load the cog.
# It's called when you use `bot.load_extension("...cogs.your_cog_name")`
def setup(bot):
    bot.add_cog(BasicCommands(bot))

