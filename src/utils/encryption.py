import os
from cryptography.fernet import Fernet
# Get encryption key from the enviroment
encryption_key = os.getenv("ENCRYPTION_KEY")
# Ensure the encryption key is present
if not encryption_key:
    raise ValueError("ENCRYPTION_KEY not found in enviroment!")

# Initializes the Fernet instance with the encryption key
fernet = Fernet(encryption_key.encode())

# Function to encrypt the sensitive tokens
def encrypt(value: str) -> str:
    if value is None:
        return None
    return fernet.encrypt(value.encode()).decode()

# Function to decrypt the sensitive tokens
def decrypt(value: str) -> str:
    if value is None:
        return None
    return fernet.decrypt(value.encode()).decode()
