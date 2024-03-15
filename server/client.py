from meta_data import *
from os.path import getsize, exists
from tqdm import tqdm
from select import select
import socket 
from server.translator_langs import LANGUAGES

MESSAGE: bytes = bytes()
wrong_command_flag: bool = False
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
server.connect((host, port))

def check_for_command_integrity(message: list[str]) -> bool: # [0] tt or ts [1] arg 1 [2] arg 2
    match message[0]:
        case 'info':
            if len(message) > 2: return False
            try: int(message[1]); return True
            except: return False
        case 'ts':
            if len(message) != 3: return False
            if not exists(message[1]): return False
        case 'tt':
            if len(message) != 4: return False
            if not exists(message[1]): return False
            if message[3] not in LANGUAGES.keys(): return False
        case _:
            return True
    return True

while True:
    if not wrong_command_flag: print('\n'+server.recv(buffer_size).decode()) 
    MESSAGE = input('>').strip()
    if not check_for_command_integrity(MESSAGE.split(' ')): wrong_command_flag = True; print('Invalid command! Try again!\n'); continue
    server.send(MESSAGE.encode())
    MESSAGE = MESSAGE.split(' ')
    if 'info' == MESSAGE[0]:
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
        for x in range(lines): print(sys_info_list[x], sep='\n') 

    if 'ts' == MESSAGE[0] or 'tt' == MESSAGE[0]:
        infile_name: str = MESSAGE[1]
        outfile_name: str = MESSAGE[2]
        file_size: int = getsize(infile_name)
        server.recv(buffer_size).decode() # <TS_BEGIN>
        server.send(f"{file_size}".encode())
        print(server.recv(buffer_size).decode())
        process = tqdm(range(file_size), f"Sending {infile_name}", unit='B', unit_scale=True, unit_divisor=buffer_size, leave=True, position=0)
        with open(infile_name, 'rb') as file:
            total_bytes_read: int = 0
            while total_bytes_read < file_size:
                bytes_read = file.read(buffer_size)
                total_bytes_read += len(bytes_read)
                server.send(bytes_read)
                process.update(len(bytes_read))
                process.display()
            process.display()
            process.close()

        # Receive out file
        MESSAGE = server.recv(buffer_size).decode().strip('<>').split('|')
 
        if 'CONT' == MESSAGE[0]: 
            print('<TRANSFER>')
            server.send('<TRANSFER>'.encode())
            with open(outfile_name, "wb") as file:
                total_bytes_read: int = 0
                file_size = int(MESSAGE[1])
                process = tqdm(range(file_size), f"Receiving {outfile_name}", unit='B', unit_scale=True, unit_divisor=buffer_size, position=0, leave=True)
                while total_bytes_read < file_size: 
                    bytes_read = server.recv(buffer_size)
                    total_bytes_read += len(bytes_read)
                    file.write(bytes_read)
                    process.update(len(bytes_read))
                    process.display()
                process.display()
                process.close()
                server.send('<DONE>'.encode())
        else: 
            print('Server error, try again! (Internet connection)')
    elif 'exit' == MESSAGE[0]: break
    wrong_command_flag = False
server.close()