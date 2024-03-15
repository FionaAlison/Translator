import fcntl
import tempfile
from meta_data import *
from os import O_NONBLOCK
from os.path import join, getsize
from sys import stdin, stderr
from subprocess import run
from socket import socket
from socketserver import BaseServer, ThreadingTCPServer, BaseRequestHandler
from selectors import PollSelector, EVENT_READ
from typing import Any
from functionalities.pegassusSUM import TextSummariser
from googletrans import Translator

class CP_RequestHandler(BaseRequestHandler):

    users_files_path = join(cwd, 'users_files')
    translator = Translator()

    menu: str = """EC2 Server instance
        1. Command: "info [lines]" to get information about the server
        2. Commnad: (text sumarisation [.txt, .png, .jpg, .jpeg]) "ts [input_file] [output_file]"
        3. Commnad: (text translation  [.txt, .png, .jpg, .jpeg]) "tt [input_file] [output_file] [LANG_ID]"
        4. Command: "exit" to exit\n"""

    def __init__(self, request: socket, client_address: Any, server: BaseServer) -> None:
        self.user_folder: tempfile.TemporaryDirectory
        self.unknown_command_message: bool = False
        self.last_message: str = ''
        super().__init__(request, client_address, server)

    def setup(self) -> None: # prepare files and directorie
        self.user_folder = tempfile.TemporaryDirectory(suffix=None, 
                                                       prefix=f'user_fd:{self.request.fileno()}_', 
                                                       dir=CP_RequestHandler.users_files_path, 
                                                       ignore_cleanup_errors=True)
    
    def handle(self) -> None: # handle communication and requests
        # add auto delete mechanism for space TODO
        message: str = ''
        while True: 
            if self.unknown_command_message:
                self.request.send(f'\nUnknown command: {self.last_message}\n\n{CP_RequestHandler.menu}'.encode())
                self.unknown_command_message = False
            else: 
                self.request.send(CP_RequestHandler.menu.encode())
            message = self.request.recv(buffer_size).decode().split(' ')
            if 'info' == message[0]:
                with tempfile.NamedTemporaryFile(dir=join(CP_RequestHandler.users_files_path, self.users_files_path), mode='w+b') as info_file:
                    run(['top', '-n', '1', '-b'], stdout=info_file, text=True) # linux
                    # run(['top', '-l', '1'], stdout=info_file, text=True) # mac
                    info_file.seek(0)
                    content: bytes = info_file.read()
                    transfers: int = len(content)//buffer_size
                    chunk: int = 0
                    for _ in range(transfers-1):
                        self.request.send(content[buffer_size*chunk:buffer_size*(chunk+1)])
                        chunk += 1
                self.request.send('<DONE>'.encode())
                self.request.recv(buffer_size)
                continue
            if 'ts' == message[0] or 'tt' == message[0]:
                # Transfer input file
                commnad: str = message[0]
                infile_name: str = message[1]
                outfile_name: str = message[2]
                infile_path: str = join(CP_RequestHandler.users_files_path, self.user_folder.name, infile_name)
                outfile_path: str = join(CP_RequestHandler.users_files_path, self.user_folder.name, outfile_name)
                lang_param: str | None = None if len(message) == 3 else message[3]
                self.request.send('<BEGIN>'.encode())
                message = self.request.recv(buffer_size).decode()
                file_size: int = int(message)
                self.request.send(f'<TRANSFER>'.encode())
                with open(infile_path, "wb") as file:
                    total_bytes_read: int = 0
                    while total_bytes_read < file_size: 
                        bytes_read = self.request.recv(buffer_size)
                        total_bytes_read += len(bytes_read)
                        file.write(bytes_read)

                # Compute
                succesful: bool = False
                if '.txt' == infile_name[-4:]:
                    if 'ts' == commnad:
                        succesful = True
                        with open(outfile_path, 'wb') as outfile:
                            with open(infile_path, 'r') as infile:
                                outfile.write(TextSummariser.request(infile.read()).encode()) # add a flag for length
                    else:
                        if lang_param is not None:
                            succesful = True
                            try:
                                with open(outfile_path, 'wb') as outfile:
                                    with open(infile_path, 'r') as infile:
                                        outfile.write(CP_RequestHandler.translator.translate(infile.read(), dest=lang_param).text.encode())
                            except:
                                succesful = False
                elif '.png' or '.txt' or '.jpg': 
                    tesseract_file: str = join(CP_RequestHandler.users_files_path, self.user_folder.name, 'tesseract_tempfile')
                    run(['tesseract', infile_path, tesseract_file], stdout=stderr, text=True)
                    if 'ts' == commnad:
                        succesful = True
                        with open(tesseract_file+'.txt', 'r') as infile:
                            with open(outfile_path, 'wb') as outfile:
                                outfile.write(TextSummariser.request(infile.read()).encode()) # add a flag for length
                        run(['rm', tesseract_file+'.txt'], text=False)
                        run(['rm', infile_path], text=True)
                    else: 
                        if lang_param is not None:
                            succesful = True
                            try: 
                                with open(tesseract_file+'.txt', 'r') as infile:
                                    with open(outfile_path, 'wb') as outfile:
                                        outfile.write(CP_RequestHandler.translator.translate(infile.read(), dest=lang_param).text.encode())
                                run(['rm', tesseract_file+'.txt'], text=False)  
                                run(['rm', infile_path], text=True)
                            except:
                                succesful = False

                # Sync
                if succesful: 
                    file_size = getsize(outfile_path)
                    self.request.send(f'<CONT|{file_size}>'.encode())
                
                # Send file output file back
                    self.request.recv(buffer_size)
                    with open(outfile_path, 'rb') as file:
                        total_bytes_read: int = 0
                        while total_bytes_read < file_size:
                            bytes_read = file.read(buffer_size)
                            total_bytes_read += len(bytes_read)
                            self.request.send(bytes_read)
                    self.request.recv(buffer_size)
                    run(['rm', outfile_path], text=True)
                else: 
                    self.request.send('ABORT'.encode())
                continue
            if 'exit' == message[0]: break
            self.last_message = ''.join(message)
            self.unknown_command_message = True
    
    def finish(self) -> None: # delete all files from session
        self.user_folder.cleanup()

