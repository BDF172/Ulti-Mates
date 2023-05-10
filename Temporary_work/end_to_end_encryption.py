import random
import string

fix_token = 'uCTXeITdeSfD421rlVnn9fhPA1a8cvapQ6caY4v6IbsN8f3RAw0peeSjyhV2TfLnvzCD4T7HMQXFnAJN3CRahV1RZmahCEKLgsKAICffjvEYBD9ZAUck9dwwpFpz2k5V'

def generate_token():
    """Generate a random token."""
    return ''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(128))


def encrypt_message(message: str, token: str):
    """
    Encrypt <message> with <token>
    -
    Encrypt a message with a token.
    """
    binary_message = message.encode()
    binary_token = token.encode()
    
    encrypted_message = bytearray()

    for i in range(len(binary_message)):
        encrypted_message.append(binary_message[i] ^ binary_token[0 - i % len(binary_token)])

    return encrypted_message


def decrypt_message(encrypted_message: bytearray, token: str):
    """
    Decrypt <encrypted_message> with <token>
    -
    Decrypt a message with a token.
    """
    binary_token = token.encode()
    decrypted_message = bytearray()

    for i in range(len(encrypted_message)):
        decrypted_message.append(encrypted_message[i] ^ binary_token[0 - i % len(binary_token)])

    return decrypted_message.decode()


def main():
    """Main fonction"""
    token = generate_token()
    sent_token = encrypt_message(token, fix_token)
    message = "Hello world!"

    print("\nMessage: " + message)
    print("\nToken: " + token)
    print(f"Sent token: {sent_token.decode()}\n")

    encrypted_message = encrypt_message(message, decrypt_message(sent_token, fix_token))
    received_token = decrypt_message(sent_token, fix_token)

    print("Received token: " + decrypt_message(sent_token, fix_token))
    print("\nEncrypted message: " + encrypted_message.decode())

    decrypted_message = decrypt_message(encrypted_message, received_token)

    print("Decrypted message: " + decrypted_message)
    print("\nEncryption valid\n" if decrypted_message == message else "\nEncryption failed\n")


# main()
