# Import necessary libraries
from openai import AzureOpenAI
import os
import time
import sys
import re
import unicodedata
import asyncio
from twitchio.ext import commands

# ********************************************************************************************************************
# ******************************************** SET VARIABLES *********************************************************
# ********************************************************************************************************************

# Twitch
TWTICH_TOKEN = os.environ["TWITCH_TOKEN"]                       # Get the Twitch token from environment variables
CHANNEL_NAME = os.environ["TWITCH_CHANNEL"]                     # Specify the Twitch channel to send messages to

#Azure
ASSISTANT_ID = os.environ["AZ_ASSISTANT_ID"]                    # Get the Azure assistant ID from environment variables
api_URI = os.environ["AZ_ASSISTANT_URI"]                        # Get the Azure assistant URI from environment variables
api_KEY = os.environ["AZ_ASSISTANT_API_KEY"]                    # Get the Azure assistant API key from environment variables
api_version = "2024-02-15-preview"                              # Set the API version 

#Command Line
name_of_chatter = "@" + sys.argv[1]                             # Get the name of the chatter from command line arguments
game_played = sys.argv[2]                                       # Get the game from the broadcaster from command line arguments    

# Define a function to remove emojis from text - this is necessary because sometimes the response contains emojis and we only want the text
def remove_emojis(text):
    return ''.join(c for c in text if unicodedata.category(c) not in ['So', 'Cn'])

# ********************************************************************************************************************
# ************************************** AZURE OPENAI ASSISTANT SETUP ************************************************
# ********************************************************************************************************************

# Create an AzureOpenAI client with the specified API key, version, and endpoint
client = AzureOpenAI(api_key=api_KEY, api_version=api_version, azure_endpoint=api_URI)

# Create a new thread
thread = client.beta.threads.create()

# Send a message to the thread
message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content= "The game we're playing is " + game_played + ". The user is " + name_of_chatter + ".",
)

# Send thread to the Assistant as a new run
run = client.beta.threads.runs.create(
    thread_id=thread.id, assistant_id=ASSISTANT_ID
    )

# Wait for run to complete
while run.status != "completed":
    run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
    time.sleep(1)

# Get the latest message from the thread
message_response = client.beta.threads.messages.list(thread_id=thread.id)
messages = message_response.data
latest_message = messages[0]

# Remove emojis from the message
text_without_emoji = remove_emojis(latest_message.content[0].text.value)

# ********************************************************************************************************************
# ******************************************* TWITCH BOT SETUP *******************************************************
# ********************************************************************************************************************

# We're going to use the TwitchIO library to create a bot that will send the message to the Twitch channel, but this 
# will throw an error since we're not triggering the bot with a command. We're just sending a message to Twitch. We 
# can ignore this error.

class Bot(commands.Bot):

    # Initialize the Bot with a token and a prefix, and specify the initial channel to join
    def __init__(self):
        super().__init__(token=TWTICH_TOKEN, prefix='!', initial_channels=[CHANNEL_NAME])

    # Define an asynchronous event that is triggered when the bot is ready
    async def event_ready(self):
        # Join the specified channels
        await self.join_channels(CHANNEL_NAME)
        # Pause for 1 second
        await asyncio.sleep(1)
        # Get the specified channel
        channel = self.get_channel(CHANNEL_NAME)
        # If the channel exists, try to send a message to it
        if channel:
            try:
                await channel.send(text_without_emoji)
            except AttributeError:
                pass  # Suppress the error
        # If the channel does not exist, print an error message
        else:
            print("Channel not found or failed to join.")

    # Define an asynchronous event that is triggered when a message is received
    async def event_message(self, message):
        print(message.content)
        await self.handle_commands(message)

# Initialize the Twitch bot and send the message
bot = Bot()
bot.run()

sys.exit(0)


