import socket
import threading

def send_message(sock) :
    while True :
        message = str(input())
        try :
            sock.send(message.encode())
        except :
            print("Impossible d'envoyer le message !")
    
def receive_message(sock) :
    while True :
        try :
            message = sock.recv(1024).decode()
            print(message)
        except :
            print("Une erreur est survenue lors de la dernière réception de message")
            sock.close()
            break

host="91.173.148.254"
#host="127.0.0.1"
port = 24444
sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
sock.connect((host,port))

send_thread = threading.Thread(target=send_message, args=(sock,))
receive_thread = threading.Thread(target=receive_message, args=(sock,))
receive_thread.start()
send_thread.start()


while True :
    send_message(sock)

sock.close()