"""
Gestionnaire de paramètres pour Connect Four.

Gère le chargement, la sauvegarde et la modification des paramètres utilisateur
(couleurs, volume, etc.) via un fichier JSON.
"""

import json
import os
from typing import Any, Dict


class SettingsManager:
    """Gère les paramètres de l'application."""
    
    # Paramètres par défaut
    DEFAULT_SETTINGS = {
        "colors": {
            "player1": (255, 0, 0),      # Rouge
            "player2": (255, 255, 0),    # Jaune
            "grid": (0, 0, 255),         # Bleu
            "background": (0, 0, 0),     # Noir
            "empty_slot": (255, 255, 255)  # Blanc
        },
        "volume": {
            "master": 50,
            "sfx": 50,
            "music": 50
        }
    }
    
    def __init__(self, settings_file: str = "settings.json"):
        """
        Initialise le gestionnaire de paramètres.
        
        Args:
            settings_file: Chemin vers le fichier de paramètres
        """
        self.settings_file = settings_file
        self.settings = self.load_settings()
    
    def load_settings(self) -> Dict[str, Any]:
        """
        Charge les paramètres depuis le fichier JSON.
        
        Returns:
            Dictionnaire des paramètres (ou paramètres par défaut si le fichier n'existe pas)
        """
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    # Fusion avec les paramètres par défaut pour les clés manquantes
                    return self._merge_settings(self.DEFAULT_SETTINGS.copy(), loaded_settings)
            except (json.JSONDecodeError, IOError) as e:
                print(f"[SETTINGS] Erreur lors du chargement : {e}")
                return self.DEFAULT_SETTINGS.copy()
        else:
            print("[SETTINGS] Fichier de paramètres introuvable, utilisation des valeurs par défaut")
            return self.DEFAULT_SETTINGS.copy()
    
    def save_settings(self) -> bool:
        """
        Sauvegarde les paramètres dans le fichier JSON.
        
        Returns:
            True si la sauvegarde a réussi, False sinon
        """
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            print(f"[SETTINGS] Paramètres sauvegardés dans {self.settings_file}")
            return True
        except IOError as e:
            print(f"[SETTINGS] Erreur lors de la sauvegarde : {e}")
            return False
    
    def get_setting(self, category: str, key: str) -> Any:
        """
        Récupère une valeur de paramètre.
        
        Args:
            category: Catégorie du paramètre (ex: "colors", "volume")
            key: Clé du paramètre (ex: "player1", "master")
        
        Returns:
            Valeur du paramètre ou None si introuvable
        """
        return self.settings.get(category, {}).get(key)
    
    def update_setting(self, category: str, key: str, value: Any) -> None:
        """
        Met à jour un paramètre et sauvegarde immédiatement.
        
        Args:
            category: Catégorie du paramètre
            key: Clé du paramètre
            value: Nouvelle valeur
        """
        if category not in self.settings:
            self.settings[category] = {}
        
        self.settings[category][key] = value
        self.save_settings()
        print(f"[SETTINGS] Paramètre mis à jour : {category}.{key} = {value}")
    
    def reset_to_defaults(self) -> None:
        """Réinitialise tous les paramètres aux valeurs par défaut."""
        self.settings = self.DEFAULT_SETTINGS.copy()
        self.save_settings()
        print("[SETTINGS] Paramètres réinitialisés aux valeurs par défaut")
    
    def _merge_settings(self, default: Dict, loaded: Dict) -> Dict:
        """
        Fusionne les paramètres chargés avec les paramètres par défaut.
        
        Args:
            default: Paramètres par défaut
            loaded: Paramètres chargés depuis le fichier
        
        Returns:
            Dictionnaire fusionné
        """
        for key, value in loaded.items():
            if isinstance(value, dict) and key in default:
                default[key] = self._merge_settings(default[key], value)
            else:
                default[key] = value
        return default
    
    def get_color(self, color_key: str) -> tuple[int, int, int]:
        """
        Récupère une couleur.
        
        Args:
            color_key: Clé de la couleur (player1, player2, grid, etc.)
        
        Returns:
            Tuple RGB de la couleur
        """
        color = self.get_setting("colors", color_key)
        if color and isinstance(color, (list, tuple)) and len(color) == 3:
            return tuple(color)
        # Retour aux valeurs par défaut si erreur
        return self.DEFAULT_SETTINGS["colors"].get(color_key, (255, 255, 255))
