

import discord
from discord.ext import commands
import aiosqlite
import os

class WhitelistCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'glossary.db') # glossary.dbを共有
        self.admin_id = int(os.getenv('ADMIN_ID'))
        self.bot.loop.create_task(self._async_setup_db()) # 非同期でDBセットアップを呼び出す

    async def _async_setup_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            # ホワイトリストテーブル
            await db.execute('''
                CREATE TABLE IF NOT EXISTS whitelist (
                    user_id INTEGER PRIMARY KEY
                )
            ''')
            await db.commit()

    async def _is_admin(self, user_id):
        return user_id == self.admin_id

    # ホワイトリスト管理コマンドグループ
    whitelist = discord.SlashCommandGroup("whitelist", "ホワイトリスト管理コマンド (管理者のみ)。")

    @whitelist.command(name="add", description="ユーザーをホワイトリストに追加します (管理者のみ)。")
    async def whitelist_add(self, ctx: discord.ApplicationContext, user: discord.User):
        if not await self._is_admin(ctx.author.id):
            await ctx.respond("このコマンドを実行する権限がありません。", ephemeral=True)
            return

        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute('INSERT INTO whitelist (user_id) VALUES (?)', (user.id,))
                await db.commit()
                await ctx.respond(f"ユーザー `{user.name}` をホワイトリストに追加しました。")
            except aiosqlite.IntegrityError:
                await ctx.respond(f"ユーザー `{user.name}` は既にホワイトリストに登録されています。", ephemeral=True)

    @whitelist.command(name="remove", description="ユーザーをホワイトリストから削除します (管理者のみ)。")
    async def whitelist_remove(self, ctx: discord.ApplicationContext, user: discord.User):
        if not await self._is_admin(ctx.author.id):
            await ctx.respond("このコマンドを実行する権限がありません。", ephemeral=True)
            return

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('DELETE FROM whitelist WHERE user_id = ?', (user.id,))
            await db.commit()
            if cursor.rowcount > 0:
                await ctx.respond(f"ユーザー `{user.name}` をホワイトリストから削除しました。")
            else:
                await ctx.respond(f"ユーザー `{user.name}` はホワイトリストに登録されていません。", ephemeral=True)

    @whitelist.command(name="list", description="ホワイトリストに登録されているユーザーを表示します (管理者のみ)。")
    async def whitelist_list(self, ctx: discord.ApplicationContext):
        if not await self._is_admin(ctx.author.id):
            await ctx.respond("このコマンドを実行する権限がありません。", ephemeral=True)
            return

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('SELECT user_id FROM whitelist')
            user_ids = [row[0] for row in await cursor.fetchall()]

        if not user_ids:
            await ctx.respond("ホワイトリストにユーザーは登録されていません。", ephemeral=True)
            return

        users = []
        for user_id in user_ids:
            try:
                user = await self.bot.fetch_user(user_id)
                users.append(user.name)
            except discord.NotFound:
                users.append(f"不明なユーザー (ID: {user_id})")

        embed = discord.Embed(title="ホワイトリストユーザー", description="\n".join(users), color=discord.Color.blue())
        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(WhitelistCog(bot))

