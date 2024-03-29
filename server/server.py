import hashlib
import socket
import sqlite3
import threading
import time
import traceback

import end_to_end_encryption as e2ee


class Client :
    def __init__(self,conn:socket,adresse:str,key:str,user_name:str) :
        self.username = user_name
        self.conn = conn
        self.adresse = adresse
        self.key = key
        self.connected = True
        self.db_id = self.registered()

    def connection(self) -> socket:
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
        time.sleep(0.05)

    def receive(self) :
        return str(e2ee.decrypt_message(self.conn.recv(1024), self.key))
    

    def registered(self) :
        temp_db = sqlite3.connect(path_db)
        temp_cur = temp_db.cursor()
        # TODO : Patch SQL injection vuln
        temp_cur.execute("SELECT COUNT(*) FROM entite WHERE user = ? ;", (self.username,))
        if temp_cur.fetchall()[0][0]==1 :
            temp_cur.execute("SELECT id FROM entite WHERE user = ? ;", (self.username,))
            result = temp_cur.fetchall()[0][0]
            temp_db.close()
            return result
        
        temp_db.close()
        return False
        

    def ouinon(self) :
        answer = self.receive()
        if answer == "oui" :
            return True
        elif answer == "non" :
            return False
        else :
            self.send("Votre réponse n'est pas valide, entrez oui ou non :")
            return self.ouinon()

clients = {}
path_db='\\home\\freebox\\server\\users.db'
local_path_db = 'server\\users.db'

path_db = local_path_db



try:
    with open("server/server.info", "r") as info:
        server_version = info.read()
except:
    print("❌ | Impossible de trouver la version du server !")
    server_version = "unknown"

"""
---------TO DO---------
    - Ajouter un système pour les programmeurs qui ouvre une fenêtre et exécute le programme qu'ils viennent de recevoir 
    pour éviter de faire des copiers collers

"""


users_ip = {}

def load_user_name(username:str):
    """
    Permet de savoir si un nom d'utilisateur est déjà pris
    True = found
    False = inexistant 
    """
    temp_db = sqlite3.connect(path_db)
    temp_cur=temp_db.cursor()
    print("👉 |checking user name")
    # TODO : Patch SQL injection vuln
    temp_cur.execute("SELECT COUNT(user) FROM entite WHERE user= ? ;", (username,))
    res = temp_cur.fetchall()[0][0] == 1
    temp_db.close()
    return res



def get_client_obj(username:str) :
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
    try :
        return clients[username]
    except :
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
            if message == "has joined the chat":
                clients[user].send((f"{client.username} {message}"))
            else:
                clients[user].send((f"<{client.username}> {message}"))



def first_connection(client:Client,attempts=0) :
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
            client.send("> Vous avez fait trop d'erreurs, vous allez être déconnecté(e).")
            return False
        
        temp_db=sqlite3.connect(path_db)
        temp_cur=temp_db.cursor()

        if load_user_name(client.username) == True :  # Vérifie que le nom d'utilisateur entré existe dans la base de données.
            
            print(f"👉 | {client.username} is trying to connect")

            client.send("> Quel est votre mot de passe ?")

            # TODO : Patch SQL injection vuln
            temp_cur.execute("SELECT COUNT(*) FROM entite WHERE user= ? AND password= ? ;", (client.username, hashlib.sha256(client.receive().encode()).hexdigest()) )
            if temp_cur.fetchall()[0][0]==1 :

                print(f"👉 | {client.username} is connected")

                client.send("> Vous êtes connecté(e) !")
                temp_db.close()
                return True
            else :
                print(f"👉 | {client.username} failed to connect (too many failed attempts))")

                client.send(f"> Vous avez {attempts+1} mauvaise(s) tentative(s), veuillez recommencer")
                temp_db.close()
                return first_connection(client, attempts+1)

        else :  # Si le nom d'utilisateur entré n'existe pas, la console proposera à l'utilisateur de créer un compte
            temp_db.close()
            print(f"👉 |{client.username} is trying to create an account")
            etapes_creation_compte = create_user(client)
            if etapes_creation_compte == True : # La fonction nous renverra True si le compte est créé avec succès.
                print(f"✅ | {client.username} created an account")

                client.send("> Votre compte a été créé ! \n\n> Vous allez être déconnecté, veuillez vous reconnecter. (/exit)")
                client.disconnect()
                return True
            elif etapes_creation_compte == "#USER_INPUT_MISTAKE#" :
                return "#USER_INPUT_MISTAKE#"
            else:
                
                print(f"❌ | {client.username} failed to create an account")

                return False
    except :
        return False



