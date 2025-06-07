import os

# Chemins absolus
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
RESOURCES_DIR = os.path.join(BASE_DIR, "resources")
DATA_DIR = os.path.join(BASE_DIR, "data")

# Fichiers
STYLE_FILE = os.path.join(RESOURCES_DIR, "styles", "style.css")
ICON_FILE = os.path.join(RESOURCES_DIR, "images", "easycmir_icon.png")
ISOTOPES_FILE = os.path.join(DATA_DIR, "isotopes.txt")
HISTORY_FILE = os.path.join(DATA_DIR, "historique.txt")