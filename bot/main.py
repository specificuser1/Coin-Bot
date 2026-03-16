import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
import os
import sys
import signal

from config import TOKEN, PREFIX, MIN_ACCOUNT_AGE_DAYS
from database import Database

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)
db = Database()
bot.db = db

# Global bot state
bot.is_active = True
bot.vc_channels = []  # List of VC IDs that earn coins

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guilds')
    bot.loop.create_task(voice_monitor())
    await bot.change_presence(activity=discord.Game(name=f"{PREFIX}help | {len(bot.guilds)} servers"))

async def voice_monitor():
    await bot.wait_until_ready()
    
    while not bot.is_closed():
        if bot.is_active:
            for guild in bot.guilds:
                for vc in guild.voice_channels:
                    if vc.id in bot.vc_channels or not bot.vc_channels:
                        for member in vc.members:
                            if not member.bot:
                                # Check account age
                                account_age = (datetime.now() - member.created_at).days
                                if account_age >= MIN_ACCOUNT_AGE_DAYS:
                                    # Calculate coins
                                    coins_to_add = 1.0  # Base rate
                                    
                                    # Check if sharing screen
                                    for member_vc in guild.voice_channels:
                                        if member in member_vc.members:
                                            if member.voice and member.voice.self_stream:
                                                coins_to_add = 1.5
                                                break
                                    
                                    db.add_coins(member.id, coins_to_add)
                                else:
                                    # Blacklist new accounts
                                    if not db.get_user_coins(member.id).get('blacklisted', False):
                                        user_data = db.get_user_coins(member.id)
                                        user_data['blacklisted'] = True
                                        db.update_user_coins(member.id, user_data['coins'], 
                                                           blacklisted=True)
                                        
                                        try:
                                            await member.send("❌ Your account is too new. You have been blacklisted from earning coins.")
                                        except:
                                            pass
        await asyncio.sleep(60)  # Check every minute

@bot.command(name='coins')
async def check_coins(ctx):
    """Check your coins"""
    user_data = bot.db.get_user_coins(ctx.author.id)
    
    if user_data.get('blacklisted', False):
        embed = discord.Embed(
            title="⛔ Blacklisted",
            description="You are blacklisted from the coin system.",
            color=0xFF0000
        )
        embed.set_footer(text="Programmed by SUBHAN")
        await ctx.send(embed=embed)
        return
    
    embed = discord.Embed(
        title="💰 Coin System",
        description=f"**Your Balance:** {user_data['coins']:.2f} coins",
        color=0x00FF00
    )
    
    # Add rules
    rules = (
        "📋 **Rules:**\n"
        f"• {MIN_ACCOUNT_AGE_DAYS}+ days account required\n"
        "• 1 coin per minute in VC\n"
        "• 1.5 coins per minute with screenshare\n"
        "• No coins if AFK/deafened\n"
        f"• Redeem keys for {KEY_COST} coins (max {DAILY_KEY_LIMIT}/day)"
    )
    embed.add_field(name="📜 Server Rules", value=rules, inline=False)
    
    # Key stock
    with open('keys/unused_keys.txt', 'r') as f:
        keys_available = len(f.read().splitlines())
    
    embed.add_field(name="🔑 Keys Available", value=str(keys_available), inline=True)
    
    embed.set_footer(text="Programmed by SUBHAN")
    
    # Create buttons
    class CoinView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
        
        @discord.ui.button(label="Check Coins", style=discord.ButtonStyle.green)
        async def check_coins(self, interaction: discord.Interaction, button: discord.ui.Button):
            user_data = bot.db.get_user_coins(interaction.user.id)
            await interaction.response.send_message(
                f"💰 You have {user_data['coins']:.2f} coins", 
                ephemeral=True
            )
        
        @discord.ui.button(label="Redeem Key", style=discord.ButtonStyle.blurple)
        async def redeem_key(self, interaction: discord.Interaction, button: discord.ui.Button):
            user_data = bot.db.get_user_coins(interaction.user.id)
            
            if user_data.get('blacklisted', False):
                await interaction.response.send_message("❌ You are blacklisted!", ephemeral=True)
                return
            
            if user_data['daily_keys'] >= DAILY_KEY_LIMIT:
                await interaction.response.send_message(
                    f"❌ Daily key limit reached ({DAILY_KEY_LIMIT}/day)", 
                    ephemeral=True
                )
                return
            
            if user_data['coins'] < KEY_COST:
                await interaction.response.send_message(
                    f"❌ Insufficient coins! Need {KEY_COST} coins", 
                    ephemeral=True
                )
                return
            
            key = bot.db.get_key()
            if key:
                bot.db.remove_coins(interaction.user.id, KEY_COST)
                user_data['daily_keys'] += 1
                bot.db.update_user_coins(
                    interaction.user.id, 
                    user_data['coins'] - KEY_COST,
                    daily_keys=user_data['daily_keys']
                )
                
                # DM the key
                try:
                    await interaction.user.send(f"🔑 Your key: `{key}`")
                    await interaction.response.send_message("✅ Key sent to DMs!", ephemeral=True)
                except:
                    await interaction.response.send_message(
                        f"❌ Could not DM you. Your key: `{key}`", 
                        ephemeral=True
                    )
            else:
                await interaction.response.send_message("❌ No keys available!", ephemeral=True)
    
    await ctx.send(embed=embed, view=CoinView())