def create_user(client:Client) :
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
    client.send("> Le nom/pseudonyme entré n'est pas enregistré chez nous, voulez-vous créer un compte (oui/non) ?")
    answer = client.receive()
    if answer == "non" :
        return "#USER_INPUT_MISTAKE#"
    elif answer != "oui" :
        client.send("> La commande que vous avez entré n'est pas valide. \n")
        return create_user(client)
    else :
        count = 0
        while True :
            try :
                print(f"👉 |{client.username} is creating an account")

                client.send(("> Vous n'existez pas dans notre base de données, entrez le mot de passe souhaité :"))
                psw = hashlib.sha256(client.receive().encode()).hexdigest()
                client.send(("> Confirmez votre saisie :"))
                confirmation = hashlib.sha256(client.receive().encode()).hexdigest()
                if(count>=2) :
                    print(f"❌ | {client.username} failed to create an account (too many failed attempts)")
                    client.send(("> Vous avez essayé 3 fois, veuillez recommencer plus tard."))
                    psw, confirmation = None, None
                    return False

                elif psw == confirmation and count < 3 :
                    try :
                        temp_db=sqlite3.connect(path_db)
                        temp_cur=temp_db.cursor()
                        temp_cur.execute("INSERT INTO entite (user,password) VALUES ( ? , ? );", (client.username, psw))
                        temp_db.commit()
                        print(f"✅ | L'utilisateur {client.username} vient d'être ajouté à la base de données.")
                        temp_db.close()
                        psw, confirmation = None, None
                        return True
                    except :
                        print(f"❌ | Un problème est survenu lors de la création du compte pour l'utilisateur {client.username}")
                        psw, confirmation = None, None
                        return False
            
                else :
                    print(f"❌ | mots de passe de {client.username} ne correspondent pas")
                    count+=1
                    psw, confirmation = None, None
                    client.send("> Vos mots de passe ne correspondent pas, veuillez recommencer.")
            except :
                psw, confirmation = None, None
                return False



def amities(client:Client) :
    temp_db=sqlite3.connect(path_db)
    temp_cur=temp_db.cursor()
    temp_cur.execute('select user from entite where id in (select user2 as user from Amities where user1 in (select id from entite where user = ? ) UNION select user1 as user from Amities where user2 in (select id from entite where user = ? ));', (client.username, client.username) )
    res = temp_cur.fetchall()
    temp_db.close()
    for i in range(len(res)) :
        res[i] = res[i][0]
    return res

def requested_by(client:Client) :
    db = sqlite3.connect(path_db)
    cur = db.cursor()
    cur.execute("SELECT user FROM Req_Amis JOIN entite ON Req_Amis.sender = entite.ID WHERE receiver = ? ;", (client.db_id,))
    liste = []
    for i in cur.fetchall() :
        liste.append(i[0])
    db.close()
    return liste

def requete_amis(client:Client,receiver:str) :
    amis = amities(client)
    db = sqlite3.connect(path_db)
    cur = db.cursor()
    cur.execute("SELECT user FROM Req_Amis JOIN entite ON Req_Amis.receiver = entite.id WHERE sender = ? ;", (client.db_id,))
    amis_en_attente = cur.fetchall()
    print(amis_en_attente)
    for demande in amis_en_attente :
         if receiver == demande[0] :
            client.send(f"> Vous avez déjà demandé {receiver} en ami(e).")
            db.close()
            return None
    for i in requested_by(client) :
        if i == receiver :
            client.send(f"> L'utilisateur {receiver} vous déjà demandé en ami, voulez vous accepter ?")
            if not client.ouinon() :
                db.close()
                client.send("> Retour aux messages !")
                return None
            else :
                cur.execute("INSERT INTO Amities (user1,user2) VALUES ( ? , ? );", (get_user_db_id(receiver),client.db_id) )
                cur.execute("DELETE FROM Req_Amis WHERE sender = ? AND receiver = ? ;", (get_user_db_id(receiver),client.db_id) )
                db.commit()
                db.close()
                client.send(f"Vous êtes maintenant ami avec {receiver} !")
                return None
    if amis != [] :
        if receiver in amities(client) :
            client.send(f"> Vous êtes déjà ami avec {receiver}")
    elif load_user_name(receiver) != False :
        if receiver in blocked_list(client) :
            client.send(f"> Vous avez bloqué {receiver}.")
        elif receiver in blockers_list(client) :
            client.send(f"> L'utilisateur {receiver} n'existe pas.")
        else :
            cur.execute("select id from entite where user = ? ;", (receiver,))
            receiver_database_id = cur.fetchall()[0][0]
            print(f"insert into Req_Amis (sender,receiver) values ( ? , ? );", (client.id(), receiver_database_id))
            cur.execute("insert into Req_Amis (sender,receiver) values ( ? , ? );", (client.id(), receiver_database_id))
            client.send(f"> Votre demande d'ami envers {receiver} a été envoyée !")
    else :
        client.send(f"> Le nom d'utilisateur {receiver} n'existe pas.")
    db.commit()
    db.close()



