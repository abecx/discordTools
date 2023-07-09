#!/bin/env python
import sqlite3
import re
import logging
import requests
import asyncio
import discord
from discord.ext import commands,tasks
import json
import time
import os
from dotenv import load_dotenv
from aiohttp import ClientOSError
from discord.errors import HTTPException


# enable logging
logger = logging.getLogger('devastator-gpt')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# file logging output
file_handler = logging.FileHandler('logs/devastator-gpt.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# add a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

load_dotenv()
client_secret = os.environ.get('CLIENT_SECRET')
server_id = os.environ.get('SERVER_ID')
channel_id = os.environ.get('CHANNEL_ID')
sqlite_data = os.environ.get('CHAT_HISTOY_DB')


intents = discord.Intents.all()
intents.members = True

bot = commands.Bot(intents=intents,command_prefix='!')

conn = sqlite3.connect(sqlite_data)
cursor = conn.cursor()

def commit():
    conn.commit()

def insert_data(discord_user_id, discord_user_name, discord_user_nick, discord_server_id, discord_channel_id, timestamp, question, answer):
    # Execute an SQL INSERT statement to insert the data into the table
    insert_query = "INSERT INTO chat_history(discord_user_id, discord_user_name, discord_user_nick, discord_server_id, discord_channel_id, timestamp, question, answer) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
    data = (discord_user_id, discord_user_name, discord_user_nick, discord_server_id, discord_channel_id, timestamp, question, answer)
    cursor.execute(insert_query, data)
    commit()

    return

def get_history(discord_server_id, discord_channel_id, discord_user_id):
    #select_query = "SELECT discord_user_name,question,answer from chat_history WHERE discord_server_id = ? AND discord_channel_id = ? AND discord_user_id = ? order by timestamp"
    select_query = "SELECT * FROM (SELECT discord_user_name,question,answer,timestamp from chat_history WHERE discord_server_id = ? AND discord_channel_id = ?  order by timestamp desc limit 5) order by timestamp asc"
    data = (discord_server_id, discord_channel_id)

    #data = (discord_server_id, discord_channel_id, discord_user_id)
    cursor.execute(select_query, data)
    rows = cursor.fetchall()
    history = {'internal': [], 'visible': []}
    for row in rows:
        history["internal"].append([f"{row[0]} asked: {row[1]}", row[2]]) 
        history["visible"].append([f"{row[0]} asked: {row[1]}", row[2]])

    return(history)


@bot.event
async def on_ready():
    # debug, info, warning, error, critical
    logger.info("Booting...")
    logger.info("Boot complete.")


@bot.event
async def on_message(incoming_message):
    logger.debug(f"{incoming_message.author.name}: {incoming_message.content}")
    if incoming_message.author == bot.user:
        return


    #if incoming_message.channel.id == 542608448127369216 and bot.user in incoming_message.mentions:
    if bot.user in incoming_message.mentions:
        discord_user_id = incoming_message.author.id
        discord_user_name = incoming_message.author.name
        discord_user_nick = incoming_message.author.nick
        discord_server_id = incoming_message.guild.id
        discord_channel_id = incoming_message.channel.id
        timestamp = round(time.time())
        question = incoming_message.content

        guild = discord.utils.get(bot.guilds, id=98468906720579584)
        channel = discord.utils.get(guild.channels, id=542608448127369216)

        history = get_history(discord_server_id, discord_channel_id, discord_user_id)


        HOST = 'localhost:5000'
        URI = f'http://{HOST}/api/v1/chat'

        logger.info(f"{incoming_message.author.name}: {incoming_message.content}")
        prompt = f"Question: {incoming_message.content}\n\n### Response:\n"

        request = {
			'user_input': question,
			'max_new_tokens': 250,
			'history': history,
			'mode': 'chat-instruct',
			'character': 'devastator',
			'instruction_template': 'Guanaco non-chat',
			'your_name': incoming_message.author.name,
			'regenerate': False,
			'_continue': False,
			'stop_at_newline': False,
			'chat_prompt_size': 2048,
			'chat_generation_attempts': 3,
			#'chat-instruct_command': 'Continue the chat dialogue below. Your characters name is Devastator. Write a single reply for the character in less than 8000 characters "".\n\n',
			'preset': 'None',
			'do_sample': True,
			'temperature': 0.7,
			'top_p': 0.1,
			'typical_p': 1,
			'epsilon_cutoff': 0,
			'eta_cutoff': 0,
			'tfs': 1,
			'top_a': 0,
			'repetition_penalty': 1.18,
			'top_k': 40,
			'min_length': 0,
			'no_repeat_ngram_size': 0,
			'num_beams': 1,
			'penalty_alpha': 0,
			'length_penalty': 1,
			'early_stopping': False,
			'mirostat_mode': 0,
			'mirostat_tau': 5,
			'mirostat_eta': 0.1,
			'seed': -1,
			'add_bos_token': True,
			'truncation_length': 8192,
			'ban_eos_token': False,
			'skip_special_tokens': True,
			'stopping_strings': []
        }

        logger.info("Sending message to text-generator.")
        logger.info(json.dumps(request))
        response = requests.post(URI, json=request)
        if response.status_code == 200:
            result = response.json()['results'][0]['history']
            answer = result['visible'][-1][1]
            insert_data(discord_user_id, discord_user_name, discord_user_nick, discord_server_id, discord_channel_id, timestamp, question, answer)
            logger.info(answer)
            await incoming_message.channel.send(answer)
    

bot.run(client_secret)
