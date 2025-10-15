
import discord
from discord.commands import slash_command
from discord.ext import commands

# This template covers more advanced concepts like error handling and permission checks.

class AdvancedUsage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- Permission Checks ---
    # The following commands demonstrate how to restrict command access.

    @slash_command(name="admin_only", description="A command only usable by server administrators.")
    @commands.has_permissions(administrator=True)
    async def admin_only_command(self, ctx: discord.ApplicationContext):
        """A command restricted to users with the 'Administrator' permission."""
        await ctx.respond(f"Hello, Administrator {ctx.author.mention}!")

    @slash_command(name="owner_only", description="A command only usable by the bot owner.")
    @commands.is_owner()
    async def owner_only_command(self, ctx: discord.ApplicationContext):
        """A command restricted to the owner of the bot."""
        await ctx.respond(f"Hello, my owner, {ctx.author.mention}!")


    # --- Error Handling ---
    # This section demonstrates how to handle errors that occur within a cog.

    @slash_command(name="cause_error", description="A command designed to fail for demonstration.")
    async def cause_error(self, ctx: discord.ApplicationContext):
        """This command intentionally raises an error to show the handler."""
        # This will cause a ZeroDivisionError
        result = 1 / 0
        await ctx.respond(f"The result is {result}") # This line will not be reached

    # A local error handler for this specific cog.
    # This will catch errors from any command within this cog.
    async def cog_command_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        """Handles errors that occur in this cog's commands."""
        # You can handle different types of errors specifically.
        if isinstance(error, commands.MissingPermissions):
            await ctx.respond("You don't have the required permissions to run this command.", ephemeral=True)
        elif isinstance(error, commands.NotOwner):
            await ctx.respond("You must be the bot owner to use this command.", ephemeral=True)
        else:
            # For other errors, you might want to log them and inform the user.
            print(f"An error occurred in the AdvancedUsage cog: {error}")
            await ctx.respond(
                "An unexpected error occurred. I have logged it for the developer.",
                ephemeral=True
            )

def setup(bot):
    bot.add_cog(AdvancedUsage(bot))
