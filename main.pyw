import sys
import os
from time import sleep

# Ajout du chemin racine au PYTHONPATH
root_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.append(root_dir)

from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtGui import QIcon, QPixmap,Qt


def main():
    """Point d'entrée principal de l'application"""
    # Vérifier/créer les dossiers nécessaires
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    
    # QApplication DOIT être créée avant tout import de widgets
    app = QApplication(sys.argv)
    
    # Import après QApplication
    from src.widgets.main_window import MainWindow
    from src.config import STYLE_FILE, ICON_FILE
    from src.utils.config_manager import config_manager
    from src.utils.auth_manager import auth_manager
    
    # Initialiser le gestionnaire d'authentification
    # Cela va créer la base par défaut avec l'utilisateur administrateur si elle n'existe pas
    print("Initialisation du système d'authentification...")
    
    # Initialiser le gestionnaire de configuration
    print(f"Configuration chargée:")
    print(f"- Base de données: {config_manager.get_database_path()}")
    print(f"- Fichier isotopes: {config_manager.get_isotopes_path()}")
    print(f"- Dossier interventions: {config_manager.get_interventions_path()}")
    print(f"- Base d'authentification: {auth_manager.db_path}")

    # Configuration de l'icône
    app.setWindowIcon(QIcon(ICON_FILE))
    
    # Application du style
    try:
        with open(STYLE_FILE, 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())
    except Exception as e:
        print(f"Erreur lors du chargement du style: {e}")
    
    # Création du splash screen
    splash_path = os.path.join(os.path.dirname(__file__), "resources", "images", "splash_screen.png")
    splash_pix = QPixmap(splash_path)
    splash_pix = splash_pix.scaled(400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.show()
    
    # Pause pour le splash screen
    app.processEvents()
    sleep(2)
    
    # Création de la fenêtre principale
    window = MainWindow()
    window.show()
    

    splash.finish(window)
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())