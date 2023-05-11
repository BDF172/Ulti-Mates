import socket, threading, sqlite3, time, hashlib
import end_to_end_encryption as e2ee

class Client :
    def __init__(self,conn,adresse,key,user_name) :
        self.username = user_name
        self.conn = conn
        self.adresse = adresse
        self.key = key
        self.connected = True
        self.db_id = self.registered()

    def connection(self) :
        return self.conn

    def connection_status(self) :
        return self.connected

    def disconnect(self) :
        if not self.connected : broadcast(f"has left the chat", self)
        self.connected = False

    def id(self) :
        return self.db_id

    def send(self,message:str) :
        self.conn.send(e2ee.encrypt_message(message, self.key))

    def receive(self) :
        return str(e2ee.decrypt_message(self.conn.recv(1024), self.key))
    

    def registered(self) :
        temp_db = sqlite3.connect(path_db)
        temp_cur = temp_db.cursor()
        temp_cur.execute(f"SELECT COUNT(*) FROM entite WHERE user = '{self.username}'")
        if temp_cur.fetchall()[0][0]==1 :
            temp_cur.execute(f"SELECT id FROM entite WHERE user = '{self.username}';")
            return temp_cur.fetchall()[0][0]
        return False
        temp_db.close()

clients = {}
# path_db='/home/freebox/server/users.db'
path_db = 'Temporary_work\\users.db'

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
        if client.username == username :
            return client
    return False

