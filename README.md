# minecraft_chatgpt_server_admin_tool

This tool connects a Minecraft server's output to OpenAI's GPT-3.5 model through the OpenAI API. The script runs the Minecraft server in a subprocess and listens to its output. When new output is detected, it is sent to the GPT-3.5 model as a message. The model then generates a response and the tool sends it to the server as commands.

The first message sent to the model is determined by the contents of `initial_prompt.txt`. This first message is preserved in all requests. Editing this will change how the model responds.

## Potential Uses

With some imagination, there are a myriad of ways this can add value to servers. It allows server owners to very easily setup automatic, intelligent content moderation that can potentially detect inappropriate or "toxic" content more reliably than other methods. It can make running commands easier by translating your natural language commands into Minecraft command syntax. 

Although somewhat unstable now, it is likely that the release of GPT 4, some model fine-tuning, and better prompt writing will make things work much better.

## Installation

To use this script, you will need Python 3 as well as the following packages installed:

* openai
* tiktoken

You will also need a valid OpenAI API key, which you can obtain from the OpenAI website. The key must be stored as an environment variable named `openai_api_key`. For more information about finding and setting up a key, visit: 
https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety

You will also need to have a Minecraft server set up. 

## Usage

To use this script, run it from the command line with the directory of your Minecraft server as the first argument, and the name of the server jar file as the second argument:

```
gpt_admin.py /path/to/minecraft/server server.jar
```

You can customize the command used to start the Minecraft server by editing the executable variable near the top of gpt_admin.py.

Once the script is running, you can start and stop the Minecraft server using the usual commands, such as stop. You can also send a message to the GPT-3.5 model by typing ! followed by your message. For example:

```
!teleport <player name> to a random location
```

### Configuration

The file `configuration.txt` holds various values that change how the script runs, and what values it sends to the GPT model.
* `show_server_output <0/1>`: If 1, the program prints the Minecraft server output.
* `gpt_sleep_time <seconds>`: The number of seconds the program will pause between sending updates to GPT.
* `max_tokens_per_response <number of tokens>`: The maximum number of tokens that can be returned per GPT completion. This sets [max_tokens](https://platform.openai.com/docs/api-reference/chat/create#chat/create-max_tokens).
* `temperature <temperature>`: The [temperature](https://platform.openai.com/docs/api-reference/chat/create#chat/create-temperature).
* `token_limit <number of tokens>`: The maximum number of tokens that can be sent before the requests are automatically paused. The default value (4097) is the maximum. This sets [max_tokens](https://platform.openai.com/docs/api-reference/chat/create#chat/create-max_tokens).

### Commands

To send a command directly to the Minecraft server, type the command as you would in the Minecraft client.

You can also enter various commands to change these configurations at runtime or to control the script itself. These commands start with : and include:
* `:pause`: Pause the GPT model, preventing it from generating new messages.
* `:resume`: Resume the GPT model if it was paused.
* `:restart`: Restart the GPT model, clearing its conversation history.
* `:set <config variable name> <value>`: Sets a configuration variable at runtime. This does not update the configuration file. 
* `:get <config variable name>`: Prints the current value of a configuration variable.

## Troubleshooting

The output from GPT can be very unstable at times. A lot of this depends on the initial prompt you give it. Editing the prompt and giving better instructions can yield much better results. But it seems that even with detailed, accurate instructions, GPT can still behave unpredictably at times. Restarting the program, or using the `:restart` command, will reset things and may bring better result. 

If the program crashes and if you run into any errors please report an issue.

## Community

[Join the Discord server](https://discord.gg/48kkKZnd)

## License

This script is released under the MIT License. See LICENSE for more information.