def demande_amis(client:Client,message:str) :
    temp_db = sqlite3.connect(path_db)
    temp_cur = temp_db.cursor()
    temp_cur.execute("select req_id,user from Req_Amis join entite on Req_Amis.sender = entite.id where receiver = ? ;", (client.id(),))
    ans = temp_cur.fetchall()
    temp_db.close()

    if len(ans) != 0 :

        amis = ""
        for i in range(len(ans)) :
            amis += f" |- <{str(ans[i][0])}> {str(ans[i][1])}{' '*(58 - len(str(ans[i][0])) - len(str(ans[i][1])))}|\n"

        print('amis : ',amis)


        message_ami  = "  _______________________________________________________________  \n"
        message_ami += " /                                                               \ \n"
        message_ami += " | Ces personnes vous ont demandé(e) en ami(e) <ID> <username> : | \n" if len(ans) > 1 else " | Cette personne vous à demandé(e) en ami(e) : |\n"
        message_ami += amis
        message_ami += " \_______________________________________________________________/\n"
        
        client.send(message_ami)

        return True # Pour indiquer que le client a des demandes d'amis
    else :
        client.send("> Vous n'avez aucune nouvelle demande d'amis.")
        return False # Pour indiquer que le client n'a aucune demande d'amis

def get_user_db_id(username:str) :
    db = sqlite3.connect(path_db)
    cur = db.cursor()
    cur.execute("SELECT * FROM entite WHERE user = ? ;", (username,))
    result = cur.fetchall()
    db.close()
    if len(result) == 1 :
        return result[0][0]
    else :
        return []

def get_friends(client):
    friends = amities(client)
    if friends != [] :
        if len(friends) == 1 :
            client.send("> Tu as un ami :")
        else : 
            client.send("> Tes amis sont :")
        for friend in friends :
            client.send(f"    -  {friend}")
    else :
        client.send("> Tu n'es ami avec personne pour le moment.")



def amities_inbox(client:Client,message:str) :
    if demande_amis(client,message) :
        client.send("> Voulez-vous accepter une demande (oui/non) ?")
        answer = client.receive()
        if answer == "oui" :
            client.send("> Quel utilisateur voulez-vous accepter ?")
            username = client.receive()
            db = sqlite3.connect(path_db)
            cur = db.cursor()
            cur.execute("select req_id from Req_Amis join entite on req_amis.sender=entite.id where receiver = ? and user = ? ;", (client.id(), username))
            requete = cur.fetchall()
            if requete != [] :
                cur.execute("insert into Amities (user1,user2) select sender,receiver from Req_Amis where req_id = ? ;", (requete[0][0],))
                cur.execute("delete from Req_Amis where req_id = ? ;", (requete[0][0],))
                db.commit()
                db.close()
                client.send("> Demande acceptée !")
            else :
                client.send("> Aucune demande trouvée pour cet identifiant.\n")
                db.close()
        elif answer == "non" :
            client.send("> D'accord, retour aux messages !\n")
            return None
        else :
            client.send("> Je n'ai pas compris votre réponse.\n> Retour aux messages !\n")
            return None

def blocked_list(client:Client) :
    db = sqlite3.connect(path_db)
    cur = db.cursor()
    cur.execute("select user from Blocked JOIN entite on Blocked.blocked = entite.id where blocker = ? ;", (client.id(),))
    result = cur.fetchall()
    liste_amis=[]
    for i in result :
        liste_amis.append(i[0])
    db.close()
    return liste_amis