class CP_Server(ThreadingTCPServer):

    def __init__(self, server_address: str, RequestHandlerClass: BaseRequestHandler, bind_and_activate: bool = True) -> None:
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)
        self.selector = PollSelector()
        self.shut_down_req: bool = False
        self.active_clients: int = 0
        self.time_offset = 6
        self.active_clients_timeoffset: int = self.time_offset
        return

    def run(self, timeout: float):
        print('Server running:...\n(exit) to exit server\n')
        try:
            self.selector.register(self, EVENT_READ)
            self.selector.register(stdin, EVENT_READ)
            while not self.shut_down_req:
                fd_ready = self.selector.select(timeout=timeout)
                if self.active_clients_timeoffset == 0 : 
                    print('active clients: ', self.active_clients)
                    self.active_clients_timeoffset = self.time_offset
                else: self.active_clients_timeoffset -= 1
                if self.shut_down_req: break
                if fd_ready: 
                    if fd_ready[0][0].fd == 0:
                        if 'exit' in stdin.read(): 
                            self.shut_down_req = True; 
                            print('-- Stopping Server --')
                    else:
                        print('client on fd: ', fd_ready[0][0].fd, end='\n')
                        self.active_clients += 1
                        self.handle_request_noblocking()
                self.service_actions()

            self.selector.unregister(self)
            self.selector.unregister(stdin)
            self.server_close()
        finally:
            self.shut_down_req = False
    
    def handle_request_noblocking(self):
        try: 
            client_sock, client_addr = self.get_request() # accept the connection
        except OSError: 
            return
        if self.verify_request(client_sock, client_addr):
            try:
                self.process_request(client_sock, client_addr)
            except Exception:
                self.handle_error(client_sock, client_addr)
                self.shut_down_req = True
            except:
                self.shut_down_req = True
                raise
        else: pass

    def process_request_thread(self, request: socket | tuple[bytes, socket], client_address: Any) -> None:
        super().process_request_thread(request, client_address)
        self.active_clients -= 1
        return
    
    def verify_request(self, request: socket | tuple[bytes, socket], client_address: Any) -> bool:
        return super().verify_request(request, client_address)
    
    def handle_error(self, request: socket | tuple[bytes, socket], client_address: Any) -> None:
        self.close_request(request)
        return super().handle_error(request, client_address)
    
    def server_close(self) -> None:
        return super().server_close()

orig_fl = fcntl.fcntl(stdin, fcntl.F_GETFL)
fcntl.fcntl(stdin, fcntl.F_SETFL, orig_fl | O_NONBLOCK)

cpserver: CP_Server = CP_Server((host, port), CP_RequestHandler, True)
cpserver.run(0.5)