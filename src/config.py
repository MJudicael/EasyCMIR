import os

# Chemins absolus
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
RESOURCES_DIR = os.path.join(BASE_DIR, "resources")
DATA_DIR = os.path.join(BASE_DIR, "data")

# Fichiers
STYLE_FILE = os.path.join(RESOURCES_DIR, "styles", "style.css")
ICON_FILE = os.path.join(RESOURCES_DIR, "images", "easycmir_icon.png")
HISTORY_FILE = os.path.join(DATA_DIR, "historique.txt")

# Fonction pour obtenir le chemin du fichier isotopes depuis la configuration
def get_isotopes_file():
    """Récupère le chemin du fichier isotopes depuis la configuration"""
    try:
        from .utils.config_manager import config_manager
        return config_manager.get_isotopes_path()
    except ImportError:
        # Fallback si le gestionnaire de config n'est pas disponible
        return os.path.join(DATA_DIR, "isotopes.txt")

# Variable d'accès au fichier isotopes (utilisera la configuration)
ISOTOPES_FILE = get_isotopes_file()

# Chemins des fichiers de données
CODES_DANGER_FILE = os.path.join(DATA_DIR, "codes_danger.txt")