def blockers_list(client:Client) :
    db = sqlite3.connect(path_db)
    cur = db.cursor()
    cur.execute("select user from Blocked JOIN entite on Blocked.blocked = entite.id where blocked = ? ;", (client.id(),))
    result = cur.fetchall()
    liste_blockers=[]
    for i in result :
        liste_blockers.append(i[0])
    db.close()
    return liste_blockers

def who_is_blocked(client:Client, comeback:bool=False) :
    db = sqlite3.connect(path_db)
    cur = db.cursor()
    liste_amis = blocked_list(client)
    if liste_amis == [] :
        client.send("Vous n'avez bloqué personne.")
        db.close()
        return None
    else :
        client.send(f"Vous avez bloqué les personne suivantes : \n")
        client.send(", ".join(liste_amis))
    client.send("\n> Voulez-vous débloquer quelqu'un (oui/non) ?")
    answer = client.receive()
    if answer == "oui" :
        client.send("Qui voulez-vous débloquer ?")
        username_to_unblock = client.receive()
        if not load_user_name(username_to_unblock) :
            client.send("Le nom d'utilisateur entré n'existe pas.")
        else :
            cur.execute("SELECT block_id FROM Blocked JOIN entite ON Blocked.blocked = entite.ID WHERE Blocker= ? AND user= ? ;", (client.db_id,username_to_unblock))
            result = cur.fetchall()
            if result != [] :
                client.send(f"Voulez-vous vraiment débloquer {username_to_unblock} ?")
                if client.ouinon() :
                    cur.execute("DELETE FROM Blocked WHERE block_id = ? ", (result[0][0],))
                    db.commit()
            else :
                client.send(f"Vous n'avez pas bloqué {username_to_unblock}")
        db.close()
    elif answer == "non" :
        client.send("> D'accord, retour aux messages !")
        db.close()
    else :
        client.send("> Je n'ai pas compris votre réponse.\n")
        db.close()
        who_is_blocked(client,True)

def block(client:Client, message:str) :
    if len(message.split(" ")) == 2:
        blocked = message.split(" ")[1]
        blocked_db_id = get_user_db_id(blocked)
        if blocked_db_id == [] :
            client.send(f"L'utilisateur {blocked} n'a pas été trouvé.")
            return None
    else :
        client.send("Vous devez entrer un nom d'utilisateur valide.")
        return None

    db = sqlite3.connect(path_db)
    cur = db.cursor()
    cur.execute("INSERT INTO Blocked (blocker,blocked) values ( ? , ? );", (client.db_id, blocked_db_id))
    cur.execute("DELETE FROM Amities WHERE (user1= ? AND user2= ? ) OR (user2= ? AND user1= ? );", (client.db_id, blocked_db_id, client.db_id, blocked_db_id))
    cur.execute("DELETE FROM Req_Amis WHERE (sender= ? AND receiver= ? ) OR (receiver= ? AND sender= ? );", (client.db_id, blocked_db_id, client.db_id, blocked_db_id))
    db.commit()
    db.close()
    client.send(f"Vous avez bien bloqué {blocked}")


def msg(client:Client, message:str):
    """
    Envoie un message a un client specifique
    """
    if len(message.split(" ")) < 3 :
        client.send("Vous devez entrer un message ainsi qu'un nom d'utilisateur à qui l'envoyer.")
        return None
    
    message = message.split(" ")[1:]
    receiver_username = message[0]
    message = " ".join(message[1:])
    receiver = get_client_obj(receiver_username)
    if receiver != False :
        if receiver.username in amities(client) :
            client.send(f"<me -> {str(receiver.username)}> {message}")
            receiver.send(f"<{str(client.username)} -> me> {message}")
        else :
            client.send(f"> Vous n'êtes pas ami avec {receiver_username}.\n")
    else:
        client.send(f"> {receiver_username} n'existe pas ou n'est pas connecté\n")

