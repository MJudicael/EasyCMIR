"""
EasyCMIR - Application de calculs radiologiques
Version 1.3
"""

from .utils.database import load_isotopes, save_to_history
from .utils.widgets import (
    ClearingDoubleSpinBox,
    ClearingSpinBox,
    ClearingLineEdit
)

__author__ = "Judicaël Mougin - SDIS 71"
__license__ = "GPL 3 or Later"
__email__ = "jmougin@sdis71.fr"

# Constantes globales
ISOTOPES_DB_FILE = "../data/isotopes.txt"
HISTORY_DB_FILE = "../data/historique.txt"