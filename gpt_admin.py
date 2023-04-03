#!/usr/bin/env python3
import subprocess
import sys
import threading
import time
from enum import Enum
from io import StringIO

import openai
import os

import tiktoken as tiktoken

try:
    openai.api_key = os.environ['api_key']
except KeyError:
    print("OpenAI API Key not set as environment variable! Try using: \n\texport api_key=<api key value>")
    exit()

# max_num_tokens = 4096
max_num_tokens = 3000


# max_num_tokens = 2048
# max_num_tokens = 1024


class Role(Enum):
    SYSTEM = "system"
    USER = "user"


max_idle_time = 500
idle = 0

gpt_sleep_time = 5
gpt_sleep_time_sem = threading.Semaphore(1)
pause = False
pause_sem = threading.Semaphore(1)

show_server_output = False
show_server_output_sem = threading.Semaphore(1)

messages = []

new_output = ""
new_output_sem = threading.Semaphore(1)
lines = 0

executable = 'java -Xmx1024M -Xms1024M -jar server.jar'

argc = len(sys.argv)
if argc > 1:
    server_dir = sys.argv[1]
else:
    server_dir = '../server'

try:
    with open("initial_prompt.txt", "r") as f:
        initial_training_prompt = f.read()
        f.close()
except FileNotFoundError:
    print("initial_prompt.txt not found in directory! Make sure this file is stored in the same directory of this "
          "script.")

print("initial prompt: ")
print(initial_training_prompt)


def send_system_prompt(prompt):
    return send_user_prompt(prompt, Role.SYSTEM)


def send_server_update(server_output):
    return send_user_prompt(server_output)


def num_tokens_from_messages(ms, model="gpt-3.5-turbo-0301"):
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo-0301":  # note: future models may deviate from this
        num_tokens = 0
        for message in ms:
            num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":  # if there's a name, the role is omitted
                    num_tokens += -1  # role is always required and always 1 token
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens
    else:
        raise NotImplementedError(f"""num_tokens_from_messages() is not presently implemented for model {model}.""")


initial_num_tokens = num_tokens_from_messages([{"role": Role.SYSTEM.value, "content": initial_training_prompt}])
print("initial prompt num of tokens: " + str(initial_num_tokens))


def print_messages():
    for m in messages:
        print(m["content"])


def send_user_prompt(prompt, role=Role.USER):
    msg_obj = {"role": role.value, "content": prompt}

    # TODO handle single message with token length > max_num_tokens
    # if len(messages) > 0 and num_tokens_from_messages([msg_obj]) > max_num_tokens - initial_num_tokens:
    #     prompt = prompt[-(max_num_tokens - initial_num_tokens)]
    # msg_obj = {"role": role.value, "content": prompt}

    messages.append(msg_obj)

    while len(messages) > 1 and num_tokens_from_messages(messages) > max_num_tokens:
        print("removing old messages from request: " + str(num_tokens_from_messages(messages)) + "/" + str(
            max_num_tokens))
        messages.pop(1)

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
    except openai.error.InvalidRequestError:
        print("too many tokens in request!")
        print_messages()
        return "ERROR"
    new_message = completion.choices[0].message
    messages.append(new_message)

    return new_message.content


def execute_server_command(command):
    process.stdin.write(command + "\n")
    process.stdin.flush()


def handle_response(r):
    print("\n\ngpt response: \n" + r + "\n\n")
    for line in StringIO(r):
        if line[0] == "":
            continue
        elif line[0] == "/":
            execute_server_command(line)
        else:
            execute_server_command("/say " + line)


def restart_gpt():
    messages.clear()  # TODO is this atomic? might need to use semaphore
    messages.append({"role": Role.SYSTEM.value, "content": initial_training_prompt})


def input_thread():  # function to read user input and write it to the process input stream
    while True:
        user_input = input()
        if len(user_input) <= 0:
            continue
        elif user_input[0] == "!":
            handle_response(send_system_prompt(user_input))
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


os.chdir(server_dir)
process = subprocess.Popen(executable, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

# start a separate thread to handle user input
input_thread = threading.Thread(target=input_thread)
input_thread.start()

# start a separate thread to handle server output
output_thread = threading.Thread(target=output_thread)
output_thread.start()

print("initial gpt response: \n\n" + send_system_prompt(initial_training_prompt))

while True:
    time.sleep(get_gpt_sleep_time())

    pause_sem.acquire()
    if pause:
        continue
    pause_sem.release()

    if len(get_new_output()) <= 0:
        idle += 1
        if idle * 5 > max_idle_time:
            idle = 0
            print("Server has been idle for too long! Time for some fun...")
            send_system_prompt("punish some players")
        continue
    response = send_server_update(get_and_clear_new_output())
    handle_response(response)

# TODO gracefully exit

process.wait()

input_thread.join()
output_thread.join()

process.stdin.close()
process.kill()
