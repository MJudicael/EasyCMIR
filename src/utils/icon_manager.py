from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt
import os

PICTOGRAM_MAPPING = {
    # Mapping des pictogrammes
    "code1": "explosion.png",
    "code2": "explosion.png",
    # Ajouter d'autres mappings si nécessaire
}

class IconManager:
    def __init__(self):
        self.icon_mapping = {
            # Boutons
            "Décroissance": "decroissance.png",
            "Distance": "distance.png",
            "DED 1m": "ded1m.png",
            "P Public": "perimetre_public.png",
            "TMR": "tmr.png",
            "Unités RAD": "units_rad.png",
            "Ecran": "ecran.png",
            "Gestion RH": "RH.png",
            "Matériel": "inventaire.png",
            "Activité": "activite_origin.png",
            "Intervention": "pompier.png"
            #Ne pas oublire de modifier le main_window pour ajouter les icônes correspondantes """
        }
        
        self.icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                     "resources", "icons")
    
    def get_icon(self, button_text):
        if button_text in self.icon_mapping:
            icon_file = os.path.join(self.icon_path, self.icon_mapping[button_text])
            if os.path.exists(icon_file):
                return QIcon(icon_file)
        return None

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