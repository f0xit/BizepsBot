# Read me #

## About the project ## 

This bot was created as my first project in Python.  
Before that I mostly scripted in PowerShell which is still my main language.  
Since discord.py was discontinued, the bot was ported to py-cord and slash commands are fully implemented.  

## About the bot ## 

Most of the settings are configurable via the Settings.json, an example is provided.  
There are a few hardcoded IDs, you can just delete or replace them.  
For some functionality like Twitch notifications, tokens are needed, this is also provided via an example file.  
Some stuff like the trash reminder is only for my personal use, the functionality is pretty simple but you will need to provide the file yourself.  
This is by all means a **fun** project and should not be considered for production environments.
Logging is not implemented for commands that just return text or are just for fun.  
Since this was a learning-by-doing project there will be multiple code snippets which will do the same but are extremly different in quality.  
Feel free to open an issue thread or a pull request with suggestions or better code.

**THIS IS BY NO MEANS AN "OUT OF THE BOX" BOT, YOU SHOULD BE FAMILIAR HOW TO SET UP A DISCORD BOT TO USE THIS**  

## To Dos ## 

+ Split Messages over 2k chars | Needs to be implemented as func