"""
Module contenant tous les dialogues de l'application EasyCMIR.
"""

from .intervention import InterventionDialog
from .decroissance import DecroissanceDialog
from .ded1m import Ded1mDialog  # Utiliser un alias
from .ppublic import PPublicDialog
from .tmr import TMRDialog
from .distance import DistanceDialog
from .unites import UnitesRadDialog
from .ecran import EcranDialog

__all__ = [
    'InterventionDialog',
    'DecroissanceDialog',
    'Ded1mDialog',
    'PPublicDialog',
    'TMRDialog',
    'DistanceDialog',
    'UnitesRadDialog',
    'EcranDialog'
]