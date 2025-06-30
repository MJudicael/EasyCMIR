import json
import os

class ConfigManager:
    """Gestionnaire de configuration pour EasyCMIR"""
    
    def __init__(self):
        # Chemin du fichier de configuration
        self.config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
        self.config_file = os.path.join(self.config_dir, "config.json")
        
        # Configuration par défaut
        self.default_config = {
            "paths": {
                "database": os.path.join(self.config_dir, "materiel.db"),
                "isotopes": os.path.join(self.config_dir, "isotopes.txt"),
                "interventions": os.path.join(os.path.dirname(self.config_dir), "interventions")
            },
            "general": {
                "language": "Français",
                "check_updates": True,
                "restore_windows": False,
                "auto_save": True,
                "save_interval": 5
            },
            "display": {
                "theme": "Clair",
                "icon_size": 32,
                "graph_quality": "Normale",
                "show_grid": True,
                "show_legend": True
            },
            "calculations": {
                "decimal_places": 3,
                "scientific_notation": True,
                "activity_unit": "MBq",
                "dose_unit": "µSv/h",
                "distance_unit": "m",
                "default_distance": 100
            }
        }
        
        # Créer le dossier de configuration s'il n'existe pas
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Charger la configuration
        self.config = self.load_config()
    
    def load_config(self):
        """Charge la configuration depuis le fichier JSON"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Fusionner avec la config par défaut pour gérer les nouvelles clés
                    return self._merge_configs(self.default_config, loaded_config)
            else:
                # Créer le fichier de configuration avec les valeurs par défaut
                self.save_config(self.default_config)
                return self.default_config.copy()
        except Exception as e:
            print(f"Erreur lors du chargement de la configuration: {e}")
            return self.default_config.copy()
    
    def save_config(self, config=None):
        """Sauvegarde la configuration dans le fichier JSON"""
        try:
            if config is None:
                config = self.config
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la configuration: {e}")
            return False
    
    def get_value(self, section, key, default=None):
        """Récupère une valeur de configuration"""
        try:
            return self.config.get(section, {}).get(key, default)
        except:
            return default
    
    def set_value(self, section, key, value):
        """Définit une valeur de configuration"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
    
    def get_database_path(self):
        """Récupère le chemin de la base de données"""
        return self.get_value("paths", "database", self.default_config["paths"]["database"])
    
    def get_isotopes_path(self):
        """Récupère le chemin du fichier des isotopes"""
        return self.get_value("paths", "isotopes", self.default_config["paths"]["isotopes"])
    
    def get_interventions_path(self):
        """Récupère le chemin du dossier des interventions"""
        return self.get_value("paths", "interventions", self.default_config["paths"]["interventions"])
    
    def set_database_path(self, path):
        """Définit le chemin de la base de données"""
        self.set_value("paths", "database", path)
    
    def set_isotopes_path(self, path):
        """Définit le chemin du fichier des isotopes"""
        self.set_value("paths", "isotopes", path)
    
    def set_interventions_path(self, path):
        """Définit le chemin du dossier des interventions"""
        self.set_value("paths", "interventions", path)
    
    def _merge_configs(self, default, loaded):
        """Fusionne la configuration chargée avec la configuration par défaut"""
        merged = default.copy()
        for section, values in loaded.items():
            if section in merged and isinstance(merged[section], dict) and isinstance(values, dict):
                merged[section].update(values)
            else:
                merged[section] = values
        return merged

# Instance globale du gestionnaire de configuration
config_manager = ConfigManager()
