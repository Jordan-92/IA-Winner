import json
import time
import sys
import socket
import random

# Timeout, sendJSON, receiveJSON, NotAJSONObject ont été copiés de jsonNetwork

class NotAJSONObject(Exception):
	pass

class Timeout(Exception):
	pass

def sendJSON(socket, obj):
	message = json.dumps(obj)
	if message[0] != '{':
		raise NotAJSONObject('sendJSON support only JSON Object Type')
	message = message.encode('utf8')
	total = 0
	while total < len(message):
		sent = socket.send(message[total:])
		total += sent

def receiveJSON(socket, timeout = 1):
	finished = False
	message = ''
	data = ''
	start = time.time()
	while not finished:
		message += socket.recv(4096).decode('utf8')
		if len(message) > 0 and message[0] != '{':
			raise NotAJSONObject('Received message is not a JSON Object')
		try:
			data = json.loads(message)
			finished = True
		except json.JSONDecodeError:
			if time.time() - start > timeout:
				raise Timeout()
	return data

def subscribe(port, s0) :
    """
    inscrit notre IA sur le serveur
    """
    s0.connect(('0.0.0.0', 3000))
    obj = json.dumps({
        "request": "subscribe",
        "port": port,
        "name": "IA_Winner",
        "matricules": ["19195", "19016"]
    })
    s0.send(obj.encode('utf8'))
    result = s0.recv(512)
    print(result.decode('utf8'))
    s0.close()

def listen(port) :
    """
    écoute le serveur
    """
    s = socket.socket()
    s.bind(('0.0.0.0', port))
    s.listen()
    while True :
        client, address = s.accept()
        with client :
            message = receiveJSON(client)
            if message["request"] == "ping" :
                pingpong(client)
            if message["request"] == "play" :
                play_a_move(client, message)

def pingpong(client) :
    """
    confirmation de la connexion
    """
    print("vérification de la connection")
    sendJSON(client, {
        "response": "pong"
    })

def play_a_move(client, message) :
    """
    créé le message à envoyer au serveur
    """
    print("demande de coups")
    state = message["state"]
    move_json = play(state)
    message = ""
    if moves(state, "message") == True :
        message = "bille adverse éjectée, défaite ennemie en approche"
    print(move_json)
    sendJSON(client, {
        "response": "move",
        "move": move_json,
        "message": message
    })

def play(state):
    """
    appelle les différentes fonctions permettant de décider du move. Nous avons créé plusieurs fonctions
    afin de mieux se répartir le travail
    """
    move_list = moves(state, "move")
    if move_list == [] :
        res = {
            "response": "giveup",
        }
        return res                          # permet d'abandonner si il n'y a que des "bad move" mais c'est sensé ne jamais arriver
    coup_aléatoire = aléatoire(move_list)
    move_json = move_list_to_json(coup_aléatoire)
    return move_json

def moves(state, data):
    """
    fonctions centrale du code, elle renvoie une liste de tous les meilleurs mouvements possibles
    selon notre intelligeance artificielle

    entrée : state et data qui demande un mouvement ou un message
    sortie : liste comprenant des listes de mouvements. Le premier élément de la liste de mouvement reprend les billes à bouger
    et le deuxième élément reprend la direcction
    exemple : liste en sortie des meilleurs coups possible pour un départ du joueur blanc selon notre IA:
    [[[[0, 0], [1, 1], [2, 2]], 'SE'], [[[0, 4], [1, 4], [2, 4]], 'SW']]
    """

    board = state["board"]                          # définition du plateu
    couleur = ma_couleur(state)                     # couleur du joueur
    mes_pions = pion_du_joueur(board,couleur)       # liste de la position des pions du joueur
    
    if data == "message" :
        return train_billes(mes_pions, board,couleur, data)
    move_1_bille = coup_pour_un_pion_liste(mes_pions, board)        # déplacement d'une bille
    move = train_billes(mes_pions, board,couleur, move_1_bille)     # liste des meilleurs coups possible selon notre IA
    return move


def coup_pour_un_pion_liste(mes_pions, board):
    """
    cette fonctions renvoie tous les moves qui sont fait en bougeant 1 seul pion

    entrée : liste des pions du joueur et le plateau
    sortie : dictionnaire reprenant en clé le pion qui bouge et en valeur les cases sur lesquels il peut aller
    """
    move = []
    for pion in mes_pions:
        liste_cases_autour = case_autour_pion(pion)[0]
        liste_directions = case_autour_pion(pion)[1]
        i=0
        for mouvement in liste_cases_autour:
            direction = liste_directions[i]
            i+=1
            if sur_plateau(mouvement) == True:
                if etat_de_la_case(board, mouvement)=="E":
                    move += [[[pion], direction]]
    return move


