import requests

IP_ROBOT = "192.168.137.92"  # L'IP de ton amie

try:
    # On teste juste si le serveur répond
    response = requests.get("http://" + IP_ROBOT + ":5000/", timeout=3)
    print("Connexion reussie ! Code : " + str(response.status_code))
except Exception as e:
    print("Connexion echouee : " + str(e))
    print("Verifie que :")
    print("- Vous etes sur le meme reseau WiFi")
    print("- Le serveur Flask est bien lance")
    print("- L'IP est correcte")