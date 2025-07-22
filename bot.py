#========  Legal & Privacy Disclaimer ========
#- This script only accesses publicly available content from:
#    https://erc2025.husarion.com/
#- No login, user accounts, or personal data are collected or stored.
#- All data scraped is from pages visible without authentication.
#- This tool respects site bandwidth by limiting requests (1 per 60 sec).
#- This bot is intended for **educational and non-commercial use** only.
#- If you are the website owner and want this bot to stop scraping, 
# please contact the bot maintainer or block it via `robots.txt`.

import discord
import asyncio
import requests
from bs4 import BeautifulSoup
import json
import os
import logging

# === Configuration ===
TOKEN ="put here token"  # Replace with your real token

CATEGORY_CHANNELS = {
"channel name" : "channel id"
}

FORUM_URL = "website" 
CHECK_INTERVAL = 60  # check every 60 sec for new topics
SENT_TOPICS_FILE = "sent_topics.json"  # file to track sent topics

intents = discord.Intents.default()
intents.message_content = True  # required to read user messages
intents.messages = True # manage message
intents.guilds = True 
client = discord.Client(intents=intents) # make a bot client object
stop_in_welcome =  False



logging.basicConfig(level=logging.INFO, filename="log.txt", filemode="a")


# === Load sent topics ===
if os.path.exists(SENT_TOPICS_FILE):  # check if the url exist
    with open(SENT_TOPICS_FILE, "r") as f: # open the json
        sent_topics = set(json.load(f))
else:
    sent_topics = set()

def save_sent_topics(): # put topics not in json file 
    with open(SENT_TOPICS_FILE, "w") as f: # write in json
        json.dump(list(sent_topics), f)

# === Cache all categories from forum ===
def get_all_categories():
    try:
        res = requests.get(FORUM_URL + "categories.json")
        if res.status_code == 200: # menas ok 
            data = res.json() # make  a dictinoary 
            return {
                str(cat["id"]): cat["name"]
                for cat in data["category_list"]["categories"]
            }
    except Exception as e:  #handle error
        print(f"Error fetching categories: {e}")
    return {}

CATEGORY_MAP = get_all_categories()

# === Fetch full topic info from topic ID ===
def get_topic_info_from_json(topic_id):
    try:
        url = f"{FORUM_URL}t/{topic_id}.json"
        res = requests.get(url)  
        if res.status_code == 200: # OK
            data = res.json()
            title = data.get("title", "No Title")
            slug = data.get("category_slug")
            cat_id = str(data.get("category_id", "0"))
            if slug:
                category_name = slug.replace('-', ' ').title()
            else:
                category_name = CATEGORY_MAP.get(cat_id, "Uncategorized")
            return title, category_name
    except Exception as e:
        print(f" Error fetching topic info for ID {topic_id}: {e}")
    return None, "Uncategorized"

# === Background task: Check forum for new topics ===
async def check_forum():
    await client.wait_until_ready() # wait to bot is online
    print("Bot started. Checking forum...")

    while not client.is_closed():
        try:
            response = requests.get(FORUM_URL)
            soup = BeautifulSoup(response.text, "html.parser")
            topic_links = soup.find_all("a", class_="title raw-link raw-topic-link")
            print(f"Found {len(topic_links)} topics.")

            for a_tag in topic_links:
                href = a_tag.get("href", "")
                if href.startswith("http"):
                    full_link = href
                else:
                    full_link = FORUM_URL.rstrip("/") + href

                if full_link in sent_topics:
                    continue

                topic_id = href.strip("/").split("/")[-1]
                title, category_name = get_topic_info_from_json(topic_id)

                print(f"Topic: {title} | Category: {category_name}")

                channel_id = CATEGORY_CHANNELS.get(category_name)
                if channel_id:
                    channel = client.get_channel(channel_id)
                    if channel:
                        await channel.send(f" **{title}**\n {full_link}")
                        print(f"Sent: {title}")
                        sent_topics.add(full_link)
                        save_sent_topics()
                    else:
                        print(f"Channel with ID {channel_id} not found")
                else:
                    print(f"No Discord channel set for category: '{category_name}'")

        except Exception as e:
            print(f"Error checking forum: {e}")

        await asyncio.sleep(CHECK_INTERVAL)

# === On bot ready ===
@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    client.loop.create_task(check_forum())

# === On user message ===
@client.event # event 
async def on_message(message):
    if message.author.bot: # check author is not bot
        return

    # Admin-only: clear all messages
    if message.content.startswith("!clearall"):
        if not message.author.guild_permissions.administrator:
            await message.channel.send("You need to be an admin to do this.")
            return

        await message.channel.send("Deleting messages...")

        def not_bot(m):
            return True

        try:
            deleted = await message.channel.purge(limit=1000, check=not_bot)
            await message.channel.send(f"Deleted {len(deleted)} messages.", delete_after=5)
        except discord.Forbidden:
            await message.channel.send("I don't have permission to delete messages.")
        return  # exit after clear command

    
    global stop_in_welcome 
 
    if message.channel.name == "welcome-channel":
        if message.content.strip().lower() == "!stop":
            stop_in_welcome = True
            await message.channel.send("Search disabled in welcome channel.")
            return

        if message.content.strip().lower() == "!resume":
            stop_in_welcome = False
            await message.channel.send("Search enabled in welcome channel.")
            return

        if stop_in_welcome:
            return  # Don’t do anything if stopped   
    # === SEARCH feature ===
    search_word = message.content.strip().lower()

    try:
        with open("sent_topics.json", "r") as f:
            topics = json.load(f)

        # if saved as list of URLs
        if isinstance(topics, list):
            matches = [url for url in topics if search_word in url.lower()]
        else:
            matches = []
        
        if matches :
             for match in matches:
                 await message.channel.send(match)
        else:
             await message.channel.send("No results found.")
    except Exception as e:
        await message.channel.send("Error reading topic data.")
        print(f"Search error: {e}")


@client.event
async def on_member_join(member):
    await client.wait_until_ready()
    guild = member.guild
    welcome_channel = discord.utils.get(guild.text_channels, name="welcome-channel")

    if welcome_channel:
        await welcome_channel.send(f"Hello {member.mention}, welcome to the server!")
        await mention_mentors()
    else:
        print("Welcome channel not found.")

# === Auto mention mentors in welcome channel ===
async def mention_mentors():
    await client.wait_until_ready()
    guild = discord.utils.get(client.guilds)
    welcome_channel = discord.utils.get(guild.text_channels, name="welcome-channel")
    mentor_role = discord.utils.get(guild.roles, name="Mentor")

    if not welcome_channel or not mentor_role:
        print("Welcome channel or 'Mentor' role not found.")
        return

    mentions = [member.mention for member in mentor_role.members]

    if mentions:
        mention_text = " ".join(mentions)
        await welcome_channel.send(f"{mention_text} A new member has joined. Please welcome them! 🎉")
    else:
        await welcome_channel.send("No mentors found to mention.")

client.run(TOKEN)
