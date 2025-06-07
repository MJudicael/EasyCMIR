import sys
import os
from time import sleep  # Ajout de l'import

# Ajout du chemin racine au PYTHONPATH
root_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.append(root_dir)

from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt
from src.widgets.main_window import MainWindow
from src.config import STYLE_FILE, ICON_FILE

def main():
    """Point d'entrée principal de l'application"""
    app = QApplication(sys.argv)
    
    # Création du splash screen
    splash_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                              "resources", "images", "easycmir_icon.png")
    splash_pix = QPixmap(splash_path)
    
    # Redimensionnement de l'image (ajustez les dimensions selon vos besoins)
    splash_pix = splash_pix.scaled(400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.show()
    
    # Application du style
    try:
        with open(STYLE_FILE, 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())
    except Exception as e:
        print(f"Erreur lors du chargement du style: {e}")
    
    # Configuration de l'icône
    app.setWindowIcon(QIcon(ICON_FILE))
    
    # Pause de 2 secondes pour afficher le splash screen
    app.processEvents()
    sleep(2)  # Maintenant sleep est défini
    
    # Création et affichage de la fenêtre principale
    window = MainWindow()
    window.show()
    
    # Fermeture du splash screen
    splash.finish(window)
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())