def train_billes(mes_pions, board, ma_couleur, data):
    """
    cette fonction renvoie tous les meilleurs mouvements possibles de plusieurs billes (2 et 3 billes)
    et les attaques et kills possible   
    
    entrées : billes du joueur (list), le plateau (list), la couleur du joueur (str), data qui demande un mouvement ou un message
    sorties : liste comprenant en boucle: une liste des trains de billes qui bougent puis un string de la directions dans laquelle ils bougent
    """
    move_2 = []
    move_3 = []
    attack = []
    ball_pushed = []
    kill = []
    couleur_adverse = couleur_adversaire(ma_couleur)

    # partie train de 2 billes
    for case1 in mes_pions:
        cases_autour_position = case_autour_pion(case1)[0]
        i=0
        for case2 in cases_autour_position:
            etat_case2 = etat_de_la_case(board, case2)
            direction = case_autour_pion(case1)[1][i]
            i+=1
            if etat_case2 == ma_couleur:                           # 2e bille est à moi
                case3 = case_suivante(case2, direction)
                etat_case3 = etat_de_la_case(board, case3)
                if etat_case3 == "E":
                    move_2 += [[[case1,case2],direction]]
                elif etat_case3 == couleur_adverse:                 # 3e bille est adverse
                    case4 = case_suivante(case3, direction)
                    etat_case4 = etat_de_la_case(board, case4)
                    if etat_case4 == "E":
                        ball_pushed.append([case3, [[case1,case2], direction]])
                        move_2 += [[[case1,case2],direction]]
                        attack += [[[case1,case2],direction]]
                    if sur_plateau(case4)== False:                          # ATTENTION coup KILL  :)
                        kill += [[[case1,case2],direction]]
                
                # partie train de 3 billes
                elif etat_case3 == ma_couleur:                      # 3e bille est à moi
                    case4 = case_suivante(case3, direction)
                    etat_case4 = etat_de_la_case(board, case4)
                    if etat_case4 == "E":
                        move_3 += [[[case1,case2,case3],direction]]
                    elif etat_case4 == couleur_adverse:             # 4e bille est adverse
                        case5 = case_suivante(case4, direction)
                        etat_case5 = etat_de_la_case(board, case5)
                        if etat_case5 == "E":
                            ball_pushed.append([case4, [[case1,case2,case3], direction]])
                            move_3 += [[[case1,case2,case3], direction]]
                            attack += [[[case1,case2,case3], direction]]
                        elif sur_plateau(case5)== False:
                            kill += [[[case1,case2,case3], direction]]        # ATTENTION coup KILL  :)
                        elif etat_case5 == couleur_adverse:             # 5e bille est adverse
                            case6 = case_suivante(case5, direction)
                            etat_case6 = etat_de_la_case(board, case6)
                            if etat_case6 == "E":
                                ball_pushed.append([case6, [[case1,case2,case3], direction]])
                                move_3 += [[[case1,case2,case3], direction]]
                                attack += [[[case1,case2,case3], direction]]
                            elif sur_plateau(case6)== False:                # ATTENTION coup KILL  :)
                                kill += [[[case1,case2,case3], direction]]
    if data == "message" :
        return kill != []
    else :
        move = data + move_2 + move_3 + kill
        best_move = AI(move, attack, ball_pushed, kill, move_2, move_3, board, ma_couleur, couleur_adverse)
        return best_move

