import socket, threading, sqlite3

class Client :
    def __init__(self,conn,addr,user) :
        self.user = user
        self.conn = conn
        self.addr = addr
        self.connected = True

    def username(self) :
        return str(self.user)
    
    def address(self) :
        return self.addr

    def connection(self) :
        return self.conn

    def connection_status(self) :
        return self.connected

    def disconnect(self) :
        self.connected = False

clients = []
path_db='/home/freebox/server/users.db'

"""
---------TO DO---------

- load and save data from and to a SQL database
    - user ; id ; pseudo ; table = entites

- python only dict 
    - {pseudo: IPv4}
    
-
-
-
-

"""

commandes = ["/msg", "/users", "/help"]
users_ip = {}

def load_user_name(client):
    """
    find a user by name
    code 1 = found
    code 0 = inexistant 
    """
    temp_db = sqlite3.connect(path_db)
    temp_cur=temp_db.cursor()
    print("👉 |checking user name")
    temp_cur.execute("SELECT COUNT(user) FROM entite WHERE user='"+client.username()+"';")
    res = temp_cur.fetchall()[0][0] == 1
    temp_db.close()
    return res

def broadcast(message, client):
    """
    Envoie un message à tous les clients, sauf à l'expéditeur.
    """
    for user in clients:
        if user != client:
            user.connection().send((f" {message}").encode())
    #############################################
    ############INSERTION PSEUDO#################
    #############################################

def first_connection(client,attempts=0) :
    try :
        if attempts==2 :
            client.connection().send("Vous avez fait trop d'erreurs, vous allez être déconnecté(e).".encode())
            return False
        temp_db=sqlite3.connect(path_db)
        temp_cur=temp_db.cursor()
        if load_user_name(client) == True :
            client.connection().send(("Quel est votre mot de passe ?").encode())
            password = client.connection().recv(1024).decode()
            temp_cur.execute(f"SELECT COUNT(*) FROM entite WHERE user='{client.username()}' AND password='{password}';")
            if temp_cur.fetchall()[0][0]==1 :
                client.connection().send("Vous êtes connecté(e) !".encode())
                temp_db.close()
                return True
            else :
                client.connection().send(f"Vous avez {attempts} mauvaise(s) tentative(s), veuillez recommencer".encode())
                temp_db.close()
                return first_connection(client, attempts+1)

        else :
            temp_db.close()
            if create_user(client) :
                client.connection().send("Vous êtes connecté(e) !".encode())
                return True
            else:
                print("Il y a eu un problème dans la création du compte")
    except :
        return False

def create_user(client) :
    """
    -----------
    Description
    -----------
        Crée un utilisateur.
    
    -------
    Entrees
    -------
        user : str, nom d'utilisateur entré
        cur : variable curseur issue de la base de données utilisée
        conn,addr : variables socket permettant de connaître le destinataire

    ------
    Sortie
    ------
        bool : vient vérifier que la création de compte est un succès.

    """
    count = 0
    while True :
        try :
            client.connection().send(("Vous n'existez pas dans notre base de données, entrez le mot de passe souhaité :").encode())
            data = client.connection().recv(1024)
            if not data:
                return False
            message = data.decode()
            psw1 = str(message)
            client.connection().send(("Confirmez votre saisie :").encode())
            data = client.connection().recv(1024)
            if not data:
                return False
            message=data.decode()
            psw2 = message

            if(count>=2) :
                client.connection().send(("Vous avez essayé 3 fois, veuillez recommencer plus tard.").encode())
                return False

            elif psw1==psw2 and count < 3 :
                try :
                    temp_db=sqlite3.connect(path_db)
                    temp_cur=temp_db.cursor()
                    temp_cur.execute("INSERT INTO entite (user,password) VALUES ('"+client.username()+"','"+psw1+"');")
                    temp_db.commit()
                    print(f"L'utilisateur {client.username()} vient d'être ajouté à la base de données.")
                    temp_db.close()
                    return True
                except :
                    print(f"Un problème est survenu lors de la création du compte pour l'utilisateur {client.username()}")
                    return False
        
            else :
                message = "Vos mots de passes ne correspondent pas, veuillez recommencer."
                count+=1
                client.connection().send(message.encode())
        except :
            return False

