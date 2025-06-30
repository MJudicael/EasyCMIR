from .utils.database import load_isotopes, save_to_history
from .utils.widgets import (
    ClearingDoubleSpinBox,
    ClearingSpinBox,
    ClearingLineEdit
)
from .utils.config_manager import config_manager

__author__ = "Judicaël Mougin - SDIS 71"
__license__ = "GPL 3 or Later"
__email__ = "jmougin@sdis71.fr"

# Constantes globales (maintenant dynamiques via config_manager)
def get_isotopes_file():
    return config_manager.get_isotopes_path()

HISTORY_DB_FILE = "../data/historique.txt"