def AI(move, attack, ball_pushed, kill, move_2, move_3, board, ma_couleur, couleur_adverse) :              #priorité dans l'ordre
    """
    cette fonction renvoit la liste des meilleurs coups en triant la liste de tous les coups possibles avec des conditions
    possèdant un ordre de priorité
    """
    stay_safe = []
    secure_ball = []
    secure_corner = []
    save_ball = []
    dangerous_opponent = []
    protection=[]
    save_and_secure_ball = []
    push_opponent = []
    center_ball = []
    ball_together = []
    safe_move = []
    train_3 = []
    train_2 = []
    Best_move = move
    if kill != [] :
        Best_move = kill                                                        # 1) kill une bille
    for i in Best_move :
        case = i[0][0]
        next_case = case_suivante(case, i[1])
        if corner(case) == True :
            if last_row(next_case) == False :
                secure_corner.append(i)
        if last_row(case) == True :
            if last_row(next_case) == False :
                secure_ball.append(i)
            if danger(case, board, ma_couleur, couleur_adverse) != [] :
                if last_row(next_case) == False :
                    save_and_secure_ball.append(i)
                else :
                    cases_opponent = danger(case, board, ma_couleur, couleur_adverse)
                    for k in cases_opponent :
                        dangerous_opponent.append(k)
                for j in i[0] :
                    each_next_case = case_suivante(j, i[1])
                    if danger(each_next_case, board, ma_couleur, couleur_adverse) == [] :
                        save_ball.append(i)
        last_case = i[0][len(i[0])-1]
        next_last_case = case_suivante(last_case, i[1])
        if last_row(next_last_case) == False :
            stay_safe.append(i)
    if dangerous_opponent != [] :
        for i in dangerous_opponent :
            for j in ball_pushed :
                print("FFFFFFF"+str(i)+str(j))
                if j[0] == i :
                    protection.append(j[1])
    if stay_safe != [] :
        Best_move = stay_safe                                                   # 7) rester en sécurité en n'allant pas sur la dernière ligne
    if secure_ball != [] :
        Best_move = secure_ball                                                 # 6) sécuriser une bille de la dernière ligne
    if secure_corner != [] :
        Best_move = secure_corner                                               # 5) sécuriser une bille d'un coin
    if save_ball != [] :
        Best_move = save_ball                                                   # 4) sauver une bille de la dernière ligne
    if protection != [] :
        Best_move = protection                                                  # 3) sauver en attaquant la train adverse
    if save_and_secure_ball != [] :
        Best_move = save_and_secure_ball                                        # 2) sauver et sécuriser une bille de la dernière ligne
    for i in Best_move :
        case = i[0][len(i[0])-1]
        next_case = case_suivante(case, i[1])
        cases_autour_position = case_autour_pion(next_case)[0]
        n=0
        for case1 in cases_autour_position :
            if etat_de_la_case(board, case1) == ma_couleur :
                n+=1
        if n>1 :
            ball_together.append(i)
    if ball_together != [] :
        Best_move = ball_together                                               # 8) éviter la dispersion
    for i in Best_move :
        if i in attack :
            push_opponent.append(i)
    if push_opponent != [] :
        Best_move = push_opponent                                               # 9) pousser l'ennemi
    for i in Best_move :
        case = i[0][0]
        if Before_last_row(case) == True :
            next_case = case_suivante(case, i[1])
            if Before_last_row(next_case) == False :
                center_ball.append(i)
    if center_ball != [] :
        Best_move = center_ball                                                 # 10) centrer les billes lorsqu'il n'y a pas d'attaque possible
    for i in Best_move :
        case = i[0][len(i[0])-1]
        next_case = case_suivante(case, i[1])
        if safe(next_case, board, couleur_adverse) == True :
            safe_move.append(i)
    if safe_move != [] :
        Best_move = safe_move                                                   # 11) restreint le nombre de possibilités de se faire pousser
    for i in Best_move :
        if i in move_3 :
            train_3.append(i)
        if i in move_2 :
            train_2.append(i) 
    if train_2 != [] :
       Best_move = train_2                                                      # 13) favoriser train de 2 billes 
    if train_3 != [] :
        Best_move = train_3                                                     # 12) favoriser train de 3 billes
    return Best_move

def danger(case, board, ma_couleur, couleur_adverse) :
    """
    permet de savoir pour une case si elle est attaquable par l'adversaire
    """
    res=[]
    cases_autour_position = case_autour_pion(case)[0]
    i=0
    for case1 in cases_autour_position :
        direction = case_autour_pion(case)[1][i]
        i+=1
        if etat_de_la_case(board, case1) == couleur_adverse :
            case2 = case_suivante(case1, direction)
            if etat_de_la_case(board, case2) == couleur_adverse :
                case3 = case_suivante(case2, direction)
                res.append(case3)
                if etat_de_la_case(board, case3) != couleur_adverse :
                    res.append(case2)
        if etat_de_la_case(board, case1) == ma_couleur :
            case2 = case_suivante(case1, direction)
            if etat_de_la_case(board, case2) == couleur_adverse :
                case3 = case_suivante(case2, direction)
                if etat_de_la_case(board, case3) == couleur_adverse :
                    case4 = case_suivante(case3, direction)
                    if etat_de_la_case(board, case4) == couleur_adverse :
                        case5 = case_suivante(case4, direction)
                        res.append(case5)
                        res.append(case4)
                        res.append(case3)
    return res

