import discord
from discord.ext import commands
import aiosqlite
import os

class UserSpellSetsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'spells.db')
        self.bot.loop.create_task(self._async_setup_db())

    async def _async_setup_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_spell_sets (
                    user_id INTEGER NOT NULL,
                    spell_id INTEGER NOT NULL,
                    PRIMARY KEY (user_id, spell_id),
                    FOREIGN KEY (spell_id) REFERENCES spells(ID) ON DELETE CASCADE
                )
            ''')
            await db.commit()

    async def get_spell_by_query(self, query: str):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            # 最初にIDで検索を試みる
            if query.isdigit():
                cursor = await db.execute('SELECT * FROM spells WHERE ID = ?', (int(query),))
                spell = await cursor.fetchone()
                if spell: return spell
            # IDで見つからなければ名前で検索
            cursor = await db.execute('SELECT * FROM spells WHERE name LIKE ?', (f'%{query}%',))
            spell = await cursor.fetchone()
            return spell

    async def add_spell_to_user_set(self, user_id: int, spell_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute('INSERT INTO user_spell_sets (user_id, spell_id) VALUES (?, ?)', (user_id, spell_id,))
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                return False # 既に存在する場合

    async def remove_spell_from_user_set(self, user_id: int, spell_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('DELETE FROM user_spell_sets WHERE user_id = ? AND spell_id = ?', (user_id, spell_id,))
            await db.commit()
            return cursor.rowcount > 0

    async def reset_user_spell_set(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('DELETE FROM user_spell_sets WHERE user_id = ?', (user_id,))
            await db.commit()
            return cursor.rowcount > 0

    async def get_user_spell_set_spells(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT s.* FROM spells s
                JOIN user_spell_sets uss ON s.ID = uss.spell_id
                WHERE uss.user_id = ?
                ORDER BY s.level, s.name
            ''', (user_id,))
            spells = await cursor.fetchall()
            return spells

    @commands.slash_command(name="setspell", description="あなたの呪文セットに呪文を追加します。")
    async def setspell(self, ctx: discord.ApplicationContext, query: str):
        spell = await self.get_spell_by_query(query)
        if not spell:
            await ctx.respond(f"'{query}' に一致する呪文は見つかりませんでした。", ephemeral=True)
            return

        if await self.add_spell_to_user_set(ctx.author.id, spell['ID']):
            await ctx.respond(f"呪文 '{spell['name']}' をあなたの呪文セットに追加しました。", ephemeral=True)
        else:
            await ctx.respond(f"呪文 '{spell['name']}' は既にあなたの呪文セットに登録されています。", ephemeral=True)

    @commands.slash_command(name="unsetspell", description="あなたの呪文セットから呪文を削除します。")
    async def unsetspell(self, ctx: discord.ApplicationContext, query: str):
        spell = await self.get_spell_by_query(query)
        if not spell:
            await ctx.respond(f"'{query}' に一致する呪文は見つかりませんでした。", ephemeral=True)
            return

        if await self.remove_spell_from_user_set(ctx.author.id, spell['ID']):
            await ctx.respond(f"呪文 '{spell['name']}' をあなたの呪文セットから削除しました。", ephemeral=True)
        else:
            await ctx.respond(f"呪文 '{spell['name']}' はあなたの呪文セットに登録されていません。", ephemeral=True)

    @commands.slash_command(name="resetspellset", description="あなたの呪文セットをリセットします。")
    async def resetspellset(self, ctx: discord.ApplicationContext):
        if await self.reset_user_spell_set(ctx.author.id):
            await ctx.respond("あなたの呪文セットをリセットしました。", ephemeral=True)
        else:
            await ctx.respond("あなたの呪文セットは既に空です。", ephemeral=True)

    @commands.slash_command(name="displayspellset", description="あなたの呪文セットを表示します。")
    async def displayspellset(self, ctx: discord.ApplicationContext):
        spells = await self.get_user_spell_set_spells(ctx.author.id)
        if not spells:
            await ctx.author.send("あなたの呪文セットは空です。")
            await ctx.respond("あなたの呪文セットは空です。DMを確認してください。", ephemeral=True)
            return

        embed = discord.Embed(title=f"{ctx.author.display_name} の呪文セット", color=discord.Color.purple())

        display_fields = {
            'ID': 'ID',
            'name': '名前',
            'level': 'レベル',
            'type': 'タイプ',
            'Stime': '詠唱時間',
            'Range': '射程',
            'target': '対象',
            'TimeC': '持続時間',
            'save': 'セーヴ',
            'Ref': '参照',
            'mov': '構成要素',
            'highlevel': '高レベル化'
        }

        for spell in spells:
            spell_info = []
            for key, display_name in display_fields.items():
                value = spell[key] if spell[key] is not None else "(なし)"
                spell_info.append(f"**{display_name}**: {value}")
            
            description = spell['description'] if spell['description'] is not None else "(説明なし)"
            if len(description) > 200: # 埋め込みフィールドの文字数制限を考慮
                description = description[:197] + "..."

            embed.add_field(
                name=f"***{spell['name']} (ID: {spell['ID']})***",
                value="\n".join(spell_info) + f"\n**説明**: {description}\n--------------------",
                inline=False
            )
        
        # Discordの埋め込みの合計文字数制限 (6000文字) を考慮
        # 必要であれば、ここで複数の埋め込みに分割するロジックを追加することも可能ですが、
        # 今回は「ページングせずに１つの埋め込み表示ににまとめて」という要望なので、
        # 制限を超える場合は途中で切れる可能性があります。
        # ユーザーの呪文セットの呪文数が多い場合は注意が必要です。

        try:
            await ctx.author.send(embed=embed)
            await ctx.respond("あなたの呪文セットをDMに送信しました。", ephemeral=True)
        except discord.Forbidden:
            await ctx.respond("DMを送信できませんでした。プライバシー設定を確認してください。", ephemeral=True)


def setup(bot):
    bot.add_cog(UserSpellSetsCog(bot))
