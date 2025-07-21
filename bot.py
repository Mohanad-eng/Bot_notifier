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
TOKEN = "put token here"  # Replace with your real token

# here category channels from the site and put it to the channel ids in discord

CATEGORY_CHANNELS = {
    "channel name in website" : "channel_id"
}

FORUM_URL = "website here "
CHECK_INTERVAL = 60  # here interval to go to the website and see for new published topics
SENT_TOPICS_FILE = "sent_topics.json" # json file where we put the sent topics so bot dont resend it 

intents = discord.Intents.default()  # tells the bot what to do
intents.message_content = True  # make bot reaad message 
intents.messages = True # make bot delete the message
intents.guilds = True  
client = discord.Client(intents=intents) # create discord bot client 

logging.basicConfig(level=logging.INFO) 

# === Load sent topics ===
# it here checks if the topics in the json and read it 
if os.path.exists(SENT_TOPICS_FILE):
    with open(SENT_TOPICS_FILE, "r") as f:
        sent_topics = set(json.load(f))
else:
    sent_topics = set()

def save_sent_topics():  # write the topics not in the json 
    with open(SENT_TOPICS_FILE, "w") as f:
        json.dump(list(sent_topics), f)

# === Get all categories once and cache them ===
def get_all_categories():
    try:
        res = requests.get(FORUM_URL + "categories.json")
        if res.status_code == 200: # 200 means ok 
            data = res.json() #convert json response to python dictionary
            return {
                str(cat["id"]): cat["name"]
                for cat in data["category_list"]["categories"]
            }
    except Exception as e:
        print(f"Error fetching categories: {e}")
    return {} # empty dictionary 

CATEGORY_MAP = get_all_categories()

def get_topic_info_from_json(topic_id):
    try:
        url = f"{FORUM_URL}t/{topic_id}.json"
        res = requests.get(url) # send a get requst to topic json url 
        if res.status_code == 200: # ok 
            data = res.json() # convert json to python dictionary
            title = data.get("title", "No Title") # get topic title
            slug = data.get("category_slug") # get category slug
            cat_id = str(data.get("category_id", "0")) # get category id as str
            if slug:
                category_name = slug.replace('-', ' ').title()  #convert slug to readable format
            else:
                category_name = CATEGORY_MAP.get(cat_id, "Uncategorized") # no slug try using the ID to get category name from cached map
            return title, category_name
    except Exception as e:
        print(f" Error fetching topic info for ID {topic_id}: {e}")
    return None, "Uncategorized" 

async def check_forum():
    await client.wait_until_ready() # wait to bot to connect 
    print("Bot started. Checking forum...")

    while not client.is_closed(): # infinte until bot is shutdown
        try:
            response = requests.get(FORUM_URL) # get request to website
            soup = BeautifulSoup(response.text, "html.parser") # parse html 

            topic_links = soup.find_all("a", class_="title raw-link raw-topic-link") 
            print(f"Found {len(topic_links)} topics.")

            for a_tag in topic_links:
                href = a_tag.get("href", "")
                if href.startswith("http"):  # Already a full URL
                   full_link = href
                else:  # It's a relative URL
                   full_link = FORUM_URL.rstrip("/") + href


                if full_link in sent_topics:
                    continue

                topic_id = href.strip("/").split("/")[-1] # extract id topic ffrom url
                title, category_name = get_topic_info_from_json(topic_id)

                print(f"Topic: {title} | Category: {category_name}")

                channel_id = CATEGORY_CHANNELS.get(category_name) # look up the channel id discord 
                if channel_id: 
                    channel = client.get_channel(channel_id)
                    if channel:  # channel exists send the toic title and link
                        await channel.send(f" **{title}**\n {full_link}")
                        print(f"Sent: {title}")
                        sent_topics.add(full_link) # add the link to file
                        save_sent_topics() # save the updated sent_topics
                    else:
                        print(f"Channel with ID {channel_id} not found")
                else:
                    print(f"No Discord channel set for category: '{category_name}'")

        except Exception as e:
            print(f"Error checking forum: {e}")

        await asyncio.sleep(CHECK_INTERVAL)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    client.loop.create_task(check_forum())

@client.event
async def on_message(message):
    if message.author.bot:
        return

    # Clear all messages in the current channel (use with caution)
    if message.content.startswith("!clearall"):
        if not message.author.guild_permissions.administrator:
            await message.channel.send("You need to be an admin to do this.")
            return

        await message.channel.send("Deleting messages...")

        def not_bot(m):
            return True  # You can filter if needed

        try:
            deleted = await message.channel.purge(limit=1000, check=not_bot)
            await message.channel.send(f"Deleted {len(deleted)} messages.", delete_after=5)
        except discord.Forbidden:
            await message.channel.send("I don't have permission to delete messages.")


client.run(TOKEN)
