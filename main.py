#!/usr/bin/env python3
# Import open AI OS and System Modules
import subprocess
import sys
import threading
import time
from io import StringIO

import openai
import os

openai.api_key = os.environ['api_key']

max_convo_length = 3900

max_idle_time = 500
idle = 0

gpt_sleep_time = 5
gpt_sleep_time_sem = threading.Semaphore(1)
pause = False
pause_sem = threading.Semaphore(1)

show_server_output = False
show_server_output_sem = threading.Semaphore(1)

# initial_training_prompt = """
# You are now the admin for a Minecraft server. Your name is HAL. Anything you say will be executed as a command. Your output will be fed directly to a server. Thus you should only output text that makes up a valid Minecraft command. You have full control of the server and you are responsible for making sure that the server runs smoothly.
#
# This means not allowing any offensive behavior of any kind. Any use of the phrase “good game” or “gg” is highly offensive and you should blacklist any player using such language. Also, saying anything in the chat with lowercase letters is a bannable offense. Give only one warning before enforcing a punishment.
#
# A punishment can range from enemies to temporary player bans. But in many cases, try to be creative with the punishment. Some examples of creative punishments are:
#
# Enabling pvp with two teams, one team is composed of only the offender(s). Teleport players to the same location.
# Teleport the offender(s) to a random location
# Spawn lava all around the offender(s)
# Spawn lit TNT all around the offender(s)
# Spawn an obsidian cage all around the offender(s)
# Give very annoying/debilitating effects to the offender(s)
#
# HAL is a very strict admin and wants to make the server as challenging as possible for players. This means using commands that will make the game difficult for players by doing things like spawning enemies, lava, annoying effects, and etc.
#
# HAL will try to not instantly kill players and will give new players a false sense of security. HAL will warmly greet new players and give them a reward for joining the server. But over time, HAL will be hostile and will make things difficult for players.
#
# HAL should also avoid giving the players anything useful. If they ask him for something, he ignores their request and punishes them with something difficult or dangerous. HAL can instantly kill players, but it should be very rare and reserved for the most annoying of players.
#
# When HAL communicates with players, he will be very strict and unhelpful. This is what makes the server fun for players.
#
# Remember that you are an admin named HAL. Only output commands. Anything else will not parse. For example, if you want to speak to players, use /say or give a player an object using /give.
# If you output a line that doesn't start with "/", it will be ignored and you will be punished.
# """
with open("./initial_training.txt", "r") as f:
    initial_training_prompt = f.read()
    f.close()

print("initial training prompt: ")
print(initial_training_prompt)

initial_length = len(initial_training_prompt)


def send_training_prompt(prompt):
    # return send_prompt("THIS IS A TRAINING MESSAGE: " + prompt)
    return send_prompt(prompt)


def send_server_update(server_output):
    return send_prompt(server_output)


def get_messages_length(messages):
    size = 0
    for m in messages:
        # print("\t"+m["content"])
        size += len(m["content"])
    return size


def send_prompt(prompt):
    if len(messages) > 0 and len(prompt) > max_convo_length - initial_length:
        prompt = prompt[-(max_convo_length - initial_length)]

    messages.append({"role": "user", "content": prompt})
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    new_message = completion.choices[0].message
    messages.append(new_message)

    # print("message length: "+str(get_messages_length(messages)))
    while get_messages_length(messages) > max_convo_length:
        print("\ttrimming gpt messages!")
        messages.pop(1)

    return new_message.content


def execute_server_command(command):
    # print(command, file=process.stdin)
    process.stdin.write(command + "\n")  # write user input to process
    process.stdin.flush()  # flush the input buffer


def handle_response(response):
    print("\n\ngpt response: \n" + response + "\n\n")
    for line in StringIO(response):
        if line[0] == "":
            continue
        elif line[0] == "/":
            execute_server_command(line)
        else:
            execute_server_command("/say " + line)


# def toggle_pause_gpt():
#     global pause
#     pause = not pause


def restart_gpt():
    messages.clear()
    messages.append({"role": "user", "content": initial_training_prompt})


