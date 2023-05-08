import socket, threading, sqlite3

class Client :
    def __init__(self,conn,addr,user) :
        temp_db = sqlite3.connect(path_db)
        temp_cur = temp_db.cursor()
        temp_cur.execute(f"SELECT id FROM entite WHERE user = '{user}';")
        self.db_id = temp_cur.fetchall()[0][0]
        self.user = user
        self.conn = conn
        self.addr = addr
        self.connected = True
        temp_db.close()

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

    def id(self) :
        return self.db_id

    def send(self,message) :
        self.conn.send(message.encode())

    def receive(self) :
        message = self.conn.recv(1024)
        return message.decode()

clients = []
path_db='/home/freebox/server/users.db'

"""
---------TO DO---------
    - Ajouter un système pour les programmeurs qui ouvre une fenêtre et exécute le programme qu'ils viennent de recevoir 
    pour éviter de faire des copiers collers

"""

commandes = ["/msg", "/users", "/help"]
users_ip = {}

def load_user_name(username):
    """
    Permet de savoir si un nom d'utilisateur est déjà pris
    True = found
    False = inexistant 
    """
    temp_db = sqlite3.connect(path_db)
    temp_cur=temp_db.cursor()
    print("👉 |checking user name")
    temp_cur.execute(f"SELECT COUNT(user) FROM entite WHERE user='{username}';")
    res = temp_cur.fetchall()[0][0] == 1
    temp_db.close()
    return res

def get_client_obj(username) :
    """ 
    -----------
    Description
    -----------
        Fonction permettant d'obtenir l'objet de connexion d'un client si il est en ligne, nous permettant de
        lui envoyer des messages.

    -------
    Entrees
    -------
    username :
        str, nom d'utilisateur à rechercher parmis les utilisateurs en ligne
        
    -------
    Sorties
    -------
    Si le client recherché est en ligne :
        client, objet de classe client contenant toutes ses informations importantes
    Sinon :
        False, le client recherché est hors ligne

    """
    for client in clients :
        if client.username() == username :
            return client
    return False

def broadcast(message, client):
    """
    -----------
    Description
    -----------
        Fonction permettant de distribuer un message à tous les utilisateurs en ligne

    -------
    Entrees
    -------
    message :
        str, message à envoyer
    client :
        classe Client, désignant l'instance de connexion du client à l'origine de l'envoi.
    -------
    Sorties
    -------
    """
    for user in clients:
        if user != client:
            user.send((f"Message venant de {client.username()} : \n {message}"))

def first_connection(client,attempts=0) :
    try :
        if attempts==2 :
            client.connection().send("Vous avez fait trop d'erreurs, vous allez être déconnecté(e).".encode())
            return False
        temp_db=sqlite3.connect(path_db)
        temp_cur=temp_db.cursor()
        if load_user_name(client.username()) == True :
            client.connection().send(("Quel est votre mot de passe ?").encode())
            password = client.connection().recv(1024).decode()
            temp_cur.execute(f"SELECT COUNT(*) FROM entite WHERE user='{client.username()}' AND password='{password}';")
            if temp_cur.fetchall()[0][0]==1 :
                client.connection().send("Vous êtes connecté(e) !".encode())
                temp_db.close()
                return True
            else :
                client.connection().send(f"Vous avez {attempts+1} mauvaise(s) tentative(s), veuillez recommencer".encode())
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
            client.send(("Vous n'existez pas dans notre base de données, entrez le mot de passe souhaité :"))
            psw = client.receive(1024)
            client.send(("Confirmez votre saisie :"))
            if(count>=2) :
                client.send(("Vous avez essayé 3 fois, veuillez recommencer plus tard."))
                return False

            elif psw==client.receive() and count < 3 :
                try :
                    temp_db=sqlite3.connect(path_db)
                    temp_cur=temp_db.cursor()
                    temp_cur.execute(f"INSERT INTO entite (user,password) VALUES ('{client.username()}','{psw}');")
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
                client.send(message)
        except :
            return False

def receiver_is_online(username) :
    for client in clients :
        if client.username()==username :
            return client
    return False

def amities(client) :
    temp_db=sqlite3.connect(path_db)
    temp_cur=temp_db.cursor()
    temp_cur.execute(f'select user from entite where id in (select user2 as user from Amities where user1 in (select id from entite where user = "{client.username()}") UNION select user1 as user from Amities where user2 in (select id from entite where user = "{client.username()}"));')
    res = temp_cur.fetchall()
    temp_db.close()
    print(res)
    return res

