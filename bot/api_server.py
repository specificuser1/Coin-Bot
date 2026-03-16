from flask import Flask, jsonify
import discord
import asyncio
import os
from threading import Thread
import time

app = Flask(__name__)
bot = None

@app.route('/status')
def status():
    if bot and bot.is_ready():
        return jsonify({
            'online': True,
            'guilds': len(bot.guilds) if bot.guilds else 0,
            'latency': round(bot.latency * 1000) if bot.latency else 0
        })
    return jsonify({'online': False, 'guilds': 0, 'latency': 0})

@app.route('/restart', methods=['POST'])
def restart():
    # Implement restart logic
    return jsonify({'success': True})

@app.route('/stop', methods=['POST'])
def stop():
    # Implement stop logic
    return jsonify({'success': True})

@app.route('/start', methods=['POST'])
def start():
    # Implement start logic
    return jsonify({'success': True})

@app.route('/vc_stats')
def vc_stats():
    if not bot or not bot.is_ready():
        return jsonify({'total_users': 0, 'members': []})
    
    members = []
    total_users = 0
    
    for guild in bot.guilds:
        for vc in guild.voice_channels:
            for member in vc.members:
                if not member.bot:
                    total_users += 1
                    members.append({
                        'guild': guild.name,
                        'channel': vc.name,
                        'name': member.name,
                        'screenshare': member.voice.self_stream if member.voice else False,
                        'earning': True
                    })
    
    return jsonify({'total_users': total_users, 'members': members})

def run_api():
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))

def start_api(discord_bot):
    global bot
    bot = discord_bot
    api_thread = Thread(target=run_api)
    api_thread.daemon = True
    api_thread.start()