def safe(case, board, couleur_adverse) :
    """
    permet de savoir si on risque de se faire pousser par un train de 2 billes
    """
    cases_autour_position = case_autour_pion(case)[0]
    i=0
    for case1 in cases_autour_position :
        direction = case_autour_pion(case)[1][i]
        i+=1
        if etat_de_la_case(board, case1) == couleur_adverse :
            case2 = case_suivante(case1, direction)
            if etat_de_la_case(board, case2) == couleur_adverse :
                if direction == "W" :
                    direction_inverse = "E"
                if direction == "NW" :
                    direction_inverse = "SE"
                if direction == "NE" :
                    direction_inverse = "SW"
                if direction == "E" :
                    direction_inverse = "W"
                if direction == "SE" :
                    direction_inverse = "NW"
                if direction == "SW" :
                    direction_inverse = "SE"
                case0 = case_suivante(case, direction_inverse)
                if etat_de_la_case(board, case0) == "E" :
                    return False
    return True

def last_row(case) :
    """
    permet de vérifier si une bille est dans la dernière ranger du plateau
    """
    last_row = [[0,0], [0,1], [0,2], [0,3], [0,4], [1,0], [1,5], [2,0], [2,6], [3,0], [3,7], [4,0], [4,8], [5,1], [5,8], [6,2], 
    [6,8], [7,3], [7,8], [8,4], [8,5], [8,6], [8,7], [8,8]]
    return case in last_row

def corner(case):
    """
    permet de vérifier si une bille est dans un coin du plateau
    """
    corner = [[0,0], [0,4], [4,0], [4,8], [8,4], [8,8]]
    return case in corner

def Before_last_row(case) :
    """
    permet de vérifier si une bille est dans l'avant-dernière ranger du plateau
    """
    Before_last_row = [[1,1], [1,2], [1,3], [1,4], [2,1], [2,5], [3,1], [3,6], [4,1], [4,7], [5,2], [5,7], [6,3], [6,7], [7,4], 
    [7,5], [7,6], [7,7]]
    return case in Before_last_row

def ma_couleur(state):
    """
    cette fonction renvoie la couleur des pions du joueur

    entrée : state
    sortie : couleur du joueur soit "B" pour noir soit "W" pour blanc
    """
    couleur = ""
    if state["current"] == 0:        # jouer numéro 1 a les pions noirs
        couleur = "B"
    elif state["current"] == 1:       # joueur deux à les pions blancs
        couleur = "W"
    return couleur


def pion_du_joueur(board, couleur):
    """
    cette fonction renvoie une liste des pions du joueur

    enntrée : plateau et couleur du joueur
    sortie : pions du joueur (liste)
    """
    mes_pions = []
    x=0
    for i in board:
        y=0
        for j in i:
            if j == couleur:
                mes_pions += [[x,y]]
            y+=1
        x+=1
    return mes_pions


def case_autour_pion(pion):
    """
    cette fonction retrouve toutes les cases à coté d'une case (qui sera généralement une bille)

    entrée : position du pion (liste)
    sortie : liste contenant une liste avec la postion des cases autour (liste) et une liste avec le nom de la direction (liste)
    """
    # définitions des directions  premiere valeur changement de ligne, deuxieme valeur changment de colonne
    direction_W = [0, -1]
    direction_NW = [-1, -1]
    direction_NE = [-1, 0]
    direction_E = [0, +1]
    direction_SE = [+1, +1]
    direction_SW = [+1, 0]
    case_W = [pion[0] + direction_W[0],pion[1] + direction_W[1]]
    case_NW = [pion[0] + direction_NW[0],pion[1] + direction_NW[1]]
    case_NE = [pion[0] + direction_NE[0],pion[1] + direction_NE[1]]
    case_E = [pion[0] + direction_E[0],pion[1] + direction_E[1]]
    case_SE = [pion[0] + direction_SE[0],pion[1] + direction_SE[1]]
    case_SW = [pion[0] + direction_SW[0],pion[1] + direction_SW[1]]
    return [[case_W, case_NW, case_NE, case_E, case_SE, case_SW], ["W","NW","NE","E","SE","SW"]]


