from tkinter import *
import tkinter.font as font



#THEME NAME, frame principales, frames milieu, petits éléments, police, message de soi
allbg = [["Skyline","#74B1D6","#9CD1F2", "white", 'black', "red"],
         ["Dark","black","#45484A","#7D8184", "white","#CBB1E3"],
         ["Charles P.","White","White","White", "black","#B1D5E3"],
         ["Ouafa", "#30633B","#DBF2B2", "#108028", "#23432A"],

         ]
theme = 0

win = Tk()
win.configure(bg = allbg[theme][2])
win.geometry("600x600")
win.maxsize(width=1000, height=700)
win.title("Ulti-Mates")


# créer une nouvelle police en utilisant le nom Arial et la taille 10
default_font = font.Font(family='Comic Sans Ms', size=10)
# définir la police par défaut pour tous les widgets tkinter
win.option_add("*Font", default_font)

def update_colors():
    '''change la couleur pour le theme'''
    win.configure(bg = allbg[theme][2])
    themecolor.configure(text = allbg[theme][0], bg=allbg[theme][2])
    for widget in win.winfo_children():
        widget_type = widget.winfo_class()
        if widget_type == 'Frame' :
            widget.configure(bg=allbg[theme][1])
    contain.configure(bg=allbg[theme][1])
    # Couleurs des éléments dans le cadre du haut
    address.configure(bg=allbg[theme][3], fg = allbg[theme][4])
    themecolor.configure(bg=allbg[theme][2], foreground=allbg[theme][4])
    
    # Couleurs de la Listbox et de la Scrollbar
    mylist.configure(bg=allbg[theme][3], highlightbackground=allbg[theme][2])
    scrollbar.configure(troughcolor=allbg[theme][2])
    
    # Couleurs des éléments dans le cadre du bas
    texting.configure(bg=allbg[theme][3], fg = allbg[theme][4])
    send.configure(bg=allbg[theme][1], fg=allbg[theme][4])
    mylist.tag_config("me", foreground=allbg[theme][5])
    mylist.tag_config("them", foreground=allbg[theme][4])
    

def write_on():
    '''Envoie d'un message dans la listbox comme message du client'''
    print(texting.get())
    if len(texting.get()) > 0 and texting == win.focus_get():
        
        mylist.configure(state="normal")
        mylist.insert(END ,texting.get()+"\n", "me")
        stocked.append((texting.get(), 0))
        try :
            sock.send(texting.get().encode())
        except :
            print("Impossible d'envoyer le message !")
        texting.delete(0, END)

def write_other(message):
    '''Envoie d'un message dans la listbox comme message d'un tiers'''
    if len(message) > 0:
        mylist.configure(state="normal")
        mylist.insert(END, message+"\n" ,"them")
        stocked.append((message, 1))

##########################COMPLETE OBSOLETE############################

topframe = Frame(win, bg = allbg[theme][1], bd = 3)
address = Entry(topframe,bg = allbg[theme][3])
address.insert(0, '  Adresse IP serveur...')
address.configure(foreground='grey')
address.bind('<FocusIn>', lambda event: address.delete('0', 'end'))

address.pack(side="left",padx=5, pady = 10)
topframe.pack(side="top", fill="x")

bar = Frame(win, height=2, bg=allbg[theme][2])
bar.pack(side="top", fill="x")

##################LIST BOX MENU
menu = Menu(win, tearoff=0)
menu.add_command(label="Copier", command=lambda: win.clipboard_clear() or win.clipboard_append(mylist.get(ACTIVE)))


midframe = Frame(win)
listframe = Frame(midframe,)
listframe.pack(side="left", fill="both", expand=True)
listframe.columnconfigure(0, weight=1)

####LISTBOX
stocked = [] #Stock des messages [MESSAGE, DESTINATEUR] 0 = YOU ; 1 = CLIENT ; 2 = SYSTEME



mylist = Text(listframe, bg = allbg[theme][3], state="disabled",bd=0, selectborderwidth=5)
mylist.pack(side="left", fill="both", expand=True,)
mylist.tag_config('them', foreground=allbg[theme][4])
mylist.tag_config('me', foreground=allbg[theme][5])
mylist.bind("<Button-1>", lambda event: "break")


scrollframe = Frame(midframe,)
scrollframe.pack(side="left", fill="y")
scrollbar = Scrollbar(scrollframe,)
scrollbar.pack(side="left", fill="y")
mylist.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=mylist.yview)
midframe.pack(side="top", fill="both", expand=True, padx=30)

#####TEXTING FUNCTIONS
def on_entry_click(event):
    if texting.get() == 'Entrez votre texte ici':
        texting.delete(0, "end") # effacer le texte de démonstration
        texting.config(fg = allbg[theme][4]) # changer la couleur du texte

def on_focusout(event):
    if texting.get() == '':
        texting.insert(0, 'Entrez votre texte ici') # remettre le texte de démonstration
        texting.config(fg = allbg[theme][1]) # changer la couleur du texte en gris



botframe = Frame(win, bg = allbg[theme][1], bd = 3, relief="flat", highlightbackground=allbg[theme][1])
contain = Frame(botframe,bg = allbg[theme][1])
send = Button(contain, text="➤", bg = allbg[theme][1], command=write_on, relief = "flat", font=("Arial", 20))
texting = Entry(contain, width = 50, bg = allbg[theme][2],bd=0,highlightbackground=allbg[theme][1] ,highlightthickness=1, highlightcolor= allbg[theme][4], fg = allbg[theme][4], relief="flat")
texting.configure(foreground='grey')
texting.insert(0, 'Entrez votre texte ici') # ajouter le texte de démonstration
texting.bind('<Return>', lambda event: write_on())
texting.bind('<FocusIn>', on_entry_click) # définir la fonction à appeler lors du focus sur l'Entry
texting.bind('<FocusOut>', on_focusout) # définir la fonction à appeler lors de la perte de focus sur l'Entry
texting.grid(row=0, column=0, sticky="ew", padx=10)
send.grid(row=0, column=1)
contain.pack(side="bottom", padx = 15, fill = "both")
contain.columnconfigure(0, weight=1)
botframe.pack(side="bottom", fill="x")

def changetheme():
    global theme
    if theme+1 ==len(allbg):
        theme = 0
    else:
        theme += 1
    print("theme", theme)
    update_colors()

themecolor = Button(topframe, text = allbg[theme][0], bg=allbg[theme][2], command=changetheme)

themecolor.pack(side="right",padx=5, pady = 10)




#####################INTERFACE##################################################
######################################TO BE CONTINUED###########################


import socket
import threading
def receive_message(sock) :
    while True :
        try :
            message = sock.recv(1024).decode()
            write_other(message)
        except :
            print("Une erreur est survenue lors de la dernière réception de message")
            sock.close()
            break

host="91.173.148.254"
#host="127.0.0.1"
port = 24444
sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
sock.connect((host,port))
message = ""
receive_thread = threading.Thread(target=receive_message, args=(sock, ))
receive_thread.start()



win.mainloop()