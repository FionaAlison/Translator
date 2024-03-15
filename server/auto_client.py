import socket 
import os.path
import sys
from select import select
from meta_data import *
from time import sleep
from server.translator_langs import LANGUAGES
from random import randint, choice
from string import ascii_letters, digits

MESSAGE: bytes = bytes()
auto_message: list[str] = list()
try:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    server.connect((host, port))
except Exception:
    print("Unable to connect!\n")
    quit(1)

# Configuration params
client_files_id = 'autoclient_' + ''.join(choice(ascii_letters+digits) for _ in range(10))
limit_requests: int = 1000
request_time_offset: float = 1.0
files_created_to_delete: list[str] = [] # delete after reaching past limit = 10

args = sys.argv
if len(args) < 3:
    print(f"Missing params: {len(args)} given {3} required!\n")
    quit(1)

try:
    limit_requests = int(args[1])
    request_time_offset: float = float(args[2])
except:
    print("Invaid args values!\n")
    quit(1)

def randomize_command() -> tuple[list[str], list[int]]:
    global limit_requests
    limit_requests -= 1
    command: list[str] = list()
    server_command: list[str] = list()
    choice: int = ['info', 'ts', 'tt'][randint(0, 2)]
    command.append(choice)
    server_command.append(choice)
    input_dir_choice = randint(0, 1)
    match choice:
        case 'info':
            command.append(str(randint(5, 20)))
        case 'ts':
            if input_dir_choice:
                # image
                path = os.path.join(cwd, 'client_requests_data', 'ts', 'images')
                images = os.listdir(path)
                selection = images[randint(0, len(images)-1)]
                command.append(os.path.join(path, selection))
                server_command.append(selection)
            else:
                # text
                path = os.path.join(cwd, 'client_requests_data', 'ts', 'text')
                text_files = os.listdir(path)
                selection = text_files[randint(0, len(text_files)-1)]
                command.append(os.path.join(path, selection))
                server_command.append(selection)

            out_file_name: str = client_files_id+'_ts_'+'.txt'
            command.append(os.path.join(cwd, 'client_requests_data', 'results', out_file_name))
            server_command.append(out_file_name)
        case 'tt':
            if input_dir_choice:
                # image
                path = os.path.join(cwd, 'client_requests_data', 'tt', 'images')
                images = os.listdir(path)
                selection = images[randint(0, len(images)-1)]
                command.append(os.path.join(path, selection))
                server_command.append(selection)
            else:
                # text
                path = path = os.path.join(cwd, 'client_requests_data', 'tt', 'text')
                text_files = os.listdir(os.path.join(path))
                selection = text_files[randint(0, len(text_files)-1)]
                command.append(os.path.join(path, selection))
                server_command.append(selection)

            out_file_name: str = client_files_id+'_tt_'+'.txt'
            lang: str = list(LANGUAGES.keys())[randint(0, len(LANGUAGES.keys()))]
            command.append(os.path.join(cwd, 'client_requests_data', 'results', out_file_name))
            command.append(lang)
            server_command.append(out_file_name)
            server_command.append(lang)

    return command, server_command

while True:
    server.recv(buffer_size)
    sleep(request_time_offset)
    if limit_requests > 0: auto_message, server_auto_message = randomize_command()
    else: auto_message = ['exit']; server_auto_message = ['exit']
    print('\n', client_files_id, ''.join(server_auto_message))
    MESSAGE = ' '.join(server_auto_message).encode()
    server.send(MESSAGE)
    if 'info' == auto_message[0]:
        sys_info: str = ''
        while True:
            readable, _, _ = select([server], [], [])
            content = readable[0].recv(buffer_size).decode()
            if content == '<DONE>': 
                server.send('<DONE>'.encode())
                break
            sys_info += content
        sys_info_list: list[str] = sys_info.split('\n')
        lines: int = 10 if len(MESSAGE) == 1 else int(MESSAGE[1])
        with open(os.path.join(cwd, 'client_requests_data', 'results', client_files_id+'_info_'+'.txt'), 'w') as file:
            for x in range(lines): print(sys_info_list[x], sep='\n', file=file) 

    if 'ts' == auto_message[0] or 'tt' == auto_message[0]:
        infile_name: str = auto_message[1]
        outfile_name: str = auto_message[2]
        file_size: int = os.path.getsize(infile_name)
        print('in file_size: ', file_size, os.path.exists(infile_name))
        server.recv(buffer_size)
        server.send(f"{file_size}".encode())
        server.recv(buffer_size)
        with open(infile_name, 'rb') as file:
            total_bytes_read: int = 0
            while total_bytes_read < file_size:
                bytes_read = file.read(buffer_size)
                total_bytes_read += len(bytes_read)
                server.send(bytes_read)

        # Receive out file
        MESSAGE = server.recv(buffer_size)
        str_msg = MESSAGE.decode().strip('<>').split('|')
        
        if 'CONT' == str_msg[0]: 
            server.send('<TRANSFER>'.encode())
            with open(outfile_name, "wb") as file:
                total_bytes_read: int = 0
                file_size = int(str_msg[1])
                while total_bytes_read < file_size: 
                    bytes_read = server.recv(buffer_size)
                    total_bytes_read += len(bytes_read)
                    file.write(bytes_read)
                server.send('<DONE>'.encode())
    elif 'exit' == auto_message[0]: break
server.close()