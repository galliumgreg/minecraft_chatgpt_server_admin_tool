# minecraft_chatgpt_server_admin_tool

This tool connects a Minecraft server's output to OpenAI's GPT-3.5 model through the OpenAI API. The script runs the Minecraft server in a subprocess and listens to its output. When new output is detected, it is sent to the GPT-3.5 model as a message. The model then generates a response and the tool sends it tot he server as a command.

The first message sent to the model is determined by the contents of `initial_prompt.txt`. This first message is preserved in all requests. Editing this will change how the model responds.

## Installation

To use this script, you will need Python 3 and OpenAI's openai package installed. You will also need a valid OpenAI API key, which you can obtain from the OpenAI website.

You will also need to have a Minecraft server set up. 

## Usage

To use this script, run it from the command line with the directory of your Minecraft server as the first argument:

```
minecraft_chatgpt.py /path/to/minecraft/server
```

You can customize the command used to start the Minecraft server by editing the executable variable near the top of gpt_admin.py. Note that the jarfile must be named "server.jar".

Once the script is running, you can start and stop the Minecraft server using the usual commands, such as stop. You can also send a message to the GPT-3.5 model by typing ! followed by your message. For example:

```
!teleport <player name> to a random location
```

To send a command directly to the Minecraft server, type the command as you would in the Minecraft client.

You can also enter various commands to control the script itself. These commands start with : and include:
* `:pause`: Pause the GPT-3.5 model, preventing it from generating new messages.
* `:resume`: Resume the GPT-3.5 model if it was paused.
* `:show_server_output <0/1>`: Enable or disable printing of the Minecraft server's output to the console. The argument should be 0 to disable output or 1 to enable it.
* `:gpt_sleep_time <seconds>`: Set the number of seconds that the script should wait between sending prompts to the GPT-3.5 model. The argument should be an integer number of seconds.
* `:restart`: Restart the GPT-3.5 model, clearing its conversation history.

## License

This script is released under the MIT License. See LICENSE for more information.
