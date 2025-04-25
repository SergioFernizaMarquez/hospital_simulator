# utils/encryption.py

from cryptography.fernet import Fernet
import os

# Path to the key file (you can customize this)
KEY_PATH = os.path.join(os.path.dirname(__file__), 'secret.key')

def generate_key():
    """Generates a new encryption key and saves it to a file."""
    key = Fernet.generate_key()
    with open(KEY_PATH, 'wb') as key_file:
        key_file.write(key)

def load_key():
    """Loads the encryption key from file, or generates one if it doesn't exist."""
    if not os.path.exists(KEY_PATH):
        generate_key()
    with open(KEY_PATH, 'rb') as key_file:
        return key_file.read()

# Initialize the cipher using the key
cipher = Fernet(load_key())

def encrypt_data(data: str) -> bytes:
    """Encrypts a string and returns encrypted bytes."""
    return cipher.encrypt(data.encode())

def decrypt_data(token: bytes) -> str:
    """Decrypts previously encrypted bytes and returns the original string."""
    return cipher.decrypt(token).decode()
