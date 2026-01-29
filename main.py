"""
Point d'entrée principal du jeu Puissance 4.
Initialise le pattern MVC et lance le jeu.

Usage:
    python main.py
"""

from src.models.game import Game
from src.views.pygame_view import PygameView
from src.controllers.game_controller import GameController
from src.ai.random_ai import RandomAI


def main() -> None:
    """
    Fonction principale qui initialise et lance le jeu.
    
    Architecture MVC :
    - Model : Game (logique métier)
    - View : PygameView (affichage graphique)
    - Controller : GameController (orchestration)
    
    Mode de jeu : Humain (Joueur 1 - Rouge) vs IA Aléatoire (Joueur 2 - Jaune)
    """
    # Initialisation du modèle (logique du jeu)
    game = Game()
    
    # Initialisation de la vue (interface graphique)
    view = PygameView()
    
    # Initialisation de l'IA
    ai = RandomAI(name="Robot Aléatoire")
    
    # Initialisation du contrôleur (coordination)
    # Mode PvAI : Joueur 1 (Humain) vs Joueur 2 (IA)
    controller = GameController(
        game=game,
        view=view,
        gamemode="PvAI",  # Mode Joueur vs IA
        ai=ai,
        ai_player=2  # L'IA contrôle le joueur 2 (Jaune)
    )
    
    # Lancement de la boucle de jeu
    print("🎮 Démarrage de Puissance 4...")
    print("📋 Mode : Humain vs IA Aléatoire")
    print("🔴 Vous jouez ROUGE (Joueur 1)")
    print("🟡 L'IA joue JAUNE (Joueur 2)")
    print("💡 Cliquez sur une colonne pour jouer\n")
    
    controller.run()
    
    print("👋 Merci d'avoir joué!")


if __name__ == "__main__":
    main()
