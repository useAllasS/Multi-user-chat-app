from cryptography.fernet import Fernet


def generate_key():
    return Fernet.generate_key()


def encrypt_message(key, message):
    cipher = Fernet(key)
    encrypted_message = cipher.encrypt(message.encode('utf-8'))
    return encrypted_message


def decrypt_message(key, encrypted_message):
    cipher = Fernet(key)
    decrypted_message = cipher.decrypt(encrypted_message).decode('utf-8')
    return decrypted_message
