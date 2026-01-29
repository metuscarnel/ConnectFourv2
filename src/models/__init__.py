"""
Module des modèles métier du jeu (couche Model du pattern MVC).
Contient la logique pure du jeu sans dépendance à l'interface graphique.
"""

from .board import Board
from .game import Game

__all__ = ["Board", "Game"]
