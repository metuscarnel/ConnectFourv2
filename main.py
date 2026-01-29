"""
Point d'entrée principal du jeu Puissance 4.
Initialise le pattern MVC et lance le jeu avec menu principal.

Usage:
    python main.py
"""

from src.views.pygame_view import PygameView
from src.controllers.game_controller import GameController


def main() -> None:
    """
    Fonction principale qui initialise et lance le jeu.
    
    Architecture MVC avec machine à états :
    - View : PygameView (affichage graphique)
    - Controller : GameController (orchestration + états)
    - Model : Game (créé dynamiquement selon le mode choisi)
    
    Flux de l'application :
    1. Affichage du menu principal
    2. Sélection du mode (PvP ou PvAI)
    3. Partie
    4. Retour au menu
    """
    # Initialisation de la vue (interface graphique)
    view = PygameView()
    
    # Initialisation du contrôleur (gère la machine à états)
    controller = GameController(view=view)
    
    # Lancement de l'application
    print("🎮 Démarrage de Puissance 4...")
    print("📋 Menu principal à venir...\n")
    
    controller.run()
    
    print("👋 Merci d'avoir joué!")


if __name__ == "__main__":
    main()