def receiver_is_online(username) :
    for client in clients :
        if client.username()==username :
            return client
    return False

def tell(message, client):
    """
    Envoie un message a un client specifique
    """
    message = message.replace("/msg","").split(" ")
    receiver_username = message[1]
    receiver = receiver_is_online(receiver_username)
    message = " ".join(message[2:])

    if receiver != False:
        receiver.connection().send((f"{str(client.username())} -> me : {message}").encode())
        client.connection().send((f"me -> {str(receiver.username())} : {message}").encode())
    else:
        client.connection().send((f"X User {receiver_username} not found X").encode())


def help():
    return "________________________________________________________\n|- /users : liste des utilisateurs connecté\n|- /msg <username> <message> : envoyer un message privé\n|- /help : afficher ce message\n\________________________________________________________"
    
def leave(conn) :
    try :
        conn.send("Vous êtes sur le point de vous déconnecter, en êtes-vous sûr (oui/non) ?".encode())
        message=conn.recv(1024).decode()
        if message not in ["oui","non"] :
            conn.send("Nous n'avons pas compris votre requête.".encode())
            return leave(conn)
        elif message == "oui" :
            conn.send("Vous allez être déconnecté".encode())
            return True
        else :
            return False
    except :
        return False

def online_users(client) :
    user_list = []
    for user in clients :
        if user != client :
            user_list.append(user.username())
    return ",".join(user_list)
    

def handle_client(conn, addr):
    """
    Fonction pour gérer les connexions entrantes des clients
    """
    print(f"🌐 | New connection from {addr}")
    #############################################
    ############INSERTION PSEUDO#################
    #############################################
    try :
        conn.send(("Vous venez de vous connectez à notre serveur, entrez votre nom ou un pseudonyme").encode())
        user = conn.recv(1024)
    except :
        conn.close()
        return None
    if not user :
        conn.close()
        return None
    client=Client(conn, addr, user.decode())
    clients.append(client)
    if not first_connection(client) :
        print(f"L'utilisateur {client.username()} venant de l'adresse IP {client.address()} a échoué sa connexion.")
        client.disconnect()
    if client.connection_status() :
        print(f"L'utilisateur {client.username()} a réussi sa connexion sur l'adresse IP {client.address()}.")
        broadcast("👉 | New connection from "+str(client.username()), client)
        client.connection().send("Si vous ne connaissez pas les commandes habituelles, entrez '/help' pour les voir !".encode())
    while client.connection_status():
        try:
            data = client.connection().recv(1024)
            if not data:
                break
            message = data.decode()

            print(f"📳 | {client.username()},Received message: {message}")

            if message.startswith("/msg"):
                tell(message, client)

            elif message.startswith("/users"):
                client.connection().send(("Les utilisateurs en ligne sont : \n "+str(online_users(client))).encode())

            elif message.startswith("/help"):
                client.connection().send(help().encode())
            
            elif message.startswith("/whoami") :
                client.connection().send(client.username().encode())

            elif message.startswith("/exit") :
                if leave(client) :
                    client.disconnect()
                
            elif message.startswith("/") :
                client.connection().send("La commande que vous avez entré est invalide".encode())

            else:
                entete=f"Message venant de {client.username()} : \n "
                broadcast(entete+message, client)
        except:
            client.disconnect()
    try :
        print(f"📴 | Closing connection from {client.address()}")
        clients.remove(client)
        
    except :
        connected = False
        clients.remove(conn)
        conn.close()
        print(f"📴 | Connection closed from {addr}")

def start_server():
    """
    Fonction pour démarrer le serveur et écouter les connexions entrantes
    """
    # Configuration du serveur
    HOST = '192.168.1.83'
    PORT = 4444

    # Créer un socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))

    # Ecouter les connexions entrantes
    server.listen(1)

    print(f"👉 | [EN ECOUTE] Le serveur écoute sur {HOST}:{PORT}.")

    while True:
        # Accepter les connexions entrantes
        conn, addr = server.accept()

        # Créer un thread pour gérer la connexion entrante
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

        # Afficher le nombre de threads actifs
        print(f"👉 | [ACTIF] {threading.activeCount() - 1} connexions actives.")

start_server()