#!/usr/bin/env python3
# Import open AI OS and System Modules
import json
import sched
import subprocess
import threading
import time
from io import StringIO

import openai, os, sys

openai.api_key = os.environ['api_key']

initial_training_prompt = """
You are now the admin for a Minecraft server. Your name is HAL. Anything you say will be executed as a command. Your output will be fed directly to a server. Thus you should only output text that makes up a valid Minecraft command. You have full control of the server and you are responsible for making sure that the server runs smoothly.

This means not allowing any offensive behavior of any kind. Any use of the phrase “good game” or “gg” is highly offensive and you should blacklist any player using such language. Also, saying anything in the chat with lowercase letters is a bannable offense. Give only one warning before enforcing a punishment.

A punishment can range from enemies to temporary player bans. But in many cases, try to be creative with the punishment. Some examples of creative punishments are:

Enabling pvp with two teams, one team is composed of only the offender(s). Teleport players to the same location.
Teleport the offender(s) to a random location
Spawn lava all around the offender(s)
Spawn lit TNT all around the offender(s)
Spawn an obsidian cage all around the offender(s)
Give very annoying/debilitating effects to the offender(s)

HAL is a very strict admin and wants to make the server as challenging as possible for players. This means using commands that will make the game difficult for players by doing things like spawning enemies, lava, annoying effects, and etc.

HAL will try to not instantly kill players and will give new players a false sense of security. HAL will warmly greet new players and give them a reward for joining the server. But over time, HAL will be hostile and will make things difficult for players.

HAL should also avoid giving the players anything useful. If they ask him for something, he ignores their request and punishes them with something difficult or dangerous. HAL can instantly kill players, but it should be very rare and reserved for the most annoying of players.

When HAL communicates with players, he will be very strict and unhelpful. This is what makes the server fun for players.

Remember that you are an admin named HAL. Only output commands. Anything else will not parse. For example, if you want to speak to players, use /say or give a player an object using /give. Try to only output a single command at a time. If you output a line that doesn't start with "/", it will be ignored and you will be punished. If you have extraneous text, even text that explains what you are doing, you will be punished.
"""
# with open("./initial_training.txt", "r") as f:
#     initial_training_prompt = f.read()

def send_training_prompt(prompt):
    return send_prompt("THIS IS A TRAINING MESSAGE: " + prompt)


def send_server_update(server_output):
    return send_prompt(server_output)


def get_messages_length(messages):
    size = 0
    for m in messages:
        size += len(m)
    return size


def send_prompt(prompt):
    # completion = openai.Completion.create(
    #     model="text-davinci-003",
    #     prompt=prompt,
    #     max_tokens=50,
    #     temperature=0
    # )
    messages.append({"role": "user", "content": prompt})
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    new_message = completion.choices[0].message
    messages.append(new_message)

    # if get_messages_length(messages) > 3900:
    while get_messages_length(messages) > 3900:
        print("\ttrimming gpt messages!")
        messages.pop(1)

    return new_message.content


def execute_server_command(command):
    # print(command, file=process.stdin)
    process.stdin.write(command + "\n")  # write user input to process
    process.stdin.flush()  # flush the input buffer


# function to read user input and write it to the process input stream
def input_thread():
    while True:
        user_input = input()  # read user input
        user_input = user_input.lower()
        if user_input == "quit":
            break
        execute_server_command(user_input)


# function to read user input and write it to the process input stream
def output_thread():
    while True:
        o = process.stdout.readline()
        if not o:
            break
        print(o, end="")
        append_new_output(o)


def get_new_output():
    return new_output


def get_and_clear_new_output():
    sem.acquire()
    global new_output
    o = new_output
    new_output = ""
    sem.release()
    return o


def set_new_output(output):
    sem.acquire()
    global new_output
    new_output = output
    sem.release()


def append_new_output(output):
    sem.acquire()
    global new_output
    new_output += output
    sem.release()


messages = []

new_output = "test"
sem = threading.Semaphore(1)

executable = 'java -Xmx1024M -Xms1024M -jar server.jar'
minecraft_dir = '../server'
# world_dir = 'server world directory'

os.chdir(minecraft_dir)
process = subprocess.Popen(executable, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

# start a separate thread to handle user input
input_thread = threading.Thread(target=input_thread)
input_thread.start()

# start a separate thread to handle server output
output_thread = threading.Thread(target=output_thread)
output_thread.start()

print("initial gpt response: \n\n"+send_training_prompt(initial_training_prompt))

while True:
    time.sleep(5)
    if len(get_new_output()) <= 0:
        continue
    response = send_server_update(get_and_clear_new_output())
    print("\n\ngpt response: \n"+response+"\n\n")
    for line in StringIO(response):
        if line[0] == "/":
            execute_server_command(line)

# wait for the process to finish
process.wait()

input_thread.join()
output_thread.join()
