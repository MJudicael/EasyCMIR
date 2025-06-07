from PySide6.QtGui import QIcon
import os

class IconManager:
    def __init__(self):
        self.icon_mapping = {
            "Décroissance": "decroissance.png",
            "Distance": "distance.png",
            "DED 1m": "ded1m.png",
            "P Public": "perimetre_public.png",
            "TMR": "tmr.png",
            "Unités RAD": "units_rad.png",
        }
        
        self.icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                     "resources", "icons")
    
    def get_icon(self, button_text):
        if button_text in self.icon_mapping:
            icon_file = os.path.join(self.icon_path, self.icon_mapping[button_text])
            if os.path.exists(icon_file):
                return QIcon(icon_file)
        return None