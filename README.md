# Bot_notifier 📢
a repo for making a bot in discord to take the topics from a website and send it in a discord server 
# instructions for making bot
1- go to https://discord.com/developers/applications

2- Click “New Application”, name it, and click Create.

3- Go to the “Bot” tab

4- Click “Add Bot” 

5- Confirm and choose bot and choose public bot and in privilged gateway intents choose Message Content intent

6- Under Token, click “Copy” or "reset" and then copy it but you’ll use this in your code). ⚠️ Keep this secret! as with token your bot can be controlled 

7- Go to OAuth2 > URL Generator

8- Under Scopes, check bot

9- Under Bot Permissions, select permissions

10- then take the generated url and open it and add the bot to your server you must be the owner of the server you can check it by find a crown beside your name.

# write the code 
first install the discord and beautiful soup for python 
by writing this command in the bash

`pip install discord.py requests beautiflsoup4`

then make a folder and give it a name 
and inside it make 

main.py (inside it pyhton code)

log.txt (inside it the log results)

sent_topics.json (put inside it topics and save it)

and then you put the Token in your code in main.py 
and get the ID of the channel you use in code by

Go to discord 

Go down to your name and go to settings

choose advanced 

choose developer mode 

and then right click on the channel and choose channel ID and copy it 

then add it to your code in the CATEGORY_CHANNELS dictionary.


# to run the bot 
open discord server

in the bash if your ide run 

`python main.py`

or in the cmd or bash 

`cd to the folder you made`

`python main.py`

note that main.py is the file name and can change if you change it 

if you want to delete the messages in a channel just write 

`!clearall`

 see the topics sent from the website to server 

# Resources 
for more information see the discord documentation 







