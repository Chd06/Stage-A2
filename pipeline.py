import pandas as pd # On utilise la bibliothèque pandas pour lire le fichier CSV et manipuler les données de manière efficace.
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import butter, filtfilt
from numpy.fft import rfft, rfftfreq
import os 

# FICHIER = "UnicornRecorder_29_04_2026_15_26_180.csv"
DOSSIER = "enregistrements_recorder2" # Nom du dossier

fichiers = [f for f in os.listdir(DOSSIER) if f.endswith(".csv")]
print("Fichiers trouvés :", fichiers)
FENETRE = 5 
FREQ = 250 # Vu que chaque ligne = 1/250 secondes

# Filtre passe-bande 
def appliquer_filtre(signal, freq_min, freq_max, freq_echantillonnage):
    nyquist = freq_echantillonnage /2
    b, a = butter(4,[freq_min/nyquist,freq_max/nyquist], btype="band") #On utilise un filtre de Butterworth d'ordre 4 pour une bonne atténuation des fréquences indésirables
    signal_filtre = filtfilt(b, a, signal) #On utilise filtfilt pour appliquer le filtre dans les deux sens et éviter les décalages de phase
    return signal_filtre

#-- LECTURE DU FICHIER -- #
df = pd.read_csv(os.path.join(DOSSIER, fichiers[0]))
df = df.iloc[1250:] #On obtiens 1250 parce que le casque enregistre 250 mesures par seconde (250 *5 = 1250), on va ignorer les 5 premières secondes vu que le casque n'est pas stable au début
df = df.reset_index(drop=True) #On réinitialise les index pour que la première ligne soit à l'index 0 

print("Duree : ", len(df)/FREQ, "secondes")

# -- RECUPERATION ET FILTRAGE DES CANAUX OCCIPITAUX -- #
# On va utiliser ".values" pour transformer la colonne en tableau numpy pour faciliter les calculs 
ch6 = appliquer_filtre(df[" EEG 6"].values, 0.5, 30, 250) #Vu qu'on cherche à faire un filtre entre 0.5 et 30Hz
ch7 = appliquer_filtre(df[" EEG 7"].values, 0.5, 30, 250)
ch8 = appliquer_filtre(df[" EEG 8"].values, 0.5, 30, 250)

#-- Fréquences cibles à détecter : --#
freqs_cibles =[(8,"haut"), (10,"bas"), (12,"gauche"), (15,"droite")]
couleurs_cibles = {8:"blue", 10:"orange", 12:"red", 15:"purple"} #Couleurs pour chaque fréquence cible 
puissances = {fc: [] for fc, _ in freqs_cibles}

# -- Découpage en fenêtre -- #
taille_fenetre = FENETRE * FREQ 
nb_fenetres = len(df) // taille_fenetre
print ("Il y a ", nb_fenetres, "fenetres de", FENETRE, "secondes")
print()

# -- BOUCLE D'ANALYSE -- #
for i in range(nb_fenetres):
    debut = i * taille_fenetre
    fin = debut + taille_fenetre

    # -- CREATION DES FENETRES POUR CHAQUE CANAL --#
    fenetre_ch6 = ch6[debut:fin]
    fenetre_ch7 = ch7[debut:fin]
    fenetre_ch8 = ch8[debut:fin]

    # -- CALCUL DE LA FFT -- #
    transformee = (abs(rfft(fenetre_ch6))+ abs(rfft(fenetre_ch7)) + abs(rfft(fenetre_ch8)))/3
    frequences = rfftfreq(taille_fenetre, 1/FREQ) #On peut prendre n'importe quelle fenêtre pour calculer les fréquences, elles ont toutes la même longueur


    # Boucle pour les fenêtres
    for fc, label in freqs_cibles:
       idx = np.argmin(np.abs(frequences - fc)) # Index le plus proche de fc

       # Signal c'est à dire amplitude à la fréquence cible
       amplitude_signal = transformee[idx]

       # Pour prendre le bruit on pfera la moyenne de 4 valeurs voisines : 2 de chaque côté de la valeur en excluant bien sûr la valeur cible
       voisins = transformee[[idx - 2, idx-1, idx+1, idx+2]]
       bruit_moyen = np.mean(voisins)

       # Calcul du SNR
       snr = amplitude_signal / bruit_moyen if bruit_moyen > 0 else 0 
       puissances[fc].append(snr) 

       print(f"Fenetre {i+1} ({i*FENETRE}s-{(i+1)*FENETRE}s) | {label}({fc}Hz) => SNR = {snr:.2f}")

# Pour afficher le pourcentage du SNR pour chaque flèche 
print("\n=== QUALITE DU SIGNAL ===")
for fc, label in freqs_cibles:
    snrs = puissances[fc]
    nb_au_dessus = sum(1 for s in snrs if s > 1.5)
    pourcentage = (nb_au_dessus / len(snrs)) * 100
    print(f"{label} ({fc}Hz) : {pourcentage:.1f}% des fenêtres avec SNR > 1.5")

# -- AFFICHAGE DES DONNEES -- #
temps_fenetres = [i * FENETRE + FENETRE/2 for i in range(nb_fenetres)]
fig, (ax1, ax2) = plt.subplots(2, 1, figsize = (14, 10))

# Graphique 1 :  
for fc, label in freqs_cibles :
    ax1.plot(temps_fenetres, puissances[fc], color=couleurs_cibles[fc], label=f"{label} ({fc}Hz)", linewidth=2, marker='o')
ax1.set_title("SNR aux fréquences cibles dans le temps")
ax1.set_xlabel("Temps(secondes)")   
ax1.set_ylabel("SNR (signal /bruit)")
ax1.axhline(y=1.0, color='black', linewidth=1, linestyle='--', label='Seuil bruit (SNR=1)')
ax1.legend()
ax1.grid(True)

# Graphique 2 : FFT globale 
ch_moyen = (ch6 + ch7 + ch8) / 3
transformee_globale = abs(rfft(ch_moyen))
frequences_globales = rfftfreq(len(ch_moyen), 1/FREQ)
masque = (frequences_globales >= 5) & (frequences_globales <=30)

ax2.plot(frequences_globales[masque], transformee_globale[masque], color = "gray", linewidth = 0.8) 
'''for fc, label in freqs_cibles:
    ax2.axvline(x = fc, color = couleurs_cibles[fc], linewidth = 1.5, linestyle = "--")
    ax2.text(fc + 0.2, ax2.get_ylim()[1] * 0.85, label, color=couleurs_cibles[fc], fontsize=8)'''
ax2.set_title("Spectre FFT global - moyenne Ch6 Ch7 Ch8")
ax2.set_xlabel("Fréquence (Hz)")
ax2.set_ylabel("Puissance")
ax2.grid(True)   

plt.tight_layout()
plt.show()