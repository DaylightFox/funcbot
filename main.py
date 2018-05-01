import discord
import asyncio
from PIL import Image
import math
import logging
import pymysql
import urllib.request
from hashlib import md5
import numpy
from io import BytesIO
from sys import getsizeof
import datetime

import modules.encryption as encryption
from modules.database import Database
from modules.steganography import steganography

# Database(username, password, host, database)
global db
db = Database("username", "password", "host", "table")
client = discord.Client()
logging.basicConfig(level=logging.INFO)

# When connected to the API
@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

# When the bot joins a server
@client.event
async def on_server_join(server):
    if db.serverExists(server) == False:
        db.addServer(server)

# When the bot is removed from a server
@client.event
async def on_server_remove(server):
    if db.serverExists(server):
        db.removeServer(server)

# When a user updates their profile
@client.event
async def on_member_update(before, after):
    if db.userExists(before):
        db.updateUser(after)

# Check URLs for all servers
async def Watcher():
    await client.wait_until_ready()
    while not client.is_closed:
        print("Running background task: Watcher()")
        # Get all the URLs to be checked
        urls = db.getAllWatchURLs()
        for i in urls:
            wid = i['wid']
            url = i['url']
            content = i['content']
            """
            Use a custom request so headers can be changed, allowing
            the bot to move more freely.
            """
            req = urllib.request.Request(url, 
                                        data=None, 
                                        headers={
                                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
                                        }
                                    )
            site = urllib.request.urlopen(req).read().decode('utf-8')
            if site != content:
                # Get an array of all servers who watch this URL
                servers = db.whoWatches(wid)
                for s in servers:
                    found = False
                    for server in client.servers:
                        # Compare to get the server object
                        if s['sid'] == str(server.id):
                            for channel in server.channels:
                                """
                                I use the time to identify channels due ot the
                                fact that channel objects can not be
                                instantiated by the user.
                                """
                                time = channel.created_at
                                if str(time) == s['channel'] and str(channel.type) == "text":
                                    await client.send_message(channel,
                                    """\u200BThe url {} has been updated!"""
                                    .format(url))
                                    """
                                    Update the content field with the new
                                    content so the bot doesn't make false
                                    statements.
                                    """
                                    db.updateWatching(wid, site)
                                    found = True
                                    break
                    if found == False:
                        """
                        Remove the record for that server as there is no
                        channel to send to
                        """
                        db.removeWatching(s['sid'], url)
        # Wait 10 minutes                
        await asyncio.sleep(600)

