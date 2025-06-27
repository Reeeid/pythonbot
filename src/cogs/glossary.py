

import discord
from discord.ext import commands, pages
import aiosqlite
import os

class GlossaryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'glossary.db')
        self.admin_id = int(os.getenv('ADMIN_ID'))
        self.bot.loop.create_task(self._async_setup_db()) # 非同期でDBセットアップを呼び出す

    async def _async_setup_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            # 用語テーブル
            await db.execute('''
                CREATE TABLE IF NOT EXISTS terms (
                    name TEXT PRIMARY KEY,
                    description TEXT
                )
            ''')
            # ホワイトリストテーブル (GlossaryCogでも参照するため残す)
            await db.execute('''
                CREATE TABLE IF NOT EXISTS whitelist (
                    user_id INTEGER PRIMARY KEY
                )
            ''')
            await db.commit()

    async def _is_admin(self, user_id):
        return user_id == self.admin_id

    async def _is_whitelisted(self, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('SELECT 1 FROM whitelist WHERE user_id = ?', (user_id,))
            result = await cursor.fetchone()
            return result is not None

    # /docadd コマンド
    @commands.slash_command(name="docadd", description="用語を登録します (ホワイトリストユーザーのみ)。")
    async def docadd(self, ctx: discord.ApplicationContext, name: str, description: str):
        if not await self._is_whitelisted(ctx.author.id) and not await self._is_admin(ctx.author.id):
            await ctx.respond("このコマンドを実行する権限がありません。", ephemeral=True)
            return

        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute('INSERT INTO terms (name, description) VALUES (?, ?)', (name, description))
                await db.commit()
                await ctx.respond(f"用語 `{name}` を登録しました。")
            except aiosqlite.IntegrityError:
                await ctx.respond(f"用語 `{name}` は既に登録されています。", ephemeral=True)

    # /docremove コマンド
    @commands.slash_command(name="docremove", description="用語を削除します (ホワイトリストユーザーのみ)。")
    async def docremove(self, ctx: discord.ApplicationContext, name: str):
        if not await self._is_whitelisted(ctx.author.id) and not await self._is_admin(ctx.author.id):
            await ctx.respond("このコマンドを実行する権限がありません。", ephemeral=True)
            return

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('DELETE FROM terms WHERE name = ?', (name,))
            await db.commit()
            if cursor.rowcount > 0:
                await ctx.respond(f"用語 `{name}` を削除しました。")
            else:
                await ctx.respond(f"用語 `{name}` は見つかりませんでした。", ephemeral=True)

    # /doclist コマンド
    @commands.slash_command(name="doclist", description="登録されている用語の一覧を表示します。")
    async def doclist(self, ctx: discord.ApplicationContext):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('SELECT name FROM terms ORDER BY name')
            terms = [row[0] for row in await cursor.fetchall()]

        if not terms:
            await ctx.respond("まだ用語は登録されていません。", ephemeral=True)
            return

        # ページネーション
        chunked_terms = [terms[i:i + 10] for i in range(0, len(terms), 10)] # 1ページ10件
        embeds = []
        for i, chunk in enumerate(chunked_terms):
            embed = discord.Embed(title=f"登録用語リスト ({i+1}/{len(chunked_terms)})", color=discord.Color.purple())
            embed.description = "\n".join([f"- {term}" for term in chunk])
            embeds.append(embed)

        paginator = pages.Paginator(pages=embeds)
        await paginator.respond(ctx.interaction, ephemeral=False)

    # /doc コマンド
    @commands.slash_command(name="doc", description="指定した用語の説明を表示します。")
    async def doc(self, ctx: discord.ApplicationContext, name: str):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('SELECT description FROM terms WHERE name = ?', (name,))
            result = await cursor.fetchone()

        if result:
            embed = discord.Embed(title=f"用語: {name}", description=result[0], color=discord.Color.blue())
            await ctx.respond(embed=embed)
        else:
            await ctx.respond(f"用語 `{name}` は見つかりませんでした。", ephemeral=True)

def setup(bot):
    bot.add_cog(GlossaryCog(bot))