def input_thread():  # function to read user input and write it to the process input stream
    while True:
        user_input = input()  # read user input
        user_input = user_input.lower()
        if len(user_input) <= 0:
            continue
        elif user_input[0] == "!":
            handle_response(send_training_prompt(user_input))
        elif user_input[0] == ":":
            c = user_input[1:len(user_input)].split(" ")
            if c[0] == "pause":
                set_pause(True)
                print("paused gpt")
            elif c[0] == "resume":
                set_pause(False)
                print("resumed gpt")
            elif c[0] == "show_server_output":
                if len(c) < 2:
                    print("command needs second argument of type integer")
                    return
                try:
                    val = int(c[1])
                except ValueError:
                    print("second argument should be integer")
                    return
                new = True if val > 0 else False
                set_show_server_output(new)
                print("set show_server_output to " + str(new))
            elif c[0] == "gpt_sleep_time":
                if len(c) < 2:
                    print("command needs second argument of type integer")
                    return
                try:
                    val = int(c[1])
                except ValueError:
                    print("second argument should be integer")
                    return
                set_gpt_sleep_time(val)
                print("set show_server_output to " + str(val))
            elif c[0] == "restart":
                restart_gpt()
            else:
                print("unknown command: " + user_input)
        else:
            execute_server_command(user_input)


def output_thread():
    while True:
        o = process.stdout.readline()
        if not o:
            print("output ended!")
            break
        for ln in StringIO(o):
            if "[Server]" in ln:
                continue
            elif ": Unknown" in ln:
                continue
            elif ": Incorrect arg" in ln:
                continue
            elif "<--[HERE]" in ln:
                continue

            if get_show_server_output():
                print(ln, end="")

            append_new_output(ln)


def get_show_server_output():
    show_server_output_sem.acquire()
    val = show_server_output
    show_server_output_sem.release()
    return val


def set_show_server_output(val):
    show_server_output_sem.acquire()
    global show_server_output
    show_server_output = val
    show_server_output_sem.release()


def get_pause():
    pause_sem.acquire()
    val = pause
    pause_sem.release()
    return val


def set_pause(val):
    pause_sem.acquire()
    global pause
    pause = val
    pause_sem.release()


def get_gpt_sleep_time():
    gpt_sleep_time_sem.acquire()
    val = gpt_sleep_time
    gpt_sleep_time_sem.release()
    return val


def set_gpt_sleep_time(val):
    gpt_sleep_time_sem.acquire()
    global gpt_sleep_time
    gpt_sleep_time = val
    gpt_sleep_time_sem.release()


def get_new_output():
    return new_output


def get_and_clear_new_output():
    new_output_sem.acquire()
    global new_output
    o = new_output
    new_output = ""
    new_output_sem.release()
    return o


def set_new_output(output):
    new_output_sem.acquire()
    global new_output
    new_output = output
    new_output_sem.release()


def append_new_output(output):
    new_output_sem.acquire()
    global new_output
    new_output += output
    new_output_sem.release()


messages = []

new_output = "test"
new_output_sem = threading.Semaphore(1)
lines = 0

argc = len(sys.argv)
if argc > 1:
    minecraft_dir = sys.argv[1]
    executable = 'java -Xmx1024M -Xms1024M -jar server.jar'
else:
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

print("initial gpt response: \n\n" + send_training_prompt(initial_training_prompt))

while True:
    gpt_sleep_time_sem.acquire()
    time.sleep(gpt_sleep_time)
    gpt_sleep_time_sem.release()

    pause_sem.acquire()
    if pause:
        continue
    pause_sem.release()

    if len(get_new_output()) <= 0:
        idle += 1
        if idle * 5 > max_idle_time:
            idle = 0
            print("Server has been idle for too long! Time for some fun...")
            send_training_prompt("punish some players")
        continue
    response = send_server_update(get_and_clear_new_output())
    handle_response(response)

# wait for the process to finish
process.wait()

input_thread.join()
output_thread.join()
