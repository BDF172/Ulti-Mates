import random, string, traceback

with open("Temporary_work\\.security", "r") as f:
    fix_token = f.read()

def generate_token() -> str:
    """Generate a random token."""
    return ''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(128))


def encrypt_message(message: str, token: str) -> bytearray:
    """
    Encrypt <message> with <token>
    -
    Encrypt a message with a token.
    return false if an error occured
    """
    try :
        binary_message = message.encode()
        binary_token = token.encode()
        
        encrypted_message = bytearray()

        for i in range(len(binary_message)):
            encrypted_message.append(binary_message[i] ^ binary_token[0 - i % len(binary_token)])

        return encrypted_message
    
    except Exception as e:
        print("/!\ Error while encrypting message /!\ \n")
        print(traceback.format_exc())
        return False


def decrypt_message(encrypted_message: bytearray, token: str) -> str:
    """
    Decrypt <encrypted_message> with <token>
    -
    Decrypt a message with a token.
    return false if an error occured
    """
    try :
        binary_token = token.encode()
        decrypted_message = bytearray()

        for i in range(len(encrypted_message)):
            decrypted_message.append(encrypted_message[i] ^ binary_token[0 - i % len(binary_token)])

        return decrypted_message.decode()
    
    except Exception as e:
        print("/!\ Error while decrypting message /!\ \n")
        print(traceback.format_exc())
        return False