import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget, QMessageBox
from PyQt5.QtCore import Qt
import socket
import threading
from datetime import datetime
import logging

# Set up logging configuration
logging.basicConfig(filename='client.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Add logging statements in the client code

class GUI(QMainWindow):
    client_socket = None
    last_received_message = None

    def __init__(self):
        super().__init__()
        self.chat_transcript_area = None
        self.name_widget = None
        self.enter_text_widget = None
        self.join_button = None
        self.initialize_socket()
        self.initialize_gui()
        self.listen_for_incoming_messages_in_a_thread()
        logging.info("Client connected to server")

    def initialize_socket(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote_ip = '127.0.0.1'
        remote_port = 10318
        self.client_socket.connect((remote_ip, remote_port))

    def initialize_gui(self):
        self.setWindowTitle("Socket Chat")
        self.setFixedSize(500, 400)
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        label = QLabel("Enter your name:", self)
        layout.addWidget(label)

        self.name_widget = QLineEdit(self)
        layout.addWidget(self.name_widget)

        self.join_button = QPushButton("Join", self)
        layout.addWidget(self.join_button)
        self.join_button.clicked.connect(self.on_join)

        self.chat_transcript_area = QTextEdit(self)
        self.chat_transcript_area.setReadOnly(True)
        layout.addWidget(self.chat_transcript_area)

        label = QLabel("Enter message:", self)
        layout.addWidget(label)

        self.enter_text_widget = QLineEdit(self)
        layout.addWidget(self.enter_text_widget)
        self.enter_text_widget.returnPressed.connect(self.on_enter_key_pressed)

    def listen_for_incoming_messages_in_a_thread(self):
        thread = threading.Thread(target=self.receive_message_from_server, args=(self.client_socket,))
        thread.start()

    def receive_message_from_server(self, client_socket):
        while True:
            buffer = client_socket.recv(256)
            if not buffer:
                break
            message = buffer.decode('utf-8')

            if "joined" in message:
                split_message = message.split(":")
                if len(split_message) >= 2:
                    user = split_message[1]
                    if user == self.name_widget.text():
                        joined_message = "You joined the server"
                    else:
                        joined_message = user + " joined"
                    self.chat_transcript_area.append(joined_message)
            elif "Private message" in message:
                self.chat_transcript_area.append(message)
            else:
                self.chat_transcript_area.append(message)

        client_socket.close()

    def on_join(self):
        if len(self.name_widget.text()) == 0:
            QMessageBox.critical(self, "Enter your name", "Enter your name to send a message")
            return
        self.name_widget.setEnabled(False)
        self.client_socket.send(("joined:" + self.name_widget.text()).encode('utf-8'))
        logging.info("Joined the server")

    def on_enter_key_pressed(self):
        if len(self.name_widget.text()) == 0:
            QMessageBox.critical(self, "Enter your name", "Enter your name to send a message")
            return

        message = self.enter_text_widget.text().strip()

        if message.startswith('/'):
            self.parse_command(message)
        else:
            self.send_chat()

        self.enter_text_widget.clear()

    def parse_command(self, message):
        command_parts = message[1:].split(' ', 1)
        command = command_parts[0].lower()

        if command == 'help':
            self.display_help()
        elif command == 'users':
            self.display_connected_users()
        elif command == 'private':
            if len(command_parts) == 2:
                self.send_private_message(command_parts[1])
            else:
                self.display_error_message("Usage: /private <recipient>: <message>")
        else:
            self.display_error_message("Invalid command. Type /help for available commands")

    def display_help(self):
        help_message = """
        Available Commands:
        /help - Show available commands
        /users - Show connected users
        /private <recipient>: <message> - Send a private message to a specific user
        """
        self.chat_transcript_area.append(help_message)

    def display_connected_users(self):
        self.chat_transcript_area.append("Fetching connected users...")

        # Request server to broadcast connected users
        self.client_socket.send("users".encode('utf-8'))

    def send_private_message(self, message):
        self.client_socket.send(("private:" + message).encode('utf-8'))

    def send_chat(self):
        self.client_socket.send(self.enter_text_widget.text().encode('utf-8'))

    def display_error_message(self, error_message):
        self.chat_transcript_area.append("Error: " + error_message)


if __name__ == '__main__':
    logging.info("Starting the chat client...")
    app = QApplication(sys.argv)
    window = GUI()
    window.show()
    sys.exit(app.exec_())
