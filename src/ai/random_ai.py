"""
Module de l'IA aléatoire (baseline).
Choisit un coup valide au hasard parmi les colonnes disponibles.
"""

import random
from typing import Optional

from ..models.board import Board


class RandomAI:
    """
    Intelligence Artificielle aléatoire pour le jeu Puissance 4.
    
    Stratégie : Choisit une colonne valide au hasard sans aucune logique tactique.
    Utilisé comme baseline pour tester le système et comparer avec des IA plus avancées.
    
    Cette IA ne contient aucune logique de jeu avancée, elle sert de:
    - Test de base pour valider le système
    - Adversaire facile pour les débutants
    - Point de comparaison pour les IA plus complexes (Minimax)
    """
    
    def __init__(self, name: str = "Robot Aléatoire") -> None:
        """
        Initialise l'IA aléatoire.
        
        Args:
            name: Nom de l'IA pour l'affichage (optionnel)
        """
        self.name: str = name
        print(f"[IA DEBUG] {self.name} initialisé")
    
    def get_move(self, board: Board) -> Optional[int]:
        """
        Choisit une colonne valide au hasard.
        
        Stratégie :
        1. Récupère toutes les colonnes valides (non pleines)
        2. Choisit une colonne au hasard parmi les valides
        3. Retourne l'index de la colonne
        
        Args:
            board: Instance du plateau de jeu actuel
            
        Returns:
            Index de la colonne choisie (0 à COLS-1), ou None si aucun coup possible
        """
        # Récupération de toutes les colonnes valides
        valid_columns = board.get_valid_locations()
        
        print(f"[IA DEBUG] {self.name} - Colonnes valides : {valid_columns}")
        
        # Vérification qu'il existe au moins une colonne valide
        if not valid_columns:
            print(f"[IA DEBUG] {self.name} - ERREUR : Aucune colonne valide!")
            return None
        
        # Choix aléatoire parmi les colonnes valides
        chosen_column = random.choice(valid_columns)
        
        print(f"[IA DEBUG] {self.name} - Colonne choisie : {chosen_column}")
        
        return chosen_column
    
    def __str__(self) -> str:
        """
        Représentation textuelle de l'IA.
        
        Returns:
            Nom de l'IA
        """
        return self.name
