#!/bin/env python
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

intents = discord.Intents.all()
intents.members = True

bot = commands.Bot(intents=intents,command_prefix='!')


@bot.event
async def on_ready():
    # debug, info, warning, error, critical
    logger.info("Booting...")
    logger.info("Boot complete.")


@bot.event
async def on_message(incoming_message):
    if incoming_message.author == bot.user:
        return

    #if incoming_message.channel.id == 542608448127369216 and bot.user in incoming_message.mentions:
    if bot.user in incoming_message.mentions:
        guild = discord.utils.get(bot.guilds, id=98468906720579584)
        channel = discord.utils.get(guild.channels, id=542608448127369216)
		
        #history_messages = []
        #async for message in channel.history(limit=100):
        #    history_messages.append(message)

        history_messages = []
        async for history_message in channel.history(limit=20):
            history_messages.append(history_message)

        chat_history = []
        for history_message in history_messages:
            if history_message.author == bot.user:
                chat_history.append(f" answer: {history_message.content}\n")
            else:
                chat_history.append(f"question from {history_message.author.name}: {history_message.content}\n")

        chat_history.reverse()
        long_string = '\n'.join(chat_history)

        HOST = 'localhost:5000'
        URI = f'http://{HOST}/api/v1/generate'

        logger.info(f"{incoming_message.author.name}: {incoming_message.content}")
        prompt = f"Question: {incoming_message.content}\n\n### Response:\n"

        request = {
            'prompt': long_string,
            'max_new_tokens': 200,
            'do_sample': True,
            'temperature': 0.7,
            'top_p': 0.5,
            'typical_p': 1,
            'repetition_penalty': 1.2,
            'top_k': 40,
            'min_length': 0,
            'no_repeat_ngram_size': 0,
            'num_beams': 1,
            'penalty_alpha': 0,
            'length_penalty': 1,
            'early_stopping': False,
            'seed': -1,
            'add_bos_token': True,
            'truncation_length': 2048,
            'ban_eos_token': False,
            'skip_special_tokens': True,
            'stopping_strings': []
        }

        logger.info("Sending message to gpt4")
        logger.info(json.dumps(request))
        response = requests.post(URI, json=request)
        if response.status_code == 200:
            message = response.json()['results'][0]['text']
            logger.info(message)
            await incoming_message.channel.send(message)
    

bot.run(client_secret)
