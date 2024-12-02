import socket
import threading
import tkinter as tk
import crcModule as crcM
from tkinter import scrolledtext

class ChatClient:
    def __init__(self, host, port, key, name):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # using IPv4 and TCP
        self.client_socket.connect((host, port))                                # set custom address
        self.client_socket.send(f"{name}|{key}".encode())                       # send first message as the name and key (the server always sets the first message as the name and key)
        
        self.key = key
        self.running = True                                                     # enable running state
        
        # Initialize the GUI (and set title)
        self.root = tk.Tk()
        self.root.title(f"{name} | KEY:{key}")

        # Chat display area
        self.chat_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state='disabled', width=50, height=20)
        self.chat_area.grid(column=0, row=0, padx=10, pady=10, columnspan=2)

        # Message entry box
        self.message_entry = tk.Entry(self.root, width=40)
        self.message_entry.grid(column=0, row=1, padx=10, pady=10)
        self.message_entry.bind("<Return>", self.send_message)                  # call send_message when user presses "Enter" (<Return>) while on the Message entry box

        # Send button
        self.send_button = tk.Button(self.root, text="Send", command=self.send_message)
        self.send_button.grid(column=1, row=1)

        # Exit button
        self.exit_button = tk.Button(self.root, text="Exit", command=self.exit_chat)
        self.exit_button.grid(column=0, row=2, padx=10, pady=10, columnspan=2)

        # Start a thread to receive messages
        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.start()
		
        # Set the window's "X" to exit_chat() method
        self.root.protocol("WM_DELETE_WINDOW", self.exit_chat)
		
        # Start the GUI main loop
        self.root.mainloop()

    def receive_messages(self):
        message = self.client_socket.recv(1024).decode()
        self.display_message(message)

        while self.running:
            try:                                                                # keep looping and receiving messages
                cName, binaryWithCRC = self.client_socket.recv(1024).decode().split("_")
                if binaryWithCRC:
                    if int(crcM.getCRC(binaryWithCRC, key)) == 0:                                # if Mod 2 Division returns a 0, accept message
                        message = crcM.toText(binaryWithCRC[:-(len(key)-1)])                    # convert binary (w/ CRC removed) back to Text
                        self.display_message(f"[{cName}]\n{binaryWithCRC}\nValid: Yes\n  MSG: {message}")                                           # display accepted message
                    else:
                        self.display_message(f"[{cName}]\n{binaryWithCRC}\n[CRC ERROR | Received corrupted message data.]")  # discard message and inform user regarding corruption
                else:
                    break
            except ConnectionAbortedError:                                      # stop loop when connection is lost
                break
            except ConnectionResetError:
                self.running = False
                self.display_message("Connection to server lost.")
                break

    def send_message(self, event=None):
        message = self.message_entry.get()
        crcMessage = crcM.getCRCMsg(message, self.key)
        corruptBIN = crcM.corruptMessage(crcMessage)
        if message:
            # Send the message to the server
            self.client_socket.send(corruptBIN.encode())
            # Display the sent message in the chat area
            self.display_message(f"You: {message}\n{crcMessage}")
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
        self.client_socket.send("exit".encode())        # tell server that you're quitting
        self.running = False                            # disable running state
        self.client_socket.close()                      # close server socket
        self.root.destroy()                             # close tkinter window completely


if __name__ == "__main__":
    host = input("Enter server IP address: ")
    port = int(input("Enter server port: "))
    key = input("Enter server KEY (Generator polynomial binary): ")         # string instead of integer (makes things simpler since the division will be in string anyway)
    name = input("Enter your username: ")
    ChatClient(host, port, key, name)