def requete_amis(client,receiver) :
    print(client.id())
    receiver = " ".join(receiver.split(" "))
    amis = amities(client)
    if amis != [] :
        if receiver in amities(client)[0] :
            client.connection().send(f"Vous êtes déjà ami avec {receiver}")
    if load_user_name(receiver) != False :
        temp_db = sqlite3.connect(path_db)
        temp_cur = temp_db.cursor()
        temp_cur.execute(f"select id from entite where user = '{receiver}';")
        receiver_database_id = str(temp_cur.fetchall()[0][0])
        print(f"insert into Amities (user1,user2) values ({client_database_id},{receiver_database_id});")
        temp_cur.execute(f"insert into Requetes_Amis (sender,receiver) values ({client_database_id},{receiver_database_id});")
        temp_db.commit()
        temp_db.close()
        client.connection().send(f"Votre demande d'ami envers {receiver} a été envoyée !".encode())
    else :
        client.connection().send(f"Le nom d'utilisateur {receiver} n'existe pas.".encode())

def demande_amis(client,message) :
    temp_db = sqlite3.connect(path_db)
    temp_cur = temp_db.cursor()
    temp_cur.execute(f"select req_id,user from Req_Amis join entite on Req_Amis.sender = entite.id where receiver = {client.id()};")
    ans = temp_cur.fetchall()
    if ans != [] :
        for i in range(len(ans)) :
            ans[i] = (str(ans[i][0]),ans[i][1] + "\n")
        print(ans)
        temp_db.close()
        res = []
        for element in ans :
            res.append(element)
        client.connection().send((f"Ces personnes vous ont demandé(e) en ami(e) : \n").encode())
        client.connection().send("<Identifiant demande d'ami> | <Personne à l'origine de la demande>\n".encode())
        client.connection().send("------------------------------------------------------------------\n".encode())
        for i in res :
            client.connection().send((" | ".join(i)).encode())
            client.connection().send("\n".encode())
            return True # Pour indiquer que le client a des demandes d'amis
    else :
        client.send("Vous n'avez aucune nouvelle demande d'amis.")
        return False # Pour indiquer que le client n'a aucune demande d'amis
    
def amities_inbox(client,message) :
    if demande_amis(client,message) :
        client.send("Voulez-vous accepter une demande (oui/non) ?")
        answer = client.receive()
        if answer == "oui" :
            client.send("Quelle est l'identifiant de la demande à accepter ?")
            id = client.receive()
            temp_db = sqlite3.connect(path_db)
            temp_cur = temp_db.cursor()
            temp_cur.execute(f"select count(req_id) from Req_Amis where req_id = {id} and receiver = {client.id()};")
            requete = temp_cur.fetchall()[0][0]
            if requete==1 :
                print(f"insert into Amities (user1,user2) select sender,receiver from Req_Amis where req_id = {id}; delete from Req_Amis where req_id = {id};")
                temp_cur.execute(f"insert into Amities (user1,user2) select sender,receiver from Req_Amis where req_id = {id};")
                temp_cur.execute(f"delete from Req_Amis where req_id = {id};")
                temp_db.commit()
                temp_db.close()
            else :
                client.send("Aucune demande trouvée pour cet identifiant.")
                temp_db.close()
        elif answer == "non" :
            client.send("D'accord, retour aux messages !")
            temp_db.close()

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
    
def leave(client) :
    try :
        client.connection().send("Vous êtes sur le point de vous déconnecter, en êtes-vous sûr (oui/non) ?".encode())
        message=client.connection().recv(1024).decode()
        if message not in ["oui","non"] :
            client.connection().send("Nous n'avons pas compris votre requête.".encode())
            return leave(client)
        elif message == "oui" :
            client.connection().send("Vous allez être déconnecté".encode())
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

            elif message == "/friends" :
                friends = amities(client)
                if friends != [] :
                    client.send("Tes amis sont : \n ")
                    for result in friends :
                        print(result)
                        client.send(f"{result[0]} \n")
                else :
                    client.send("Tu n'es ami avec personne pour le moment.")

            elif message.startswith("/friend_requests") :
                amities_inbox(client, message)

            elif message.startswith("/befriend") :
                print(message)
                requete_amis(client, message)

            elif message.startswith("/") :
                client.connection().send("La commande que vous avez entré est invalide".encode())

            else:
                broadcast(message, client)
        except:
            client.disconnect()
    try :
        print(f"📴 | Closing connection from {client.address()}")
        clients.remove(client)
        
    except :
        connected = False
        clients.remove(client)
        client.disconnect()
        print(f"📴 | Connection closed from {client.address()}")

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