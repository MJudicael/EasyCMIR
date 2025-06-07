import os

def load_isotopes():
    """Charge les isotopes depuis le fichier texte."""
    isotopes = {}
    try:
        # Utilisation du chemin absolu
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(os.path.dirname(current_dir))
        isotopes_path = os.path.join(root_dir, "data", "isotopes.txt")
        
        with open(isotopes_path, 'r', encoding='utf-8') as file:
            for line in file:
                if line.startswith("//") or not line.strip():
                    continue
                # Séparation des données par point-virgule
                data = line.strip().split(';')
                if len(data) == 9:
                    name = data[0]
                    # Conversion des valeurs en float
                    values = [float(x) for x in data[1:]]
                    isotopes[name] = values
    except FileNotFoundError:
        print(f"Fichier isotopes.txt non trouvé à {isotopes_path}")
    except Exception as e:
        print(f"Erreur lors du chargement des isotopes: {e}")
    
    return isotopes, list(isotopes.keys())

# Chargement des isotopes au démarrage
ISOTOPES, ISOTOPE_NAMES = load_isotopes()