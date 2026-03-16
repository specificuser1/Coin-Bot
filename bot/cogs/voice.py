import discord
from discord.ext import commands
import asyncio
from datetime import datetime

class Voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_states = {}
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return
        
        # Check if deafened/afk
        if after.deaf or after.afk or after.self_deaf or after.mute or after.self_mute:
            user_data = self.bot.db.get_user_coins(member.id)
            if user_data.get('in_vc_since'):
                # Stop earning if deafened
                user_data['in_vc_since'] = None
                self.bot.db.update_user_coins(member.id, user_data['coins'])

async def setup(bot):
    await bot.add_cog(Voice(bot))
