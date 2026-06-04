import pygame 
import time

# Initialisation de la fenêtre de simulation
pygame.init()
font = pygame.font.SysFont("Arial", 30) #On initialise une police pour afficher du texte 
LARGEUR, HAUTEUR = 800, 600
screen = pygame.display.set_mode((LARGEUR, HAUTEUR))
pygame.display.set_caption("Stimulus SSVEP") #Nom de la fenêtre
clock = pygame.time.Clock() #Initialisation de l'horloge pour contrôler le taux de rafraîchissement

#On va définir les 4 flèches dans un dictionnaire : 
fleches = {
    "haut": {"frequence": 8, "visible": True, "derniere_bascule":time.time()},
    "bas": {"frequence": 10, "visible": True, "derniere_bascule":time.time()},
    "gauche": {"frequence": 12, "visible": True, "derniere_bascule":time.time()},
    "droite": {"frequence": 15, "visible": True, "derniere_bascule":time.time()}   
}

textes = {
        "haut": "Avancer",
        "bas": "Reculer",
        "gauche": "Gauche",
        "droite": "Droite"
}

#Définissons une fonction pour dessiner la flèche 
def dessiner_fleche(direction, visible):
    if not visible:
        return #Si la flèche n'est pas visible (éteinte), on ne la dessine pas
    # Coordonnées du centre de l'écran :
    CX = LARGEUR // 2 #On divise 800//2 = 400 pixels (avec une divion en entier pour éviter les décimales)
    CY = HAUTEUR // 2 #On divise 600//2 = 300 pixels (avec une divion en entier pour éviter les décimales)
    MARGE = 170 #Distance entre le centre et la pointe de chaque flèche 
    T = 40 #Taille (c'est à dire la demi-largeur) de la base du triangle 

    if direction == "haut" :
        points = [
            (CX, CY - MARGE), #la pointe de la flèche 
            (CX - T, CY - MARGE  + T*2), #le coin gauche de la base, on descends de T*2 et on va à gauche de T
            (CX + T, CY - MARGE + T*2) #le coin droit de la base, on descends de T*2 et on va à droite de T 
        ]

        #Le texte se place sous la base du triangle 
        pos_texte = (CX, CY - MARGE - 40) 

    elif direction == "bas" :
        points = [
            (CX, CY + MARGE), #la pointe de la flèche 
            (CX - T, CY  + MARGE - T*2), #le coin gauche de la base, on monte de T*2 et on va à gauche de T
            (CX + T, CY + MARGE - T*2) #le coin droit de la base, on monte de T*2 et on va à droite de T 
        ]
        #Le texte se place au dessus de la base du triangle
        pos_texte = (CX, CY + MARGE + 10)

    elif direction == "gauche" :
        points = [
            (CX - MARGE, CY), #la pointe de la flèche 
            (CX - MARGE + T*2, CY - T), #le coin gauche de la base, on va à droite de T*2 et on monte de T
            (CX - MARGE + T*2, CY + T) #le coin droit de la base, on va à droite de T*2 et on descend de T 
        ]
        
        #Le texte se place au dessus de la base du triangle
        pos_texte = (CX - MARGE - 10, CY + T + 10)


    elif direction == "droite" :
        points = [
            (CX + MARGE, CY), #la pointe de la flèche 
            (CX + MARGE - T*2, CY - T), #le coin gauche de la base, on va à gauche de T*2 et on monte de T
            (CX + MARGE - T*2, CY + T) #le coin droit de la base, on va à gauche de T*2 et on descend de T 
        ]
        #Le texte se place au dessus de la base du triangle
        pos_texte = (CX + MARGE, CY + T + 10)

    pygame.draw.polygon(screen, (255,255, 255), points)

    surface_texte = font.render(textes[direction], True, (255,255,255)) #On rend le texte en blanc
    largeur_texte = surface_texte.get_width()     #On récupère la largeur du texte pour le centrer
    screen.blit(surface_texte, (pos_texte[0] - largeur_texte//2, pos_texte[1])) #On affiche le texte centré à la position définie (on soustrait la moitié)


#Boucle principale de la simulation 
running = True
while running:
    #Pour pouvoir quitter avec la croix ou avec Echap 
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False #Si l'on appuie sur la croix, on arrête la simulation
        if event.type == pygame.KEYDOWN : 
            if event.key  == pygame.K_ESCAPE:
                running = False #Si l'on appuie sur Echap, on arrête la simulation

    maintenant = time.time() #On récupère le temps actuel

    #Ensuite on va gérer le clignotement 
    for direction, params in fleches.items() :
        intervalle = 1/ (params["frequence"]*2) #Ici intervalle = Une demi période (c'est à dire le temps entre "visible" et "non visible")

        if maintenant - params["derniere_bascule"] >= intervalle :
            params["visible"] = not params["visible"] #On inverse l'état de la flèche 
            params["derniere_bascule"] = maintenant #On met à jour le temps de la dernière bascule 
    
    #Paramètre du dessin 
    screen.fill((0,0,0)) #Fond noir 
    for direction, params in fleches.items():
        dessiner_fleche(direction, params["visible"]) #On dessine chaque flèche si elle est visible

    pygame.display.flip() #On met à jour l'affichage
    clock.tick(120) #On limite à 120 images par seconde pour ne pas surcharger le processus 

pygame.quit() #On quitte pygame une fois la boucle terminée