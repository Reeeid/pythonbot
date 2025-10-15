
import discord
import sqlite3
from discord.commands import slash_command, Option
from discord.ext import commands

# This template shows how to create and send embeds.
# It includes a static embed and an embed generated from database data.

# Assumes the database from database_access.py is in the same directory.
DB_PATH = "templates/template.db"

class EmbedExamples(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_db_connection(self):
        """Establishes a connection to the database."""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    @slash_command(name="show_static_embed", description="Displays a pre-designed embed.")
    async def static_embed(self, ctx: discord.ApplicationContext):
        """Sends a static, pre-designed embed message."""
        embed = discord.Embed(
            title="Static Embed Example",
            description="This is a demonstration of a static embed.",
            color=discord.Color.blue()  # You can use discord.Color presets
        )
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)
        embed.add_field(name="Field 1", value="This is the first field.", inline=False)
        embed.add_field(name="Field 2", value="This field is inline.", inline=True)
        embed.add_field(name="Field 3", value="So is this one.", inline=True)
        embed.set_footer(text="This is the footer.")

        await ctx.respond(embed=embed)

    @slash_command(name="show_item_embed", description="Shows item details in an embed.")
    async def item_embed(
        self,
        ctx: discord.ApplicationContext,
        name: Option(str, "The name of the item to display.")
    ):
        """Fetches an item from the database and displays it in a rich embed."""
        with self.get_db_connection() as conn:
            cursor = conn.execute("SELECT * FROM items WHERE name = ?", (name,))
            item = cursor.fetchone()

        if item:
            embed = discord.Embed(
                title=f"Item Details: {item['name']}",
                description=item['description'],
                color=discord.Color.green()
            )
            embed.add_field(name="ID", value=item["id"], inline=True)
            embed.add_field(name="Name", value=item["name"], inline=True)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}")
            await ctx.respond(embed=embed)
        else:
            error_embed = discord.Embed(
                title="Error",
                description=f"Item '{name}' not found in the database.",
                color=discord.Color.red()
            )
            await ctx.respond(embed=error_embed, ephemeral=True)

def setup(bot):
    bot.add_cog(EmbedExamples(bot))
