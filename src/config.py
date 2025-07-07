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

# Configuration pour le gestionnaire de matériel
def get_materiel_db_path():
    """Récupère le chemin du fichier materiel.db depuis la configuration"""
    try:
        from .utils.config_manager import config_manager
        # Vérifier si un chemin personnalisé est configuré
        custom_path = config_manager.get_value('paths', 'materiel_db_path', None)
        if custom_path and os.path.exists(custom_path):
            return custom_path
    except (ImportError, Exception):
        pass
    
    # Chemin par défaut dans le répertoire data
    default_path = os.path.join(DATA_DIR, "materiel.db")
    return default_path

def set_materiel_db_path(path):
    """Configure le chemin du fichier materiel.db"""
    try:
        from .utils.config_manager import config_manager
        config_manager.set_value('paths', 'materiel_db_path', path)
        config_manager.save_config()
        return True
    except (ImportError, Exception):
        return False

# Chemin par défaut du fichier matériel DB
MATERIEL_DB_FILE = get_materiel_db_path()