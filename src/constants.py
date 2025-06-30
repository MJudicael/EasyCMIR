import os

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
RESOURCES_DIR = os.path.join(ROOT_DIR, "resources")
ICONS_DIR = os.path.join(RESOURCES_DIR, "icons")
INTERVENTIONS_DIR = os.path.join(ROOT_DIR, "interventions")

# Créer les dossiers s'ils n'existent pas
for directory in [RESOURCES_DIR, ICONS_DIR, INTERVENTIONS_DIR]:
    os.makedirs(directory, exist_ok=True)