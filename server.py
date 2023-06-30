import socket
import threading
from datetime import datetime
import logging

# Set up logging configuration
logging.basicConfig(filename='server.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class ChatServer:
    clients_list = []
    usernames = {}
    last_received_message = ""

    def __init__(self):
        self.server_socket = None
        self.create_listening_server()

    def create_listening_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        local_ip = '127.0.0.1'
        local_port = 10318
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((local_ip, local_port))
        print("Listening for incoming messages...")
        self.server_socket.listen(5)
        self.receive_messages_in_a_new_thread()
        logging.info("Listening for incoming messages...")

    def receive_messages(self, client_socket):
        while True:
            incoming_buffer = client_socket.recv(256)
            if not incoming_buffer:
                break
            self.last_received_message = incoming_buffer.decode('utf-8')

            if self.last_received_message.startswith('joined:'):
                self.handle_new_client(client_socket)
            elif self.last_received_message.startswith('private:'):
                self.send_private_message(client_socket)
            elif self.last_received_message.startswith('users'):
                self.send_connected_users(client_socket)
            else:
                self.broadcast_to_all_clients(client_socket)

        self.remove_client(client_socket)
        logging.info("Received message: %s", self.last_received_message)

    def handle_new_client(self, client_socket):
        username = self.last_received_message.split(':')[1]
        self.usernames[client_socket] = username
        self.add_to_clients_list(client_socket)
        self.broadcast_to_all_clients(client_socket, f"{username} joined")
        logging.info("%s joined", username)

    def remove_client(self, client_socket):
        if client_socket in self.clients_list:
            username = self.usernames[client_socket]
            self.clients_list.remove(client_socket)
            del self.usernames[client_socket]
            self.broadcast_to_all_clients(client_socket, f"{username} left")
            client_socket.close()
        logging.info("%s left", username)

    def broadcast_to_all_clients(self, sender_socket, message=None):
        for client_socket in self.clients_list:
            if client_socket is not sender_socket:
                if message:
                    client_socket.sendall((f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}").encode('utf-8'))
                else:
                    client_socket.sendall((f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {self.last_received_message}").encode('utf-8'))
        logging.info("Broadcast message: %s", message)

    def send_private_message(self, sender_socket):
        recipient, message = self.last_received_message.split(':', 2)[1:]
        recipient = recipient.strip()
        message = message.strip()
        if recipient and message:
            for client_socket, username in self.usernames.items():
                if client_socket != sender_socket and username == recipient:
                    client_socket.sendall((f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Private message from {self.usernames[sender_socket]}: {message}").encode('utf-8'))
                    break
        logging.info("Private message from %s to %s: %s", self.usernames[sender_socket], username, message)

    def send_connected_users(self, client_socket):
        usernames = ', '.join(self.usernames.values())
        client_socket.sendall((f"Connected users: {usernames}").encode('utf-8'))
        logging.info("Sent connected users: %s", usernames)

    def receive_messages_in_a_new_thread(self):
        while True:
            client_socket, client_address = self.server_socket.accept()
            print('Connected to', client_address[0], ':', str(client_address[1]))
            t = threading.Thread(target=self.receive_messages, args=(client_socket,))
            t.start()
        logging.info("Connected to %s:%s", client_address[0], client_address[1])

    def add_to_clients_list(self, client_socket):
        if client_socket not in self.clients_list:
            self.clients_list.append(client_socket)
        logging.info("Added client: %s", client_socket)


if __name__ == "__main__":
    logging.info("Starting the chat server...")
    ChatServer()
