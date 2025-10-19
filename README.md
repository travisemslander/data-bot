## Setup
1. Create a discord bot by visiting https://discord.com/developers/applications
    - Give the bot ability to read message content as well as sending messages and adding reactions
2. Set up OpenAI platform account and generate an API Key. You'll need to deposit a small amount of money, just $10 should last quite some time as this uses very small amount of tokens.
3. Create .env file and set the following
    - TOKEN - the discord token of your bot
    - OPENAI_KEY - the OpenAI key
4. Make sure you have Docker installed
5. Run `make build` to build the docker image
6. Run `make run` to run