@bot.command(name='redeem')
@commands.has_permissions(administrator=True)
async def add_keys(ctx, *, keys):
    """Add keys (Admin only)"""
    key_list = keys.split('\n')
    for key in key_list:
        if key.strip():
            bot.db.add_key(key.strip())
    
    await ctx.send(f"✅ Added {len(key_list)} keys!")

@bot.command(name='blacklist')
@commands.has_permissions(administrator=True)
async def blacklist_user(ctx, user: discord.User):
    """Blacklist a user (Admin only)"""
    user_data = bot.db.get_user_coins(user.id)
    user_data['blacklisted'] = True
    bot.db.update_user_coins(user.id, user_data['coins'], blacklisted=True)
    
    try:
        await user.send("⛔ You have been blacklisted from the coin system.")
    except:
        pass
    
    await ctx.send(f"✅ Blacklisted {user.name}")

@bot.command(name='unblacklist')
@commands.has_permissions(administrator=True)
async def unblacklist_user(ctx, user: discord.User):
    """Unblacklist a user (Admin only)"""
    user_data = bot.db.get_user_coins(user.id)
    user_data['blacklisted'] = False
    bot.db.update_user_coins(user.id, user_data['coins'], blacklisted=False)
    
    try:
        await user.send("✅ You have been unblacklisted from the coin system.")
    except:
        pass
    
    await ctx.send(f"✅ Unblacklisted {user.name}")

@bot.command(name='addvc')
@commands.has_permissions(administrator=True)
async def add_earning_vc(ctx, vc: discord.VoiceChannel):
    """Add VC to earning channels (Admin only)"""
    if vc.id not in bot.vc_channels:
        bot.vc_channels.append(vc.id)
        await ctx.send(f"✅ Added {vc.name} to earning channels")
    else:
        await ctx.send(f"❌ {vc.name} is already an earning channel")

@bot.command(name='removevc')
@commands.has_permissions(administrator=True)
async def remove_earning_vc(ctx, vc: discord.VoiceChannel):
    """Remove VC from earning channels (Admin only)"""
    if vc.id in bot.vc_channels:
        bot.vc_channels.remove(vc.id)
        await ctx.send(f"✅ Removed {vc.name} from earning channels")
    else:
        await ctx.send(f"❌ {vc.name} is not an earning channel")

@bot.command(name='listvc')
@commands.has_permissions(administrator=True)
async def list_earning_vc(ctx):
    """List earning channels (Admin only)"""
    if bot.vc_channels:
        channels = []
        for vc_id in bot.vc_channels:
            vc = bot.get_channel(vc_id)
            if vc:
                channels.append(f"• {vc.name}")
        
        if channels:
            await ctx.send("**Earning Channels:**\n" + "\n".join(channels))
        else:
            await ctx.send("No earning channels set (all channels earn)")
    else:
        await ctx.send("All voice channels are earning channels")

@bot.command(name='resetdaily')
@commands.has_permissions(administrator=True)
async def reset_daily_keys(ctx):
    """Reset daily key limits (Admin only)"""
    bot.db.reset_daily_keys()
    await ctx.send("✅ Daily key limits reset!")

# Load cogs
async def load_extensions():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

if __name__ == '__main__':
    asyncio.run(load_extensions())
    bot.run(TOKEN)
