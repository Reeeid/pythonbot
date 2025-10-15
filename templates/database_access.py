
import discord
import sqlite3
from discord.commands import slash_command, Option
from discord.ext import commands

# This template demonstrates database interaction within a cog.
# It uses Python's built-in sqlite3 library for simplicity.
# It manages a simple database of items.

# Path to the database file. It will be created in the `templates` directory.
DB_PATH = "templates/template.db"

class DatabaseCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.init_db()

    def get_db_connection(self):
        """Establishes a connection to the database."""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # This allows accessing columns by name
        return conn

    def init_db(self):
        """Initializes the database and creates the `items` table if it doesn't exist."""
        with self.get_db_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT NOT NULL
                );
            """)
            conn.commit()

    @slash_command(name="add_item", description="Adds a new item to the database.")
    async def add_item(
        self,
        ctx: discord.ApplicationContext,
        name: Option(str, "The name of the item."),
        description: Option(str, "A short description of the item.")
    ):
        """Adds a new item to the database."""
        try:
            with self.get_db_connection() as conn:
                conn.execute("INSERT INTO items (name, description) VALUES (?, ?)", (name, description))
                conn.commit()
            await ctx.respond(f"Item '{name}' has been added successfully!")
        except sqlite3.IntegrityError:
            await ctx.respond(f"Error: An item with the name '{name}' already exists.", ephemeral=True)
        except Exception as e:
            await ctx.respond(f"An unexpected error occurred: {e}", ephemeral=True)

    @slash_command(name="get_item", description="Retrieves an item from the database.")
    async def get_item(self, ctx: discord.ApplicationContext, name: Option(str, "The name of the item to find.")):
        """Retrieves an item from the database by its name."""
        with self.get_db_connection() as conn:
            cursor = conn.execute("SELECT * FROM items WHERE name = ?", (name,))
            item = cursor.fetchone()

        if item:
            # This is a simple text response. See embed_examples.py for a richer display.
            response = f"**{item['name']}**: {item['description']}"
            await ctx.respond(response)
        else:
            await ctx.respond(f"Item '{name}' not found.", ephemeral=True)

def setup(bot):
    bot.add_cog(DatabaseCog(bot))
