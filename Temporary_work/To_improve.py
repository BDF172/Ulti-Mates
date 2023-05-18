def get_friends(client):
    friends = amities(client)
    print('friends :',friends)
    if friends != [] :

        friend = ""
        for result in friends :
            friend += f" |- {str(result[0])} {' '*30 - len(str(result[0]))}| \n"

        print('friend :',friend)

        friends_ ="\n  ________________________________\n"
        friends_ += " /                                \ \n"
        friends_ += " | Vos amis :                     |\n"
        friends_ += friend
        friends_ += " \________________________________/\n"

        client.send(friends_)
        
    else :
        client.send("> Tu n'es ami avec personne pour le moment.")