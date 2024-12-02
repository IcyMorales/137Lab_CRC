import socket
import threading
import tkinter as tk
import crcModule as crcM
from tkinter import scrolledtext

class ChatServer:
    def __init__(self, port, key, server_name, client_max):
        self.port = port
        self.key = key
        self.server_name = server_name
        self.max_client = client_max

        self.clients = []                                               # make list of clients
        self.running = True                                             # enable running state
		
        # Initialize the GUI (and set title)
        self.root = tk.Tk()
        self.root.title(f"{server_name} | KEY:{key}")

        # Chat display area
        self.chat_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state='disabled', width=100, height=20)
        self.chat_area.grid(column=0, row=0, padx=10, pady=10, columnspan=2)

        # Message entry box
        self.message_entry = tk.Entry(self.root, width=40)
        self.message_entry.grid(column=0, row=1, padx=10, pady=10)
        self.message_entry.bind("<Return>", self.send_message)

        # Send button
        self.send_button = tk.Button(self.root, text="Send", command=self.send_message)
        self.send_button.grid(column=1, row=1)

        # Exit button
        self.exit_button = tk.Button(self.root, text="Exit", command=self.exit_chat)
        self.exit_button.grid(column=0, row=2, padx=10, pady=10, columnspan=2)

        # Start a thread to receive messages
        #self.start_server()                                            # if not run in a thread (when this is un-commented), this loops and prevents the GUI from opening
        receive_thread = threading.Thread(target=self.start_server)     # run start_server in a thread
        receive_thread.start()

        # Set the window's "X" to exit_chat() method
        self.root.protocol("WM_DELETE_WINDOW", self.exit_chat)
		
        # Start the GUI main loop
        self.root.mainloop()
    
    def start_server(self):
        self.display_message("\n")
        self.display_message("#########################################################################")
        self.display_message("####           Chat Server Started! Waiting for clients...           ####")
        self.display_message("#########################################################################")
        self.display_message("\n")
        
        host = socket.gethostname()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)	# using IPv4 and TCP
        self.server_socket.bind((host, self.port))                              # set address and custom port
        self.server_socket.listen(self.max_client)                              # set how many clients can connect concurrently
    
        self.display_message(f"Server listening on {host} | {socket.gethostbyname(host)}:{self.port}")
        self.display_message(f"KEY is {self.key}")
    
        while self.running:
            client_socket, client_address = self.server_socket.accept()
            self.clients.append(client_socket)
            client_name, client_key = client_socket.recv(1024).decode().split("|")
            self.display_message(f"Client [{client_address}|{client_name}] connected.\n")
            connectFlAG = True

            if self.key != client_key:
                connectFlAG = False
                client_socket.send("You entered the wrong KEY. Please disconnect and reconnect with the correct KEY.\n".encode())                                   # tell client to reconnect
                self.display_message(f"Client [{client_name}] entered the wrong KEY:{client_key}. They need to disconnect and reconnect with the correct KEY.\n")   # display error on server GUI
                crcMessage = crcM.getCRCMsg(f"[{client_name}] entered the chat with [key error].\n", self.key)                                                                                                                    
                self.broadcast_message(crcMessage, client_socket)
            else:                                                                              # Same as send_message() | tell the others the client entered normally
                crcMessage = crcM.getCRCMsg(f"[{client_name}] has entered the chat.\n", self.key)                                                                                                            
                self.broadcast_message(crcMessage, client_socket)
            
            # Start a new thread for each client
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address, client_name, connectFlAG))
            client_thread.start()

    def handle_client(self, client_socket, client_address, client_name, connectFlAG=True):
        if (connectFlAG): client_socket.send(f"Welcome to {self.server_name}! Type 'exit' (or press it) to leave.".encode())    # ONLY send if KEY is correct. (also fixed missing "f" from v1)
        try:
            while self.running:
                # Receive message from client
                binaryWithCRC = client_socket.recv(1024).decode()

                if binaryWithCRC.lower() == 'exit':
                    crcMessage = crcM.getCRCMsg(f"Client [{client_name}] has left the chat.", self.key)   # Same as send_message() but without corruption
                    self.broadcast_message(crcMessage, client_socket)
                    self.display_message(f"Client [{client_address}|{client_name}] disconnected.")
                    # Close exiting client (not in v1)
                    for client in self.clients:
                        if client==client_socket:
                            client.close()
                            self.display_message(f"Client [{client_address}] closed.")                                          # display message (to confirm closure)
                            break                                                                                               # stop loop

                if int(crcM.getCRC(binaryWithCRC,key)) == 0:                                # if Mod 2 Division returns a 0, accept message
                    message = crcM.toText(binaryWithCRC[:-(len(key)-1)])                    # convert binary (w/ CRC removed) back to Text
                    self.display_message(f"[{client_name}] {message}")
                    # Broadcast the accepted message to other clients
                    crcMessage = crcM.getCRCMsg(f"[{client_name}]: {message}", self.key)   # Same as send_message() but without corruption
                    self.broadcast_message(crcMessage, client_socket)

                else:
                    self.display_message(f"[CRC ERROR | Received corrupted message data from {client_name}]")  # discard message and inform user regarding corruption
                    self.broadcast_message(binaryWithCRC, client_socket)

        except ConnectionResetError:
            crcMessage = crcM.getCRCMsg(f"Client [{client_address}|{client_name}] disconnected abruptly.", self.key)   # Same as send_message() but without corruption
            self.broadcast_message(crcMessage, client_socket)
            self.display_message(f"Client [{client_address}|{client_name}] disconnected abruptly.")
        finally:
            # Remove the client from the client list and close the connection
            self.clients.remove(client_socket)
            client_socket.close()
    
    def broadcast_message(self, message, sender_socket=None):
        for client in self.clients:
            if client != sender_socket:  # Don't send the message back to the sender
                client.send(message.encode())

    def send_message(self, event=None):
        message = self.message_entry.get()
        crcMessage = crcM.getCRCMsg(f"server[{self.server_name}]: {message}", self.key)   # Same as send_message() but without corruption
        if message:
            # Send the message to the clients
            self.broadcast_message(crcMessage)
            # Display the sent message in the chat area
            self.display_message("You: " + message)
            # Clear the message entry box
            self.message_entry.delete(0, tk.END)
            # Exit if the message is "exit"
            if message.lower() == 'exit':
                self.exit_chat()

    def display_message(self, message):
        self.chat_area.configure(state='normal')        # set to "normal" from the default "disabled"
        self.chat_area.insert(tk.END, message + "\n")   # insert message (w/ new line) to the end of the last message
        self.chat_area.configure(state='disabled')      # set back to "disabled" to prevent editing
        self.chat_area.see(tk.END)                      # move to the bottom to see the latest message

    def exit_chat(self):
        self.running = False            # disable running state
        for client in self.clients:     # close all clients in list
            client.close()
        self.server_socket.close()      # close server socket
        self.root.destroy()


if __name__ == "__main__":
    port = int(input("Enter port: "))
    key = input("Enter KEY (Generator polynomial binary): ")                # string instead of integer (makes things simpler since the division will be in string anyway)
    server_name = input("Enter server name: ")
    client_max = int(input("Enter max number of concurrent clients: "))
    ChatServer(port, key, server_name, client_max)
    