def broadcast(message:str, client:Client):
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
    None :
        Rien n'est renvoyé, en revanche un message est diffusé sur la console de tous les membres en ligne.
    """
    for user in list(clients.keys()):
        if clients[user].username != client.username:
            clients[user].send((f"<{client.username}> {message}"))
    return

def first_connection(client,attempts=0) :
    """
    -----------
    Description
    -----------
        Fonction exécutée lors de la première connexion du client.
        Cette fonction va faire la connexion du client.
    -------
    Entrees
    -------
    client :
        Instance de la classe Client dont le username est seulement le nom d'utilisateur non connecté
    attempts :
        Nombre de tentatives de mots de passe erronées.     
    -------
    Sorties
    -------
    type bool :
        Booléen vrai si la connexion est réussie.
    """
    try :
        if attempts == 2:
            client.send("Vous avez fait trop d'erreurs, vous allez être déconnecté(e).")
            return False
        
        temp_db=sqlite3.connect(path_db)
        temp_cur=temp_db.cursor()

        if load_user_name(client.username) == True :  # Vérifie que le nom d'utilisateur entré existe dans la base de données.
            
            print(f"👉 | {client.username} is trying to connect")

            client.send("Quel est votre mot de passe ?")
            password = hashlib.sha1(client.receive().encode()).hexdigest()
            
            print(password)

            temp_cur.execute(f"SELECT COUNT(*) FROM entite WHERE user='{client.username}' AND password='{password}';")
            if temp_cur.fetchall()[0][0]==1 :

                print(f"👉 | {client.username} is connected")

                client.send("Vous êtes connecté(e) !")
                temp_db.close()
                return True
            else :
                print(f"👉 | {client.username} failed to connect (too many failed attempts))")

                client.send(f"Vous avez {attempts+1} mauvaise(s) tentative(s), veuillez recommencer")
                temp_db.close()
                return first_connection(client, attempts+1)

        else :  # Si le nom d'utilisateur entré n'existe pas, la console proposera à l'utilisateur de créer un compte
            temp_db.close()
            print(f"👉 |{client.username} is trying to create an account")
            etapes_creation_compte = create_user(client)
            if etapes_creation_compte == True : # La fonction nous renverra True si le compte est créé avec succès.
                print(f"✅ | {client.username} created an account")

                client.send("Votre compte a été créé ! \nVous allez être déconnecté, veuillez vous reconnecter.")
                client.disconnect()
                return True
            elif etapes_creation_compte == "#USER_INPUT_MISTAKE#" :
                return "#USER_INPUT_MISTAKE#"
            else:
                
                print(f"❌ | {client.username} failed to create an account")

                return False
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
    client.send("Le nom/pseudonyme entré n'est pas enregistré chez nous, voulez-vous créer un compte (oui/non) ?")
    answer = client.receive()
    if answer == "non" :
        return "#USER_INPUT_MISTAKE#"
    elif answer != "oui" :
        client.send("La commande que vous avez entré n'est pas valide. \n")
        return create_user(client)
    else :
        count = 0
        while True :
            try :
                print(f"👉 |{client.username} is creating an account")

                client.send(("Vous n'existez pas dans notre base de données, entrez le mot de passe souhaité :"))
                psw = hashlib.sha1(client.receive().encode()).hexdigest()
                client.send(("Confirmez votre saisie :"))
                confirmation = hashlib.sha1(client.receive().encode()).hexdigest()
                if(count>=2) :
                    print(f"❌ | {client.username} failed to create an account (too many failed attempts)")
                    client.send(("Vous avez essayé 3 fois, veuillez recommencer plus tard."))
                    return False

                elif psw == confirmation and count < 3 :
                    try :
                        temp_db=sqlite3.connect(path_db)
                        temp_cur=temp_db.cursor()
                        temp_cur.execute(f"INSERT INTO entite (user,password) VALUES ('{client.username}','{psw}');")
                        temp_db.commit()
                        print(f"✅ | L'utilisateur {client.username} vient d'être ajouté à la base de données.")
                        temp_db.close()
                        return True
                    except :
                        print(f"❌ | Un problème est survenu lors de la création du compte pour l'utilisateur {client.username}")
                        return False
            
                else :
                    print(f"❌ | ")
                    message = "Vos mots de passes ne correspondent pas, veuillez recommencer."
                    count+=1
                    client.send(message)
            except :
                return False


def amities(client) :
    temp_db=sqlite3.connect(path_db)
    temp_cur=temp_db.cursor()
    temp_cur.execute(f'select user from entite where id in (select user2 as user from Amities where user1 in (select id from entite where user = "{client.username}") UNION select user1 as user from Amities where user2 in (select id from entite where user = "{client.username}"));')
    res = temp_cur.fetchall()
    temp_db.close()
    return res

def requete_amis(client,receiver) :
    amis = amities(client)
    temp_db = sqlite3.connect(path_db)
    temp_cur = temp_db.cursor()
    temp_cur.execute(f"SELECT user FROM Req_Amis JOIN entite ON Req_Amis.receiver = entite.id WHERE sender = {client.id()};")
    amis_en_attente = temp_cur.fetchall()
    print(amis_en_attente)
    for demande in amis_en_attente :
         if receiver == demande[0] :
            client.send(f"Vous avez déjà demandé {receiver} en ami(e).")
            temp_db.close()
            return None
    if amis != [] :
        if receiver in amities(client)[0] :
            client.send(f"Vous êtes déjà ami avec {receiver}")
    elif load_user_name(receiver) != False :
        temp_cur.execute(f"select id from entite where user = '{receiver}';")
        receiver_database_id = str(temp_cur.fetchall()[0][0])
        print(f"insert into Req_Amis (sender,receiver) values ({client.id()},{receiver_database_id});")
        temp_cur.execute(f"insert into Req_Amis (sender,receiver) values ({client.id()},{receiver_database_id});")
        client.send(f"Votre demande d'ami envers {receiver} a été envoyée !")
    else :
        client.send(f"Le nom d'utilisateur {receiver} n'existe pas.")
    temp_db.commit()
    temp_db.close()

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
        client.send((f"Ces personnes vous ont demandé(e) en ami(e) : \n"))
        client.send("<Identifiant demande d'ami> | <Personne à l'origine de la demande>\n")
        client.send("\n------------------------------------------------------------------\n")
        for i in res :
            client.send(str((" | ".join(i)), '\n'))
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
            return None

def who_is_blocked(client) :
    temp_db = sqlite3.connect(path_db)
    temp_cur = temp_db.cursor()
    temp_cur.execute(f"select user from Blocked JOIN entite on Blocked.blocked = entite.id where blocker = {client.id()};")
    result = temp_cur.fetchall()
    temp_db.close()
    if result == []: 
        client.send("Vous n'avez bloqué personne.")
    else :
        client.send("Vous avez bloqué les personnes suivantes : \n")
        liste_amis = []
        for i in result :
            liste_amis.append(i[0])
        client.send(",".join(liste_amis))
        client.send("Voulez-vous débloquer quelqu'un (oui/non) ?")
        answer = client.receive()
        if answer == "oui" :
            NotImplemented
        elif answer == "non" :
            client.send("D'accord, retour aux messages !")
        else :
            client.send("")

def tell(message, client):
    """
    Envoie un message a un client specifique
    """
    message = message.replace("/msg","").split(" ")
    receiver_username = message[1]
    try:
        receiver = clients[receiver_username]
    except KeyError:
        receiver = None
    message = " ".join(message[2:])

    if type(receiver) == type(client):
        receiver.send(f"<{str(client.username)} -> me> {message}")
        client.send(f"<me -> {str(receiver.username)}> {message}")
    else:
        client.send(f"{receiver_username} does not exist or is not connected.")

def help():

    """
    ascii art of 'help' HELP
    """
    help_ ="\n _________________________________________________________________  \n"
    help_ += "/                               _     _                           \ \n"
    help_ += "|                          |_| |_ |  |_)                          | \n"
    help_ += "|                          | | |_ |_ |                            | \n"
    help_ += "|                                                                 | \n"
    help_ += "+-----------------------------------------------------------------+ \n"
    help_ += "|- /users                    : liste des utilisateurs connecté    | \n"
    help_ += "|- /msg <username> <message> : envoyer un message privé           | \n"
    help_ += "|- /users                    : affiche les utilisateurs connecté  | \n"
    help_ += "|- /help                     : afficher ce message                | \n"
    help_ += "\_________________________________________________________________/  \n"
    return help_
    

def leave(client) :
    try :
        client.send("Vous êtes sur le point de vous déconnecter, en êtes-vous sûr (oui/non) ?")
        message=client.receive()
        if message not in ["oui","non"] :
            client.send("Nous n'avons pas compris votre requête.")
            return leave(client)
        elif message == "oui" :
            client.send("Vous allez être déconnecté")
            return True
        else :
            return False
    except :
        return False


def online_users() :
    """
    generate a mesage containing every username
    """
    users_line = ""
    for user in list(clients.keys()):
        users_line += f"|- {user}{' '*(36 - len(user))}|\n"

    line ="\n ______________________________________\n"
    line += "/                                      \ \n"
    line += "| Utilisateurs actuellement en ligne : |\n"
    line += users_line
    line += "\______________________________________/\n"

    return line
    


def handshake(message):
    """
    when a client to the server, it frst sends a message containing the encryption key that need to be decrypted with the fix_token
    """
    decrypted_message = e2ee.decrypt_message(message, e2ee.fix_token)

    return (True, decrypted_message) if len(decrypted_message) == 128 else (False, '')


def handle_client(conn, addr, first_time=True, handshaked=False):
    """
    Fonction pour gérer les connexions entrantes des clients
    """
              
    print(f"\n------------------------------------\
          \n🔓 | Handshake de {addr} en cours...")
    if not handshaked :
        handshaked, key = handshake(conn.recv(1024))
        if handshaked :
            conn.send(e2ee.encrypt_message(key, e2ee.fix_token))
        else :
            print(f"❌ | Handshake de {addr} échoué")
            conn.close()
            return None
    

    print(f"🔐 | Handshake de {addr} terminé")

    if first_time == True :
        print(f"🌐 | New connection from {addr}")
        
    try :
        print(f"👤 | {addr} demande d'un nom d'utilisateur")
        conn.send(e2ee.encrypt_message("Vous venez de vous connectez à notre serveur, entrez votre nom ou un pseudonyme", key))
        user = e2ee.decrypt_message(conn.recv(1024), key)
        print(user)
    except :
        conn.close()
        return None
    
    if not user :
        conn.close()
        return None
    
    print(f"👤 | {addr} a choisi le nom d'utilisateur {user}")

    client = Client(conn, addr, key, user) 
    clients[user] = client

    try :
        etapes_connexion_finies = first_connection(client)
        if etapes_connexion_finies == "#USER_INPUT_MISTAKE#" :
            client.disconnect()
            del clients[user]
            return handle_client(client.connection(),client.adresse,False)
        
        elif etapes_connexion_finies == False :
            print(f"❌ | L'utilisateur {client.username} venant de l'adresse IP {client.adresse} a échoué sa connexion.")
            client.disconnect()

        if client.connection_status() :
            print(f"✅ | L'utilisateur {client.username} a réussi sa connexion sur l'adresse IP {client.adresse}.")
            broadcast(f"has joined the chat", client)
            print("broad")
            client.send("Si vous ne connaissez pas les commandes habituelles, entrez '/help' pour les voir !\n ")
        
        while client.connection_status():
            try:
                message = client.receive() 

                print(f"📳 | {client.username},Received message: {message}")

                if message.startswith("/msg"):
                    tell(message, client)

                elif message.startswith("/users"):
                    client.send(online_users())

                elif message.startswith("/help"):
                    client.send(help())
                
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
                    if len(message.split(" ")) > 1 :
                        requete_amis(client, " ".join(message.split(" ")[1:]))
                    else :
                        client.send("La commande que vous avez entré est invalide")
                elif message.startswith("/who_is_blocked") :
                    who_is_blocked(client)
                elif message.startswith("/") :
                    client.send("La commande que vous avez entré est invalide")

                else:
                    broadcast(message, client)
            except:
                client.disconnect()
        del clients[user]
        client.disconnect()
        print(f"📴 | Connection closed to {client.adresse}")
    except :
        del clients[user]
        client.disconnect()
        print(f"📴 | Connection closed to {client.adresse}")


def start_server():
    """
    Fonction pour démarrer le serveur et écouter les connexions entrantes
    """
    # Configuration du serveur
    # HOST = '192.168.1.83'
    HOST = '127.0.0.1'
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