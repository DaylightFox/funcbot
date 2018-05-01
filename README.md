# Funcbot
A cryptographic bot for Discord

## About
Funcbot is a cryptographic bot primarily made for use in Discord cryptography ARGs. Inspiration was brought about from the 7879 (1EC7) ARG that was used for recruitment.

## Setup
### Requirements
This bot requires the following:
+ Discord.py
+ PIL
+ PyMySQL

### Installation
To setup the bot, you must do the following:
1. Create a virtual env for it using Python 3.5
2. Install the required modules
3. Add your token to main.py
4. Add your login details for MySQL in main.py
5. Open your vitual env using `source <venv-name>/bin/activate`
5. run the bot using `python main.py`

## Commands

### General Commands
| Usage | Description |
| ----- | ----------- |
| `f.help [-me]` | Shows the command list. Adding the optional parameter `-me` will send a DM of the full command list |
| `f.watch add&#124;remove <url>` | Funcbot will save up to 3 HTML pages of maximum size `200kb` per server. Pages are checked every 10 minutes |

### Cryptographic Commands
| Usage | Decription |
| ----- | ---------- |
| `f.rot encrypt\|decrypt <key> <message...>` | Encrypts/decrypts `message` with `key` using the rot cipher |
| `f.vigenere encrypt\|decrypt <key> <message...>` | Encrypts/decrypts `message` with `key` using the vigenère cipher |
| `f.xor [-b][-c] <mask> <message...>` | Applies the `mask` to `message` using XOR logic. By default, the comamnd will expect the mask to be binary and message to be characters, and will output in binary. Applying optional parameter `-c` will provide output in ASCII. Applying optional parameter `-b` will expect the message to be in binary format. |
| `f.railfence encrypt\|decrypt <rails> <message...>` | Encrypts/decrypts `message` with `rails` using the railfence cipher |
| `f.inspect <message...>` | Performs frequency analysis on `message` and provides a table ranked from most to least used |
#### Steganography
| Usage | Description |
| ----- | ----------- |
| `f.steg detect <image1> <image2>` | Detects if the images have been altered. **Note: The bot checks the md5 hash of the images to see if they are identical or not.** |
| `f.steg encrypt <image> <message...>` | Encrypts `image` with `message` using LSB steganography |
| `f.steg decrypt <image>` | Decrypts the image and returns the output. **Note: This command assumes the image has been encrypted using LSB.** |

### Leaderboard System
**Note: Leaderboards are on a per server basis**
| Usage | Description |
| ----- | ----------- |
| `f.top` | Displays the top 10 contributors of the server |
| `f.me` | Displays your current contribution points |
| `f.upvote <@user>` | Upvotes `user` (24hr cooldown) |

### Admin Commands
| Usage | Description |
| ----- | ----------- |
| `f.clear <x>` | Deletes `x` messages (up to 100). **Note: Restricted to users with manage messages permission** |
| `f.limit <channel>` | Limits all none Admin commands to `channel` on the server. **Note: Restricted to users with manage server permission** |
| `f.prefix <prefix>` | Changes the bot prefix to `prefix` for the server. **Note: Restricted to users with manage server permission** |