def sur_plateau(case):
    """
    cette fonction vérifie si une case est dans le plateau ou pas. Si la case est dans le plateau la fonction renvoie True
    sinon la fonction renvoie False

    entrée : case (liste)
    sorrtie : booléen True si danns le plateur, False si hors plateau 
    """
    hors_plateau = [[-1,-1], [-1,0], [-1,1], [-1,2], [-1,3], [-1,4], [-1,5], [0,5], [0,6], [1,6], [1,7], [2,7], [2,8], [3,8], [3,9], 
    [4,9], [5,9], [6,9], [7,9], [8,9], [9,9], [9,8], [9,7], [9,6], [9,5], [9,4], [9,3], [8,3], [8,2], [7,2], [7,1], [6,1], [6,0], [5,0],
    [5,-1], [4,-1], [3,-1], [2,-1], [1,-1], [0,-1]]
    return case not in hors_plateau


def etat_de_la_case(board, case):
    """
    fonction qui indique ce que contient une case: soit la case est vide "E" soit il y a un pion blanc "W" ou noir "B"
    soit la case est hors plateau "X"

    entrée : tableau et la case à vérifier (liste)
    sortie : string : "W" ou "B" ou "E" ou "X"
    """
    if sur_plateau(case) == True:
        res = board[case[0]][case[1]]
    else:                                           
        res = "X"
    return res


def direction_du_coup(case1, case2):
    """
    cette fonction retrouve la direction entre 2 cases (de la première vers la deuxième)

    entrée : les 2 cases (liste)
    sortie : direction (string, exemple: "NE")
    """
    direction ="rien"
    différence = [case1[0] - case2[0], case1[1] - case2[1]]
    if différence==[0, 1]:
        direction = "W"
    elif différence==[1, 1]:
        direction = "NW"
    elif différence==[1, 0]:
        direction = "NE"
    elif différence==[0, -1]:
        direction = "E"
    elif différence==[-1, -1]:
        direction = "SE"
    elif différence==[-1, 0]:
        direction = "SW"
    return direction


def case_suivante(case, direction):
    """
    fonction qui indique la case qui suit une case selon une direction

    entrée : case d'avant (liste) et direction (string de type "NE")
    sortie : la case suivante dans la direction donnée (liste)
    """
    direction_W = [0, -1]
    direction_NW = [-1, -1]
    direction_NE = [-1, 0]
    direction_E = [0, +1]
    direction_SE = [+1, +1]
    direction_SW = [+1, 0]
    if direction == "W":
        case_apres = [case[0] + direction_W[0],case[1] + direction_W[1]]
    elif direction == "NW":
        case_apres = case_NW = [case[0] + direction_NW[0], case[1] + direction_NW[1]]
    elif direction == "NE":
        case_apres = case_NE = [case[0] + direction_NE[0], case[1] + direction_NE[1]]
    elif direction == "E":
        case_apres = case_E = [case[0] + direction_E[0], case[1] + direction_E[1]]
    elif direction == "SE":
        case_apres = case_SE = [case[0] + direction_SE[0], case[1] + direction_SE[1]]
    elif direction == "SW":
        case_apres = case_SW = [case[0] + direction_SW[0], case[1] + direction_SW[1]]
    return case_apres


def couleur_adversaire(ma_couleur):
    """
    fonction qui indique la couleur des pions de l'adversaire

    entrée : ma couleur "W" ou "B"
    sortie : couleur de l'autre jouer "W" ou "B"
    """
    if ma_couleur == "W":
        couleur_adverse = "B"
    elif ma_couleur == "B":
        couleur_adverse = "W"
    return couleur_adverse

def aléatoire(moves):
    """
    fonction qui renvoie un coup aléatoire parmis tous les coups
    
    entrée : moves (list), liste des coups
    sorties : un seul coup pris aléatoirement (list)
    """
    coup_aléatoire = random.choice(moves) 
    return coup_aléatoire

   
def move_list_to_json(move):
    """
    cette fonction transforme le coup sous forme de liste en coup en fichier json

    entrée : coup (list)
    sortie : coup (json)
    """
    billes = move[0]
    direction = move[1]
    move_json = {
        "marbles": billes,
        "direction": direction
    }
    return move_json

if __name__ == '__main__' :
    """
    la programme commence ici, il récupère le port (écrit en argument dans terminal) sur le quel il doit écouter
    """
    arg = sys.argv[1]
    s0 = socket.socket()
    port = int(arg)
    subscribe(port, s0)
    listen(port)