# when someone sends a message on a server
#   that the bot is on
@client.event
async def on_message(message):
    # Do not respond to other bots
    if message.author.bot:
        return None
        
    # Get start of the time taken to evaluate message    
    start_time = datetime.datetime.now()
    
    # Get the prefix for the server
    pre = db.getPrefix(message.server)
    
    # Check to see if this server has a limit, and if so: adhere to it
    lim = db.getLimit(message.server)
    if lim is not None:
        if message.channel.name != lim:
            return None
        
    
    # ----------------
    # General Commands
    # ----------------

    # Help Command
    if message.content.startswith('{}help'.format(pre)):
        help_message = """```========== Funcbot Help ==========
f.help        Displays this message
f.rot         Use the rot cipher
f.vigenere    Use the vigenere cipher```"""
        if len(message.content.split()) > 1 and \
                message.content.split()[1].lower() == "-me":
            # DM the full help dialogue to the user.
            await client.send_message(message.author, help_message)
        else:
            await client.send_message(message.channel, "For a full \
list of commands, see the Github repo \
(https://github.com/DaylightFox/funcbot) \
or type `{}help -me`".format(pre))
    elif message.content.startswith('{}source'.format(pre)):
        await client.send_message(message.channel, "Source: \
https://github.com/DaylightFox/funcbot")

    # --------------
    # Admin Commands
    # --------------

    # Clear Command (Restricted to users with Manage Messages permission)
    elif message.content.startswith('{}clear'.format(pre)):
        # Check users has sufficient permissions
        if message.channel.permissions_for(message.author).manage_messages:
            msgs = []
            # Build a list of messages to delete
            async for i in \
                    client.logs_from(message.channel,
                                     limit=int(message.content.split()[1])):
                msgs.append(i)
            # Delete selected messages
            await client.delete_messages(msgs)
            # Send ACK
            await client.send_message(
                message.channel,
                "\u200BDeleted {} messages".format(message.content.split()[1]))
        else:
            await client.send_message(
                message.channel,
                """\u200BInsufficient permissions. You must have the Manage
                Messages permission to do this.""")

    # Limit Command (Restricted to users with Manage Server permission)
    elif message.content.startswith('{}limit'.format(pre)):
        # Check user has sufficient permissions
        if message.channel.permissions_for(message.author).manage_server:
            # Check to see if they want to remove the limit
            if message.content.split()[1].lower() == "-reset":
                db.setLimit(message.server, None)
                await client.send_message(message.channel,
                        "Successfully removed command limit")
            else:
                # Get channel to limit to
                channel = message.channel_mentions
                # Make sure they have only mentioned one channel
                if len(channel) > 1:
                    return
                    # Too many channels mentioned
                else:
                    # Set the limit to the desired channel
                    db.setLimit(message.server, channel[0])
                    # Send ACK
                    await client.send_message(message.channel,
                        "Successfully set the command limit to {}"
                        .format(message.content.split()[1]))
        else:
            await client.send_message(
                message.channel,
                """\u200BInsufficient permissions. You must have the Manage
                Server permission to do this.""")

    # Set Prefix Command (Restricted to users with Manage Server permission)
    elif message.content.startswith('{}prefix'.format(pre)):
        # Make sure corerct number of args is supplied
        if len(message.content.split()) != 2:
            await client.send_message(message.channel,
                """\u200BIncorerct number of args, 
correct usage: `f.prefix <prefix>`""")
            return
        # Check for sufficient permissions
        if message.channel.permissions_for(message.author).manage_server:
            # Set the prefix
            db.setPrefix(message.server, message.content.split()[1])
            # Send ACK
            await client.send_message(message.channel,
            """\u200BSucessfully set the prefix to `{}`"""
            .format(message.content.split()[1]))
        else:
            await client.send_message(
                message.channel,
                """\u200BInsufficient permissions. You must have the Manage
                Server permission to do this.""")

    # ---------------------
    # Cryptography Commands
    # ---------------------

    # Rot Cipher Command
    elif message.content.startswith('{}rot'.format(pre)):
        # Check for correct num of args
        if len(message.content.split()) < 4:
            await client.send_message(
                message.channel,
                '```Not enough arguments.\n Usage: \
                f.rot encrypt|decrypt <key> <message...>```')
        else:
            # Extract key
            key = int(message.content.split()[2])
            # Extract text
            txt = " ".join(message.content.split()[3:])
            try:
                # Determine operation
                if message.content.split()[1].upper() == "ENCRYPT":
                    # Perform encryption for rot
                    r = await encryption.rot().encrypt(txt, key)
                    # Send ACK with data
                    await client.send_message(
                        message.channel,
                        '```Encrypted {} with key {}: {}```'
                        .format(txt, key, r))
                elif message.content.split()[1].upper() == "DECRYPT":
                    # Perform decryption for rot
                    r = await encryption.rot().decrypt(txt, key)
                    # Senc ACK with data
                    await client.send_message(
                        message.channel,
                        '```Decrypted {} with key {}: {}```'
                        .format(txt, key, r))
                else:
                    await client.send_message(
                        message.channel,
                        '```Unknown operation for f.rot```')
            except ValueError:
                # Incorrect values provided
                await client.send_message(
                    message.channel,
                    '```Incorrect values. Correct usage: \
                    f.rot encrypt|decrypt text key```')

    # Vigenere Cipher Command
    elif message.content.startswith('{}vigenere'.format(pre)):
        # Check for sufficient number of args
        if len(message.content.split()) < 4:
            await client.send_message(
                message.channel,
                '```Not enough arguments.\n Usage: \
                f.vigenere encrypt|decrypt <key> <message...>```')
        else:
            # Extract key
            key = message.content.split()[2]
            # Extract text
            txt = " ".join(message.content.split()[3:])
            try:
                # Determine operation
                if message.content.split()[1].upper() == "ENCRYPT":
                    # Perform encryption for vigenere
                    r = await encryption.vigenere().encrypt(txt, key)
                    # Send ACK with data
                    await client.send_message(
                        message.channel,
                        '```Encrypted {} with key {}: {}```'
                        .format(txt, key, r))
                elif message.content.split()[1].upper() == "DECRYPT":
                    # Perform decryption for vigenere
                    r = await encryption.vigenere().decrypt(txt, key)
                    # Send ACK with data
                    await client.send_message(
                        message.channel,
                        '```Decrypted {} with key {}: {}```'
                        .format(txt, key, r))
                else:
                    await client.send_message(
                        message.channel,
                        '```Unknown method for f.vigenere```')
            except ValueError:
                # Incorrect values provided
                await client.send_message(
                    message.channel,
                    '```Incorrect values. Correct usage: \
                    f.vigenere encrypt|decrypt <key> <message...>```')

    # XOR Cipher Command
    elif message.content.startswith('{}xor'.format(pre)):
        params = message.content.split()
        # Check for sufficient number of args
        if len(params) < 3:
            await client.send_message(
                message.channel,
                '```Not enough arguments.\n Usage: \
                f.xor [-b][-c] <mask> <message...>```')
        """
        Determine optional parameters used:
        -b = expects the message to be in binary
        -c = outputs in ASCII
        By default it expects a binary key and ASCII text
        and outputs in binary.
        """
        if params[1].lower() == "-c" and params[2].lower() == "-b" \
                or params[1].lower() == "-b" and params[2].lower() == "-c":
            binin, binout = True, False
            mask = params[3]
            text = " ".join(params[4:])
        elif params[1].lower() == "-bc" or params[1].lower() == "-cb":
            binin, binout = True, False
            mask = params[2]
            text = " ".join(params[3:])
        elif params[1].lower() == "-c":
            binout, binin = False, False
            mask = params[2]
            text = " ".join(params[3:])
        elif params[1].lower() == "-b":
            binin, binout = True, True
            mask = params[2]
            text = " ".join(params[3:])
        else:
            binout, binin = True, False
            mask = params[1]
            text = " ".join(params[2:])
        # Perform XOR operation
        returned = await encryption.xor(str(mask), text, binaryout=binout,
                                        binaryin=binin)
        # Send ACK with data
        await client.send_message(message.channel,
                                  '```Result of mask {} on {}: {}```'
                                  .format(mask, text, returned))

    # Steganography command
    elif message.content.startswith('{}steg'.format(pre)):
        # Get args
        args = message.content.split()
        # Create a memory location for a file object
        tmpmemory = BytesIO()
        # Determine operation
        if args[1].lower() == "encrypt":
            """
            Uses a custome request for getting images so that the bot doesn't
            get blocked by servers disallowing anything but the standard
            browser headers. Such as Discord's own CDN.
            """
            req = urllib.request.Request(args[2], 
                                        data=None, 
                                        headers={
                                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
                                        }
                                    )
            # Extract the image as a PIL image object
            image = Image.open(urllib.request.urlopen(req))
            # Extract the text
            text = args[3:]
            # Run encryption for steg
            output = await steganography().encrypt(image, text)
            # Store the output in the memory file object
            output.save(tmpmemory, "png")
            # Move to the start of the memory
            tmpmemory.seek(0)
            # Send the file object in memory
            await client.send_file(message.channel, tmpmemory,
            filename="steg-encrypt.png",
            content="\u200BThe result of LSB steganography on the image provided with message '{}'"
            .format(' '.join(text)))
        elif args[1].lower() == "decrypt":
            req = urllib.request.Request(args[2], 
                                        data=None, 
                                        headers={
                                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
                                        }
                                    )
            # Extract image
            image = Image.open(urllib.request.urlopen(req))
            # Run decryption for steg
            output = await steganography().decrypt(image)
            # ACK with output data
            await client.send_message(message.channel, output)
        elif args[1].lower() == "detect":
            req1 = urllib.request.Request(args[2], 
                                        data=None, 
                                        headers={
                                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
                                        }
                                    )
            req2 = urllib.request.Request(args[3], 
                                        data=None, 
                                        headers={
                                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
                                        }
                                    )
            # Open the images as PIL image objects
            image1 = Image.open(urllib.request.urlopen(req1))
            image2 = Image.open(urllib.request.urlopen(req2))
            # Run detection
            output = await steganography().detect(image1, image2)
            """
            If the image hashes are the same:
            output = True
            else:
            output = False
            """
            if output:
                # Send ACK with result
                await client.send_message(message.channel, "```The images are\
 identical. There is no hidden message.```")
            else:
                # Send ACK with result
                await client.send_message(message.channel, "```The images pro\
vided are different and thus may contain a hidden message.```")
        else:
            return
        
    # Railfence command
    elif message.content.startswith("{}railfence".format(pre)):
        args = message.content.split()[1:]
        if len(args) == 0:
            await client.send_message(message.channel,
                "Correct usage is: `{}railfence encrypt|decrypt <rails> <msg>`"
                .format(pre))
        msg = " ".join(args[2:])
        if args[0].lower() == "encrypt":
            result, result_table = encryption.Railfence().encrypt(msg, int(args[1]))
            output = "```Result of railfence cipher on {} with {} rails: {}".format(msg, int(args[1]), result)
            if result_table is not None:
                output += "\n{}".format(result_table)
            output += "```"
            await client.send_message(message.channel, output)
        elif args[0].lower() == "decrypt":
            result, result_table = encryption.Railfence().encrypt(msg, int(args[1]))
            output = "```Result of railfence cipher on {} with {} rails: {}".format(msg, int(args[1]), result)
            if result_table is not None:
                output += "\n{}".format(result_table)
            output += "```"
            await client.send_message(message.channel, output)
        else:
            await client.send_message(message.channel,
                "Correct usage is: `{}railfence encrypt|decrypt <rails> <msg>`"
                .format(pre))
    
    # Frequency analysis command
    elif message.content.startswith("{}inspect".format((pre))):
        # Remove the prefix, just get the message
        content = " ".join(message.content.split()[1:]).lower()
        # Create the letter dictionary
        letterdict = {}
        # Total used for claculating percentage of letter used
        total = 0
        # Loop each character in content
        for c in content:
            # Skip non-alphabet chars
            if c.isalpha() == False:
                pass
            else:
                # Increment the total number of letters
                total += 1
                # If letter already in dict, increment
                if c in letterdict:
                    letterdict[c] += 1
                # Else set value of 1
                else:
                    letterdict[c] = 1
        # Start of output
        output = "```Frequency analysis for {}:".format(content)
        # Sort the dictionary and append it to the output
        for key, value in sorted(letterdict.items(), key=lambda kv: (-kv[1], kv[0])):
            output += "\n{}: {} ({}%)".format(key, value, int((value/total)*100))
        # Close codeblock
        output += "```"
        await client.send_message(message.channel, output)

    # ---------------------
    # Leaderboard Commands
    # ---------------------

    elif message.content.startswith('{}top'.format(pre)):
        # Get the users (rows)
        rows = db.getTop(message.server)
        col1head, col2head = "Username", "Score"
        col1len = len(col1head)
        # Determine longest length for the username column
        for i in rows:
            col1 = i["username"]
            if len(col1) > col1len:
                col1len = len(col1)
        # Add extra padding
        col1len += 2
        # Generate table headers
        table = "```Rank   {}{}{}\n".format(col1head, " " * math.ceil(col1len - len(col1head)), col2head)
        for c,i in enumerate(rows):
            # Add table rows
            table = table + "{}    | {}{}{}\n".format(c+1, i["username"],
                                                   " " * math.ceil(col1len - len(i["username"])),
                                                   i["score"])
        # Close the code tag
        table = table + "```"
        # Send table
        await client.send_message(message.channel, table)
            
        
    elif message.content.startswith('{}me'.format(pre)):
        # Get data on the user for the server
        user = db.getUser(message.server, message.author)
        # Check if the user is in the db
        if user is None:
            """
            Create the user profile using Discord.user and Discord.member
            attributes
            """
            # Make a dict for user
            user = {}
            user['username'] = message.author.name
            user['profile_pic'] = message.author.avatar_url
            user['score'] = 0
            rank = "Unranked"
        else:
            rank = db.getRank(message.server, message.author)
        # Create the embed
        embed = discord.Embed(title=user["username"], color=0x3498db)
        embed.set_thumbnail(url=user["profile_pic"])
        embed.add_field(name="Score", value=user["score"], inline=True)
        embed.add_field(name="Rank", value=rank, inline=True)
        embed.add_field(name="Join Date", value=message.author.joined_at.date(), inline=True)
        embed.set_footer(text="Funcbot Leaderboard for {}".format(message.server.name))
        # Send the embed
        await client.send_message(message.channel, embed=embed)

    elif message.content.startswith('{}upvote'.format(pre)):
        # Get the user mentioned
        user = message.mentions
        # Check if user trys to upvote theirself
        if user[0] == message.author:
            await client.send_message(message.channel,
                "\u200BYou can't upvote yourself!")
            return
        # Check they have only mentioned one user
        if len(user) > 1:
            await client.send_message(message.channel,
                "\u200BOnly mention one user")
            return
        # Check to see if any users have been mentioned at all
        elif len(user) == 0:
            await client.send_message(message.channel,
                "\u200BPlease mentione a user")
            return
        else:
            # Check to see it's been at least 24 hours since last upvote
            if db.userCanUpvote(message.server, message.author):
                # Upvote selected user
                db.upvoteUser(message.server, user[0])
                # Reset timer for last upvote for author on server
                db.setUpvoteTimer(message.server, message.author)
                # Sen ACK
                await client.send_message(message.channel,
                    "\u200BSucessfully upvoted {}".format(user[0].mention))
            else:
                # Get time remaining
                time = db.getUpvoteTimer(message.server, message.author)
                # Send ACK with time remaining
                await client.send_message(message.channel,
                    "\u200BSorry! You can upvote again in {}".format(time))

    # ----------------
    # Watcher Commands
    # ----------------
    
    elif message.content.startswith('{}watch'.format(pre)):
        # Get args
        args = message.content.split()
        # Check for sufficient number of args
        if len(args) == 1:
            await client.send_message(message.channel,
            "\u200BNot enough args, usage: `{}watch add|remove <url>`"
            .format(pre))
            return
        # Determine operation
        if args[1].lower() == "add":
            # Get URLs for the server
            urls = db.getWatching(message.server)
            # Check to see if server has reached its limit
            if len(urls) == 3:
                await client.send_message(message.channel,
                    "\u200BThis server has too many URLs, please remove one.")
                return
            else:
                req = urllib.request.Request(args[2], 
                                        data=None, 
                                        headers={
                                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
                                        }
                                    )
                # Get site
                site = urllib.request.urlopen(req)
                # Read the content of the site (raw HTML)
                content = site.read()
                # Check the filesize using sys.getfiszeof()
                filesize = getsizeof(content)/1024
                # Check to see filesize is less than 200KB
                if filesize < 200:
                    # Get the mentioned channel
                    channel = message.channel_mentions[0]
                    # Add watching for server with the URL and content
                    db.setWatching(message.server, args[2], channel, content)
                    # Send ACK
                    await client.send_message(message.channel,
                    "\u200BSuccessfully added URL to watch list")
                    return
                else:
                    await client.send_message(message.channel,
                    "\u200BThe file size for this site exceeds `200KB`")
                    return
        elif args[1].lower() == "remove":
            # Get URLs for server
            urls = db.getWatching(message.server)
            # Check to see if server has any URLs being watched
            if len(urls) == 0:
                await client.send_message(message.channel,
                    "\u200BThis server is not watching any URLs")
                return
            found = False
            # Check to see if valid URL in server's watched URLs
            for i in urls:
                if i["url"] == args[2]:
                    found = True
            if found:
                # Remove URL from server's watched URLs
                db.removeWatching(message.server, args[2])
                # Send ACK
                await client.send_message(message.channel,
                    "\u200BSuccessfully removed URL from watch list")
                return
            else:
                await client.send_message(message.channel,
                    "\u200BThis server is not watching this URL")
    # ---------
    # Timer Log
    # ---------
    total_time = datetime.datetime.now() - start_time
    print("Response time:",total_time.total_seconds())

# Create background task to check URLs every 10 minutes
client.loop.create_task(Watcher())
# Token to connect to the Discord API
client.run('<TOKEN HERE>')
