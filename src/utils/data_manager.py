"""
Module de gestion de la persistance des données.
Permet de sauvegarder et charger l'état d'une partie.
"""

import json
import os
from typing import Optional

from ..models.game import Game


def save_game(game: Game, filename: str = "savegame.json") -> bool:
    """
    Sauvegarde l'état actuel de la partie dans un fichier JSON.
    
    Args:
        game: Instance du jeu à sauvegarder
        filename: Nom du fichier de sauvegarde (par défaut: savegame.json)
        
    Returns:
        True si la sauvegarde a réussi, False sinon
    """
    try:
        # Conversion du jeu en dictionnaire
        game_data = game.to_dict()
        
        # Écriture dans le fichier JSON
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(game_data, f, indent=2, ensure_ascii=False)
        
        print(f"[DATA MANAGER] Partie sauvegardée dans {filename}")
        return True
        
    except Exception as e:
        print(f"[DATA MANAGER ERROR] Échec de la sauvegarde : {e}")
        return False


def load_game(filename: str = "savegame.json") -> Optional[Game]:
    """
    Charge une partie depuis un fichier JSON.
    
    Args:
        filename: Nom du fichier de sauvegarde (par défaut: savegame.json)
        
    Returns:
        Instance de Game restaurée, ou None si le fichier n'existe pas ou est invalide
    """
    try:
        # Vérification de l'existence du fichier
        if not os.path.exists(filename):
            print(f"[DATA MANAGER] Fichier {filename} introuvable")
            return None
        
        # Lecture du fichier JSON
        with open(filename, 'r', encoding='utf-8') as f:
            game_data = json.load(f)
        
        # Reconstruction de l'objet Game
        game = Game.from_dict(game_data)
        
        print(f"[DATA MANAGER] Partie chargée depuis {filename}")
        return game
        
    except Exception as e:
        print(f"[DATA MANAGER ERROR] Échec du chargement : {e}")
        return None


def delete_save(filename: str = "savegame.json") -> bool:
    """
    Supprime un fichier de sauvegarde.
    
    Args:
        filename: Nom du fichier de sauvegarde à supprimer
        
    Returns:
        True si la suppression a réussi, False sinon
    """
    try:
        if os.path.exists(filename):
            os.remove(filename)
            print(f"[DATA MANAGER] Sauvegarde {filename} supprimée")
            return True
        else:
            print(f"[DATA MANAGER] Fichier {filename} introuvable")
            return False
            
    except Exception as e:
        print(f"[DATA MANAGER ERROR] Échec de la suppression : {e}")
        return False
