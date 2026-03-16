import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
import os
import sys
import signal

from config import TOKEN, PREFIX, MIN_ACCOUNT_AGE_DAYS
from database import Database
from api_server import start_api

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
    
    # Start API server
    start_api(bot)
    print(f'API server started on port {os.getenv("PORT", 5000)}')

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
                                    if member.voice and member.voice.self_stream:
                                        coins_to_add = 1.5
                                    
                                    db.add_coins(member.id, coins_to_add)
                                else:
                                    # Blacklist new accounts
                                    user_data = db.get_user_coins(member.id)
                                    if not user_data.get('blacklisted', False):
                                        db.update_user_coins(
                                            member.id, 
                                            user_data['coins'], 
                                            blacklisted=True
                                        )
                                        
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
    
    # Get key count
    with open('keys/unused_keys.txt', 'r') as f:
        keys_available = len(f.read().splitlines())
    
    embed = discord.Embed(
        title="💰 Coin System",
        description=f"**Your Balance:** {user_data['coins']:.2f} coins\n\n**Keys Available:** {keys_available}",
        color=0x00FF00
    )
    
    # Add rules
    rules = (
        "📋 **Rules:**\n"
        f"• {MIN_ACCOUNT_AGE_DAYS}+ days account required\n"
        "• 1 coin per minute in VC\n"
        "• 1.5 coins per minute with screenshare\n"
        "• No coins if AFK/deafened\n"
        f"• Redeem keys for {90} coins (max {2}/day)"
    )
    embed.add_field(name="📜 Server Rules", value=rules, inline=False)
    
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
            
            if user_data['daily_keys'] >= 2:
                await interaction.response.send_message(
                    f"❌ Daily key limit reached (2/day)", 
                    ephemeral=True
                )
                return
            
            if user_data['coins'] < 90:
                await interaction.response.send_message(
                    f"❌ Insufficient coins! Need 90 coins", 
                    ephemeral=True
                )
                return
            
            key = bot.db.get_key()
            if key:
                bot.db.remove_coins(interaction.user.id, 90)
                user_data['daily_keys'] += 1
                bot.db.update_user_coins(
                    interaction.user.id, 
                    user_data['coins'] - 90,
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

# Admin commands
@bot.command(name='addkey')
@commands.has_permissions(administrator=True)
async def add_key(ctx, *, key):
    """Add a key (Admin only)"""
    bot.db.add_key(key)
    await ctx.send(f"✅ Key added successfully!")

@bot.command(name='addkeys')
@commands.has_permissions(administrator=True)
async def add_keys(ctx, *, keys):
    """Add multiple keys (Admin only)"""
    key_list = keys.split('\n')
    count = 0
    for key in key_list:
        if key.strip():
            bot.db.add_key(key.strip())
            count += 1
    
    await ctx.send(f"✅ Added {count} keys!")

@bot.command(name='blacklist')
@commands.has_permissions(administrator=True)
async def blacklist_user(ctx, user: discord.User):
    """Blacklist a user (Admin only)"""
    user_data = bot.db.get_user_coins(user.id)
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

@bot.command(name='resetdaily')
@commands.has_permissions(administrator=True)
async def reset_daily_keys(ctx):
    """Reset daily key limits (Admin only)"""
    bot.db.reset_daily_keys()
    await ctx.send("✅ Daily key limits reset!")

if __name__ == '__main__':
    bot.run(TOKEN)
