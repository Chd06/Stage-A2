import pandas as pd # On utilise la bibliothèque pandas pour lire le fichier CSV et manipuler les données de manière efficace.
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import butter, filtfilt
from numpy.fft import rfft, rfftfreq

FICHIER = "UnicornRecorder_29_04_2026_15_26_180.csv"
FENETRE = 5 
FREQ = 250 # Vu que chaque ligne = 1/250 secondes

#-- LECTURE DU FICHIER -- #
df = pd.read_csv(FICHIER)
df = df.iloc[1250:] #On obtiens 1250 parce que le casque enregistre 250 mesures par seconde (250 *5 = 1250), on va ignorer les 5 premières secondes vu que le casque n'est pas stable au début
df = df.reset_index(drop=True) #On réinitialise les index pour que la première ligne soit à l'index 0 

print ("Fichier :", FICHIER)
print("Duree : ", len(df)/FREQ, "secondes")

# Filtre passe-bande 
def appliquer_filtre(signal, freq_min, freq_max, freq_echantillonnage):
    nyquist = freq_echantillonnage /2
    b, a = butter(4,[freq_min/nyquist,freq_max/nyquist], btype="band") #On utilise un filtre de Butterworth d'ordre 4 pour une bonne atténuation des fréquences indésirables
    signal_filtre = filtfilt(b, a, signal) #On utilise filtfilt pour appliquer le filtre dans les deux sens et éviter les décalages de phase
    return signal_filtre

# -- RECUPERATION ET FILTRAGE DES CANAUX OCCIPITAUX -- #
# On va utiliser ".values" pour transformer la colonne en tableau numpy pour faciliter les calculs 
ch6 = appliquer_filtre(df[" EEG 6"].values, 0.5, 30, 250) #Vu qu'on cherche à faire un filtre entre 0.5 et 30Hz
ch7 = appliquer_filtre(df[" EEG 7"].values, 0.5, 30, 250)
ch8 = appliquer_filtre(df[" EEG 8"].values, 0.5, 30, 250)
ch_moyen = (ch6 +ch7 + ch8)/3 #Moyenne des 3 canaux occipitaux 

couleurs ={"ch6": "blue", "ch7": "red", "ch8": "green"}

# Axe du temps :
temps = [i/FREQ for i in range(len(ch6))] # On crée une liste de temps correspondant à chaque mesure    

#-- Fréquences cibles à détecter : --#
freqs_cibles =[(8,"haut"), (10,"bas"), (12,"gauche"), (15,"droite")]
couleurs_cibles = {8:"blue", 10:"orange", 12:"red", 15:"purple"} #Couleurs pour chaque fréquence cible 


# -- Découpage en fenêtre -- #
taille_fenetre = FENETRE * FREQ 
nb_fenetres = len(df) // taille_fenetre
print ("Il y a ", nb_fenetres, "fenetres de", FENETRE, "secondes")
print()

resultats =[]

for i in range(nb_fenetres):
    debut = i * taille_fenetre
    fin = debut + taille_fenetre

    # -- CREATION DES FENETRES POUR CHAQUE CANAL --#
    fenetre_ch6 = ch6[debut:fin]
    fenetre_ch7 = ch7[debut:fin]
    fenetre_ch8 = ch8[debut:fin]

    # -- CALCUL DE LA FFT -- #
    transformee_ch6 = abs(rfft(fenetre_ch6))
    transformee_ch7 = abs(rfft(fenetre_ch7))
    transformee_ch8 = abs(rfft(fenetre_ch8))
    frequences = rfftfreq(len(fenetre_ch7), 1/FREQ) #On peut prendre n'importe quelle fenêtre pour calculer les fréquences, elles ont toutes la même longueur

    masque = (frequences >= 7) & (frequences <= 30) # On va récupérer les indices des fréquences entre 7 et 30 Hz
    frequences_utiles = frequences[masque]

    # -- CALCUL DE LA FREQUENCE MOYENNE SUR LES 3 CANAUX -- #
    amplis_moyennes = (transformee_ch6[masque] + transformee_ch7[masque] + transformee_ch8[masque]) / 3
    freq_dominante = frequences_utiles[np.argmax(amplis_moyennes)] #On trouve la fréquence dominante en prenant l'indice du maximum de l'amplitude moyenne

    # -- VERFICATION DE LA PRESENCE D'UNE FREQUENCE CIBLE -- #
    couleur_zone = "lightgray"
    label_zone = "inconnu"
    for fc, label in freqs_cibles:
        if abs(freq_dominante - fc) < 1.5: #On vérifie si la fréquence dominante est proche d'une fréquence cible (avec une tolérance de 1.5 Hz pour tenir compte des variations): 
            couleur_zone = couleurs_cibles[fc]
            label_zone = label +"("+ str(fc) + "Hz)"
            break 

    # Afficher dans la console
    print("Fenetre " + str(i+1) + " (" + str(i*FENETRE) + "s - " + str((i+1)*FENETRE) + "s) : " + str(round(freq_dominante, 1)) + " Hz  >>> " + label_zone)

    #Stocker le résultat pour l'affichage 
    resultats.append({
        "debut": i * FENETRE, #début en secondes 
        "fin": (i+1) * FENETRE, #fin en secondes
        "frequence": round(freq_dominante, 1), #fréquence dominante 
        "couleur": couleur_zone, #couleur de la zone 
        "label": label_zone #label

    })

# -- Affichage des données -- #
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8))

# -- Graphique 1 : Fréquence dominante par fenêtre dans le temps --
for r in resultats:
    milieu = (r["debut"] + r["fin"]) / 2  # Milieu de la fenêtre en secondes
    ax1.scatter(milieu, r["frequence"], color=r["couleur"], s=100, zorder=5)
    ax1.text(milieu, r["frequence"] + 0.3, r["label"], color=r["couleur"], fontsize=8, ha="center")

# Lignes horizontales pour chaque fréquence cible
for fc, label in freqs_cibles:
    ax1.axhline(y=fc, color=couleurs_cibles[fc], linewidth=1, linestyle="--", alpha=0.5)

ax1.set_title("Frequence dominante par fenetre")
ax1.set_xlabel("Temps (secondes)")
ax1.set_ylabel("Frequence (Hz)")
ax1.set_ylim(5, 20)
ax1.grid(True)

# -- Graphique 2 : FFT globale --
transformee_globale = abs(rfft(ch_moyen))
frequences_globales = rfftfreq(len(ch_moyen), 1/FREQ)
masque_global = (frequences_globales >= 7) & (frequences_globales <= 30)

ax2.plot(frequences_globales[masque_global], transformee_globale[masque_global], linewidth=0.8, color="gray")
ax2.set_title("Spectre FFT global - moyenne Ch6 Ch7 Ch8")
ax2.set_xlabel("Frequence (Hz)")
ax2.set_ylabel("Puissance")
ax2.set_xlim(7, 30)
ax2.grid(True)

for fc, label in freqs_cibles:
    ax2.axvline(x=fc, color=couleurs_cibles[fc], linewidth=1.5, linestyle="--")
    ax2.text(fc + 0.2, ax2.get_ylim()[1] * 0.85, label, color=couleurs_cibles[fc], fontsize=8)

plt.tight_layout()
plt.show()