def help():
    """
    affiche un message d'aide
    """
    help_ ="\n  ___________________________________________________________________  \n"
    help_ += " /                                                                   \ \n"
    help_ += " |- /befriend <username>      : faire une demande d'ami              | \n"
    help_ += " |- /exit                     : quitter le programme                 | \n"
    help_ += " |- /friends                  : afficher la liste de vos amis        | \n"
    help_ += " |- /friend_requests          : afficher les demandes d'amis         | \n"
    help_ += " |- /help                     : afficher ce message                  | \n"
    help_ += " |- /info                     : afficher la version du client/server | \n"
    help_ += " |- /msg <username> <message> : envoyer un message privé à un ami    | \n"
    help_ += " |- /users                    : afficher les utilisateurs connecté   | \n"
    help_ += " |- /who_is_blocked           : afficher les personnes bloquées      | \n"
    help_ += " \___________________________________________________________________/ \n"
    # plus grand et ca bug :/
    return help_



def leave(client:Client) :
    try :
        client.send("> Vous êtes sur le point de vous déconnecter, en êtes-vous sûr (oui/non) ?")
        message=client.receive()
        if message not in ["oui","non"] :
            client.send("> Nous n'avons pas compris votre requête.")
            return leave(client)
        elif message == "oui" :
            client.send("> Vous allez être déconnecté")
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
        users_line += f" |- {user}{' '*(36 - len(user))}|\n"

    line ="\n  ______________________________________\n"
    line += " /                                      \ \n"

    if len(list(clients.keys())) == 1:
        line += " | Utilisateur actuellement en ligne :  |\n"
    elif len(list(clients.keys())) > 1:
        line += " | Utilisateurs actuellement en ligne : |\n"
    else:
        line += " | Aucun utilisateur en ligne.          |\n"

    line += users_line
    line += " \______________________________________/\n"

    return line
    


def server_info(client:Client):
    """
    envoie un message au client a propos de la version du server
    """
    try:
        with open("server/server.info", "r") as info:
            client.send(f"> Version du server : {info.read()}")
    except:
        client.send("> Impossible de trouver la version du server !")



def handshake(message:str):
    """
    when a client to the server, it frst sends a message containing the encryption key that need to be decrypted with the fix_token
    """
    decrypted_message = e2ee.decrypt_message(message, e2ee.fix_token)

    return (True, decrypted_message) if len(decrypted_message) == 128 else (False, '')



def handle_client(conn:socket, addr:str, first_time=True, handshaked=False):
    """
    Fonction pour gérer les connexions entrantes des clients
    """
              
    print(f"\n------------------------------------\n🔓 | Handshake de {addr} en cours...")
    if not handshaked :
        handshaked, key = handshake(conn.recv(1024))
        if handshaked :
            conn.send(e2ee.encrypt_message(key, e2ee.fix_token))
            time.sleep(0.1)
            conn.send(e2ee.encrypt_message(f"##{server_version}", key))
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
            broadcast("has joined the chat", client)
            print("broad")
            client.send("> Si vous ne connaissez pas les commandes habituelles, entrez '/help' pour les voir !\n ")
        
        while client.connection_status():
            try:
                message = client.receive() 

                print(f"📳 | <{client.username}> {message}")
                if message.startswith("/") :
                    if message.startswith("/msg"):
                        msg(client, message)

                    elif message.startswith("/users"):
                        client.send(online_users())

                    elif message.startswith("/help"):
                        client.send(help())
                    
                    elif message.startswith("/exit") :
                        if leave(client) :
                            client.disconnect()

                    elif message == "/friends" :
                        get_friends(client)

                    elif message.startswith("/friend_requests") :
                        amities_inbox(client, message)

                    elif message.startswith("/befriend") :
                        if len(message.split(" ")) > 1 :
                            requete_amis(client, " ".join(message.split(" ")[1:]))
                        else :
                            client.send("> La commande que vous avez entré est invalide")
                    elif message.startswith("/who_is_blocked") :
                        who_is_blocked(client)
                    elif message.startswith("/block") :
                        block(client, message)
                    elif message.startswith("/info") :
                        server_info(client)
                    else :
                        client.send("> La commande que vous avez entré est invalide")

                else:
                    broadcast(message, client)
            except:
                client.disconnect()
                print(traceback.format_exc())
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
    HOST = '127.0.0.1' # Pour les tests sur machine locale
    PORT = 4444

    #check si la base de données existe
    print("👉 | Vérification de la base de données...")
    try:
        db = sqlite3.connect(path_db)
        db.close()
    except:
        print("❌ | La base de données n'a pas été trouvée.")
        print("❌ | Le serveur ne peut pas démarrer.")
        return None

    print("✅ | La base de données a été trouvée.")
    print("✅ | Le serveur peut démarrer.")
    

    # Créer un socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server :
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
