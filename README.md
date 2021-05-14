# IA-Winner

Cette intelligeance artificielle est un programme client destiné à jouer sur le serveur disponible par le lien : 

https://github.com/qlurkin/PI2CChampionshipRunner#readme

## Déroulement

L'IA s'inscrit sur un seveur. Dès que deux clients sont inscrits, le serveur commence à faire jouer les matchs.

Chaque participants affrontera tous les autres deux fois, une fois en temps que premier joueur et une fois en temps que deuxième joueur.

Pendant un match, le serveur interroge les joueurs tour à tour pour savoir quel coups ils veulent jouer.

Il est possible d'inscrire 2 fois une même IA pour qu'elle joue contre elle même.

## Comunication

Tous les échanges entre l'IA et le serveur se font par des communications réseaux TCP en mode texte. Le contenu des messages sera toujours des objects JSON.

## Démarrer l'IA

```shell
python IA_Winner.py <port>
```

Le port ne peut pas être 3000 car c'est le port du serveur.

## Listes des requêtes / réponse

###Inscription

requêtes envoyé au serveur :

```json
{
  "request": "subscribe",
  "port": 4000,
  "name": "IA_Winner
  "matricules": ["19195", "19016"]
}
```

L'IA imprime la réponse du serveur qui est si tout est ok :

```json
{
  "reponse": "ok"
}
```

### requête de ping

L'IA doit confirmé qu'il est bien connecté avant chaque match. Le serveur lui envoie la requête :

```json
{
  "request": "ping"
}
```

L'IA répond :

```json
{
   "response": "pong"
}
```

### requête de coup

Cette requête permet au serveur de donner à un client létat du plateau et de lui demander quelle coup il joue.

La requête faite par le serveur au client est:

```json
{
   "request": "play",
   "lives": 3,
   "errors": list_of_errors,
   "state": {
     "players": ["LUR", "LRG"],
     "current": 0,
     "board": [
        ["W", "W", "W", "W", "W", "X", "X", "X", "X"],
        ["W", "W", "W", "W", "W", "W", "X", "X", "X"],
        ["E", "E", "W", "W", "W", "E", "E", "X", "X"],
        ["E", "E", "E", "E", "E", "E", "E", "E", "X"],
        ["E", "E", "E", "E", "E", "E", "E", "E", "E"],
        ["X", "E", "E", "E", "E", "E", "E", "E", "E"],
        ["X", "X", "E", "E", "B", "B", "B", "E", "E"],
        ["X", "X", "X", "B", "B", "B", "B", "B", "B"],
        ["X", "X", "X", "X", "B", "B", "B", "B", "B"]
     ]
  }
}
```

L'IA lui répond :

```json
{
   "response": "move",
   "move": {
      "marbles": [[1, 1], [2, 2]],
      "direction": "SE"
   },
   "message": "Fun message"
}
```

L'IA peut aussi abandonné si il n'y a plus aucun coup possible malgré que ce n'est pas sensé arriver. Il envoit alors :

```json
{
   "response": "giveup",
}
```

## Le choix du coup

### Respect des règles

L'IA définit d'abord une liste exhaustive des coups possibles. Ainsi il empêche les "bad moe".

### Intelligeance artificielle

l'IA fait un tri dans la liste des coups possible en suivant certaine conditions prioritaires. Les conditions dans leur ordre de priorité :
1) éjecte une bille
2) sauve et sécurise une bille en danger de la dernière ligne
3) sauve en attaquant le train de billes adverse représentant le danger
4) sauve une bille en danger de la dernière ligne
5) sécurise une bille se trouvant dans une des 6 cases formant les coins
6) sécurise une bille se trouvant sur la dernière ligne
7) reste en sécurité en ne déplaçant pas une bille sur la dernière ligne
8) évite la dispersion de ses propres billes
9) pousse l'ennemi
10) centrer les billes (lorsqu'il n'y a pas d'attaque possible)
11) restreint le nombre de possibilités de se faire pousser
12) favorise les trains de 3 billes
13) favorise les trains de 2 billes
