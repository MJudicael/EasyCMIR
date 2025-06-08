from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt
import os

# Définition des chemins
PICTOGRAMS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "resources",
    "pictograms"
)

PICTOGRAM_MAPPING = {
    "2": "danger_2.jpg",
    "3": "danger_3.jpg",
    "4": "danger_4.jpg",
    "5": "danger_5.jpg",
    "6": "danger_6.jpg",
    "7": "danger_7.jpg",
    "8": "danger_8.jpg",
    "9": "danger_9.jpg",
    "X": "danger_x.jpg"
}

class IconManager:
    def __init__(self):
        self.icon_mapping = {
            # Boutons RAD
            "Décroissance": "decroissance.png",
            "Distance": "distance.png",
            "DED 1m": "ded1m.png",
            "P Public": "perimetre_public.png",
            "TMR": "tmr.png",
            "Unités RAD": "units_rad.png",
            
            # Boutons RCH
            "Identification": "loupe.png",
            "Code DANGER": "danger.png",
            "Bio": "biohazard.png",
            "PID": "loupe.png",
            "TMD": "tanker.png",
            "Intervention": "loupe.png",
          
        }
        
        self.icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                     "resources", "icons")
        self.pictogram_cache = {}

    def get_icon(self, button_text):
        """Récupère une icône par son nom."""
        if button_text in self.icon_mapping:
            icon_file = os.path.join(self.icon_path, self.icon_mapping[button_text])
            if os.path.exists(icon_file):
                return QIcon(icon_file)
        # Au lieu de retourner None, on retourne une icône vide
        return QIcon()

    def get_pictogram_path(self, code):
        """Retourne le chemin complet du pictogramme pour un code donné."""
        if code in PICTOGRAM_MAPPING:
            return os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "resources", 
                "pictograms", 
                PICTOGRAM_MAPPING[code]
            )
        return None

    def load_pictogram(self, code, size=64):
        """Charge et redimensionne un pictogramme."""
        path = self.get_pictogram_path(code)
        if path and os.path.exists(path):
            pixmap = QPixmap(path)
            return pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return None

    def verify_pictograms(self):
        """Vérifie la présence de tous les pictogrammes nécessaires."""
        missing = []
        for code, filename in PICTOGRAM_MAPPING.items():
            path = self.get_pictogram_path(code)
            if not os.path.exists(path):
                missing.append(filename)
        
        if missing:
            print("Pictogrammes manquants :")
            for filename in missing:
                print(f"- {filename}")
            return False
        return True

    def get_danger_icon(self, code_char):
        """Récupère l'icône pour un code danger."""
        try:
            if code_char in self.pictogram_cache:
                return self.pictogram_cache[code_char]

            # Utiliser le mapping pour obtenir le nom du fichier
            if code_char in PICTOGRAM_MAPPING:
                icon_path = os.path.join(PICTOGRAMS_DIR, PICTOGRAM_MAPPING[code_char])
                
                if os.path.exists(icon_path):
                    icon = QIcon(icon_path)
                    self.pictogram_cache[code_char] = icon
                    return icon
                else:
                    print(f"Pictogramme non trouvé: {icon_path}")
            else:
                print(f"Code non trouvé dans le mapping: {code_char}")
            return None
        except Exception as e:
            print(f"Erreur lors du chargement du pictogramme {code_char}: {e}")
            return None