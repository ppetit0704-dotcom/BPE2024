"""
@author : Philippe PETIT
@version : 1.0.0
@description : Lanceur BPE2026
"""
import streamlit.web.cli as stcli
from threading import Timer
import os, sys, webbrowser
import multiprocessing
import psutil 
import subprocess
import threading

def open_browser():
    """Ouvre le navigateur après un court délai pour laisser le serveur démarrer"""
    webbrowser.open("http://localhost:8501")

def kill_port(port: int):
    """Tue proprement tout process écoutant sur le port donné"""
    killed = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            for conn in proc.net_connections(kind='inet'):
                if conn.laddr.port == port:
                    proc.kill()
                    killed.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    if killed:
        print(f"⛔ Process tués sur le port {port} : PID {killed}")
    else:
        print(f"✅ Port {port} libre.")

def get_resource_path(relative_path):
    """ Récupère le chemin absolu vers la ressource, compatible avec PyInstaller et le dev local """
    try:
        # PyInstaller crée un dossier temporaire et stocke le chemin dans _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # NOUVEAU : On cible le dossier exact où se trouve run_app.py
        base_path = os.path.dirname(os.path.abspath(__file__))
        
    return os.path.join(base_path, relative_path)


if __name__ == "__main__":
    # <-- NOUVEAU : Empêche l'ouverture infinie de fenêtres sur Windows
    multiprocessing.freeze_support() 

    # On récupère le chemin dynamique de app.py à l'intérieur du pack
    app_path = get_resource_path("app.py")

    # Pour le debug : si on est dans l'exe, on affiche où il cherche
    print(f"DEBUG: Recherche de app.py ici -> {app_path}")

    # --- NETTOYAGE DU PORT AVANT LANCEMENT ---
    print("🔍 Vérification du port 8501...")
    kill_port(8501)

    # Optionnel : Ajouter un message dans la console pour rassurer l'utilisateur
    print("🚀 Initialisation du Dashboard BPE...")
    print("Veuillez patienter, le navigateur va s'ouvrir automatiquement.")
    
    if not os.path.exists(app_path):
        print(f"Erreur : Impossible de trouver {app_path}")
        sys.exit(1)


    # 2. Ouvrir le navigateur après délai    
    Timer(8, open_browser).start()

    if not os.path.exists(app_path):
        print(f"Erreur : Impossible de trouver {app_path}")
        sys.exit(1)

    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--server.port=8501",        # Fixe le port pour éviter les doublons
        "--server.headless=true",    # Empêche Streamlit de forcer l'ouverture du navigateur si déjà ouvert
        "--global.developmentMode=false",
        "--server.runOnSave=false",
        "--server.fileWatcherType=none",
    ]
    sys.exit(stcli.main())