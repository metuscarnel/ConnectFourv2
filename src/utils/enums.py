"""
Énumérations pour gérer les états du jeu.
Fournit un typage fort pour les différentes phases de la partie.
"""

from enum import Enum, auto


class GameState(Enum):
    """
    Représente l'état actuel de la partie.
    
    Attributes:
        NOT_STARTED: La partie n'a pas encore commencé
        IN_PROGRESS: La partie est en cours
        FINISHED: La partie est terminée (victoire ou égalité)
    """
    NOT_STARTED = auto()
    IN_PROGRESS = auto()
    FINISHED = auto()


class AppState(Enum):
    """
    Représente l'état global de l'application.
    
    Utilisé pour gérer le flux entre menu principal, jeu et sortie.
    
    Attributes:
        MENU: Affichage du menu principal
        SETTINGS: Écran de paramètres/configuration
        GAME: Partie en cours
        QUIT: Fermeture de l'application
    """
    MENU = auto()
    SETTINGS = auto()
    GAME = auto()
    QUIT = auto()


class GameMode(Enum):
    """
    Représente le mode de jeu sélectionné.
    
    Attributes:
        PVP: Joueur vs Joueur (2 humains)
        PVAI: Joueur vs IA (1 humain vs 1 IA)
        AI_VS_AI: IA vs IA (mode démo, 0 humain)
    """
    PVP = "PvP"
    PVAI = "PvAI"
    AI_VS_AI = "AIvsAI"
