"""
Module contenant tous les dialogues de l'application EasyCMIR.
"""

from .decroissance import DecroissanceDialog
from .ded1m import Ded1mDialog, Ded1mManualDialog
from .distance import DistanceDialog
from .news import NewsDialog
from .p_public import PerimetrePublicDialog
from .tmr import TMRDialog
from .unites_rad import UnitesRadDialog
from .about import AboutDialog

__all__ = [
    'DecroissanceDialog',
    'Ded1mDialog',
    'Ded1mManualDialog',
    'DistanceDialog',
    'NewsDialog',
    'PerimetrePublicDialog',
    'TMRDialog',
    'UnitesRadDialog',
    'AboutDialog'
]