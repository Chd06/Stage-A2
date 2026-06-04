#Permettra d'acquérir les données en temps réel 
import os
os.add_dll_directory(r"C:\Users\Cesi\Documents\gtec\Unicorn Suite\Hybrid Black\Unicorn Python\Lib")
import UnicornPy
import numpy as np 
from scipy.signal import butter, filtfilt
from numpy.fft import rfft, rfftfreq
# import requests 
import csv #Pour pouvoir enregistrer les données en fichier CSV
from datetime import datetime #Pour ajouter un timestamp au nom du fichier CSV

SAUVEGARDER = True # Ce sera False quand on voudra désactiver la sauvegarder 
FREQUENCE =  250 # Fréquence d'échantillonnage
FENETRE_SEC = 3
FREQS_CIBLES =[(13,"haut"), (15,"bas"), (17,"gauche"), (20,"droite")]
# IP_PC = "192.168.137.92" # Adresse  IP du robot 

def appliquer_filtre(signal, freq_min, freq_max, freq_echantillonnage):
    nyquist = freq_echantillonnage /2
    b, a = butter(4,[freq_min/nyquist,freq_max/nyquist], btype="band") #On utilise un filtre de Butterworth d'ordre 4 pour une bonne atténuation des fréquences indésirables
    return filtfilt(b, a, signal)

# Fonction qui va nous permettre de pouvoir envoyer une commande directionnelle au robot vec l'API Flask 
"""def envoyer_commande(direction):
    try : 
        response = requests.post(
            "http://" + IP_PC + ":5000/commande", 
            json = {"direction": direction}, 
            timeout = 1 #On attends max 1 seconde pour ne pas bloquer la détection
        )
        print("Commande envoyee au robot :" + direction)
    except Exception as e:
        print("Erreur connexion robot : " + str(e))

#Pour envoyer une commande stop au robot
def arreter_robot(): 
    try: 
        requests.post(
            "http://" + IP_PC + ":5000/stop_robot", 
            timeout  =1
        )
        print("Robot à l'arrêt.")
    except Exception as e: 
        print("Erreur stop robot :" + str(e))"""

deviceList = UnicornPy.GetAvailableDevices(True) # Afin d'obtenir la liste d'appareils disponibles 

if len(deviceList) <= 0 or deviceList is None:
    print("Aucun casque trouvé. Veuillez vérifier la connexion Bluetooth.")
else : 
    print("Casques disponibles :")
    for i, device in enumerate(deviceList):
        print(str(i) + " : " + device)

    deviceID = int(input("Selectionnez le casque par son numero :"))
    device = UnicornPy.Unicorn(deviceList[deviceID])
    print("Connecte a :" + deviceList[deviceID])

    # -- DEMARRAGE DE L'ACQUISITION -- #
    device.StartAcquisition(False) #False pour ne pas activer les signaux de test
    print("Acquisition en cours... Appuyez sur Ctrl+C pour arrêter.")

    taille_buffer = FREQUENCE * FENETRE_SEC #On prends une taille de buffer de 1250 points (5 secondes à 250Hz)
    buffer = [] #Buffer pour stocker les données en temps réel
    nb_canaux_total = device.GetNumberOfAcquiredChannels() #Pour pouvoir obtenir le vrai nombre de canaux
    taille_bloc = nb_canaux_total * 4
    receiveBuffer = bytearray(taille_bloc) #Buffer pour recevoir les données brutes
    print("Nombre total de canaux : " + str(nb_canaux_total))

    try:
        if SAUVEGARDER : 
            nom_fichier = "enregistrement_" + datetime.now().strftime("%d_%m_%Y_%H_%M") + ".csv"
            fichier_csv = open(nom_fichier, "w", newline="")
            writer = csv.writer(fichier_csv)
            writer.writerow(["EEG1", "EEG2", "EEG3", "EEG4", "EEG5", "EEG6", "EEG7", "EEG8"]) #Ecrire les en-têtes de colonnes dans le fichier CSV
            print("Sauvegarde dans :" + nom_fichier)
        while True : 
            device.GetData(1, receiveBuffer, taille_bloc) #On récupère un bloc de données (1 point pour chaque canal)
            data = np.frombuffer(receiveBuffer, dtype =np.float32) #On convertit les données en tableau numpy de float32
            buffer.append(data[:8]) #On ajoute les données des 8 canaux au buffer
            if SAUVEGARDER :
                writer.writerow(data[:8].tolist()) #On écrit les données dans le fichier CSV au fur et à mesure de leur acquisition

            if len(buffer) >= taille_buffer: 
                donnees = np.array(buffer) #Convertissons le buffer en tableau numpy, on va empiler la liste de tableaux en une matrice (1250,8)
                
                #On va récupérer les 3 canaux occipitaux et filtrer les 3 canaux 
                ch6 = appliquer_filtre(donnees[:, 5] - np.mean(donnees[:, 5]), 10, 25, FREQUENCE)
                ch7 = appliquer_filtre(donnees[:, 6] - np.mean(donnees[:, 6]), 10, 25, FREQUENCE)
                ch8 = appliquer_filtre(donnees[:, 7] - np.mean(donnees[:, 7]), 10, 25, FREQUENCE)

                # Moyenne des 3 canaux 
                ch_moyen = (ch6 + ch7 + ch8) / 3

                # Transformée de Fourvier 
                transformee = abs(rfft(ch_moyen))
                frequences = rfftfreq(len(ch_moyen), 1/FREQUENCE)

                # On regarde entre 11 et 24 Hz
                masque = (frequences >= 11) & (frequences <= 24) 
                frequences_utiles = frequences[masque]
                amplis_utiles = transformee[masque]

                #eExtraction du pic et de sa puissance 
                idx_max = np.argmax(amplis_utiles)
                freq_dominante = frequences_utiles[idx_max]
                puissance_pic = amplis_utiles[idx_max]

                # Pour vérifier si l'on est proche d'une des fréquences cibles 
                detection = "inconnu" 
                """if detection != "inconnu":
                    envoyer_commande(detection)
                else : 
                    arreter_robot()"""
                
                SEUIL_MIN = 20.0 # Seuil de puissance pour considérer qu'une détection est valide
                if puissance_pic > SEUIL_MIN:
                    for fc, label in FREQS_CIBLES:
                        if abs(freq_dominante - fc) < 1.5 : #On vérifie si la fréquence dominante est proche d'une fréquence cible (avec une tolérance de 1.5 Hz pour tenir compte des variations): 
                            detection = label +"("+ str(fc) + "Hz)"
                            break 
                else : 
                    detection = "Aucun signal fort (Bruit de fond)"   

                print(f"Freq dominante: {round(freq_dominante, 1)} Hz | Amp: {round(puissance_pic, 1)} >>> Ordre: {detection}")

                # Vider le buffer 
                buffer = []

    except KeyboardInterrupt:
        print("Acquisition arrêtée par l'utilisateur.")

    finally:
        device.StopAcquisition() #On arrête l'acquisition
        del device
        print("Deconnecte du casque.")
        if SAUVEGARDER : 
            fichier_csv.close() #On ferme le fichier CSV
            print("Fichier sauvegarde : " + nom_fichier)



