"""
Module de gestion de la configuration du jeu.
Permet de charger, sauvegarder et manipuler les paramètres de jeu.
"""

import json
import os
from typing import Dict, Any


class ConfigManager:
    """
    Gère la configuration du jeu (taille de la grille, joueur qui commence).
    
    Les paramètres sont sauvegardés dans config.json pour persistance entre sessions.
    Si le fichier n'existe pas, utilise les valeurs par défaut.
    
    Attributes:
        rows: Nombre de lignes du plateau (minimum 4, maximum 10)
        cols: Nombre de colonnes du plateau (minimum 4, maximum 12)
        start_player: Joueur qui commence la partie (1=Rouge, 2=Jaune)
        filename: Nom du fichier de configuration
    """
    
    # Valeurs par défaut
    DEFAULT_ROWS: int = 6
    DEFAULT_COLS: int = 7
    DEFAULT_START_PLAYER: int = 1
    
    # Limites
    MIN_ROWS: int = 4
    MAX_ROWS: int = 10
    MIN_COLS: int = 4
    MAX_COLS: int = 12
    
    def __init__(self, filename: str = "config.json") -> None:
        """
        Initialise le gestionnaire de configuration.
        
        Tente de charger le fichier de configuration existant.
        Si absent, utilise les valeurs par défaut.
        
        Args:
            filename: Nom du fichier de configuration (par défaut: config.json)
        """
        self.filename: str = filename
        self.rows: int = self.DEFAULT_ROWS
        self.cols: int = self.DEFAULT_COLS
        self.start_player: int = self.DEFAULT_START_PLAYER
        
        # Chargement de la configuration existante si disponible
        self.load_config()
        
        print(f"[CONFIG MANAGER] Configuration initialisée : {self.rows}×{self.cols}, Joueur {self.start_player} commence")
    
    def load_config(self) -> bool:
        """
        Charge la configuration depuis le fichier JSON.
        
        Si le fichier n'existe pas ou est corrompu, conserve les valeurs par défaut.
        Valide les valeurs chargées pour s'assurer qu'elles sont dans les limites.
        
        Returns:
            True si le chargement a réussi, False sinon
        """
        if not os.path.exists(self.filename):
            print(f"[CONFIG MANAGER] Fichier {self.filename} introuvable, utilisation des paramètres par défaut")
            return False
        
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                data: Dict[str, Any] = json.load(f)
            
            # Chargement des valeurs avec validation
            self.rows = self._validate_rows(data.get('rows', self.DEFAULT_ROWS))
            self.cols = self._validate_cols(data.get('cols', self.DEFAULT_COLS))
            self.start_player = self._validate_player(data.get('start_player', self.DEFAULT_START_PLAYER))
            
            print(f"[CONFIG MANAGER] Configuration chargée depuis {self.filename}")
            return True
            
        except (json.JSONDecodeError, IOError, KeyError) as e:
            print(f"[CONFIG MANAGER] ❌ Erreur lors du chargement : {e}")
            print("[CONFIG MANAGER] Utilisation des paramètres par défaut")
            return False
    
    def save_config(self) -> bool:
        """
        Sauvegarde la configuration actuelle dans le fichier JSON.
        
        Returns:
            True si la sauvegarde a réussi, False sinon
        """
        try:
            data: Dict[str, Any] = {
                'rows': self.rows,
                'cols': self.cols,
                'start_player': self.start_player
            }
            
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"[CONFIG MANAGER] ✅ Configuration sauvegardée dans {self.filename}")
            return True
            
        except IOError as e:
            print(f"[CONFIG MANAGER] ❌ Erreur lors de la sauvegarde : {e}")
            return False
    
    def get_config(self) -> Dict[str, int]:
        """
        Retourne un dictionnaire avec les paramètres actuels.
        
        Returns:
            Dictionnaire contenant rows, cols et start_player
        """
        return {
            'rows': self.rows,
            'cols': self.cols,
            'start_player': self.start_player
        }
    
    def set_rows(self, rows: int) -> bool:
        """
        Modifie le nombre de lignes avec validation.
        
        Args:
            rows: Nouveau nombre de lignes
            
        Returns:
            True si la valeur est valide et a été appliquée, False sinon
        """
        validated = self._validate_rows(rows)
        if validated != self.rows:
            self.rows = validated
            return True
        return False
    
    def set_cols(self, cols: int) -> bool:
        """
        Modifie le nombre de colonnes avec validation.
        
        Args:
            cols: Nouveau nombre de colonnes
            
        Returns:
            True si la valeur est valide et a été appliquée, False sinon
        """
        validated = self._validate_cols(cols)
        if validated != self.cols:
            self.cols = validated
            return True
        return False
    
    def set_start_player(self, player: int) -> bool:
        """
        Modifie le joueur qui commence avec validation.
        
        Args:
            player: Numéro du joueur (1 ou 2)
            
        Returns:
            True si la valeur est valide et a été appliquée, False sinon
        """
        validated = self._validate_player(player)
        if validated != self.start_player:
            self.start_player = validated
            return True
        return False
    
    def increment_rows(self) -> bool:
        """Incrémente le nombre de lignes (max: MAX_ROWS)."""
        if self.rows < self.MAX_ROWS:
            self.rows += 1
            return True
        return False
    
    def decrement_rows(self) -> bool:
        """Décrémente le nombre de lignes (min: MIN_ROWS)."""
        if self.rows > self.MIN_ROWS:
            self.rows -= 1
            return True
        return False
    
    def increment_cols(self) -> bool:
        """Incrémente le nombre de colonnes (max: MAX_COLS)."""
        if self.cols < self.MAX_COLS:
            self.cols += 1
            return True
        return False
    
    def decrement_cols(self) -> bool:
        """Décrémente le nombre de colonnes (min: MIN_COLS)."""
        if self.cols > self.MIN_COLS:
            self.cols -= 1
            return True
        return False
    
    def toggle_start_player(self) -> None:
        """Alterne le joueur qui commence (1 <-> 2)."""
        self.start_player = 2 if self.start_player == 1 else 1
    
    def _validate_rows(self, rows: int) -> int:
        """Valide et borne le nombre de lignes."""
        return max(self.MIN_ROWS, min(self.MAX_ROWS, rows))
    
    def _validate_cols(self, cols: int) -> int:
        """Valide et borne le nombre de colonnes."""
        return max(self.MIN_COLS, min(self.MAX_COLS, cols))
    
    def _validate_player(self, player: int) -> int:
        """Valide le numéro du joueur (1 ou 2)."""
        return 1 if player == 1 else 2
