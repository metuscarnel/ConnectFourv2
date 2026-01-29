"""
Module du contrôleur principal du jeu.
Orchestre les interactions entre le modèle (logique) et la vue (affichage).
"""

from typing import Optional
import pygame

from ..models.game import Game
from ..views.pygame_view import PygameView
from ..ai.random_ai import RandomAI


class GameController:
    """
    Contrôleur principal gérant la boucle de jeu et les interactions utilisateur.
    
    Respecte le pattern MVC :
    - Ne contient pas de logique de jeu (délégué au Model)
    - Ne dessine pas directement (délégué à la View)
    - Coordonne les événements et met à jour Model et View
    
    Attributes:
        game: Instance du modèle de jeu
        view: Instance de la vue Pygame
        gamemode: Mode de jeu ("PvP" ou "PvAI")
        ai: Instance de l'IA (None si mode PvP)
        ai_player: Numéro du joueur contrôlé par l'IA (2 par défaut)
    """
    
    def __init__(
        self, 
        game: Game, 
        view: PygameView, 
        gamemode: str = "PvP",
        ai: Optional[RandomAI] = None,
        ai_player: int = 2
    ) -> None:
        """
        Initialise le contrôleur avec un modèle et une vue.
        
        Args:
            game: Instance du jeu (logique métier)
            view: Instance de la vue (affichage)
            gamemode: Mode de jeu ("PvP" pour Humain vs Humain, "PvAI" pour Humain vs IA)
            ai: Instance de l'IA (obligatoire si gamemode="PvAI")
            ai_player: Numéro du joueur contrôlé par l'IA (1 ou 2, défaut=2)
        """
        self.game: Game = game
        self.view: PygameView = view
        self.gamemode: str = gamemode
        self.ai: Optional[RandomAI] = ai
        self.ai_player: int = ai_player
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.fps: int = 60  # Limite de rafraîchissement
        
        print(f"[CONTROLLER DEBUG] Mode de jeu : {self.gamemode}")
        if self.gamemode == "PvAI":
            print(f"[CONTROLLER DEBUG] IA : {self.ai.name if self.ai else 'None'}")
            print(f"[CONTROLLER DEBUG] IA contrôle le joueur {self.ai_player}")
    
    def run(self) -> None:
        """
        Lance la boucle principale du jeu (game loop).
        
        Gère :

        - Les événements utilisateur (souris, clavier)
        - Le tour de l'IA si mode PvAI
        - La mise à jour de l'affichage
        - La détection de fin de partie
        """
        # Dessin initial du plateau vide
        self.view.draw_board(self.game.board)
        self.view.update_display()
        
        game_over = False
        current_hover_col: Optional[int] = None
        
        # Boucle principale
        while not game_over:
            # Limitation du framerate
            self.clock.tick(self.fps)
            
            # === GESTION DU TOUR DE L'IA ===
            if self.gamemode == "PvAI" and self.game.get_current_player() == self.ai_player:
                print(f"\n[CONTROLLER DEBUG] === TOUR DE L'IA ===")
                
                # Pause pour rendre le jeu plus naturel
                pygame.time.wait(500)  # 0.5 seconde
                
                # L'IA choisit son coup
                ai_column = self.ai.get_move(self.game.board)
                
                if ai_column is not None:
                    print(f"[CONTROLLER DEBUG] IA joue en colonne {ai_column}")
                    
                    # Placement du pion de l'IA
                    success = self.game.play_turn(ai_column)
                    
                    if success:
                        # Mise à jour de l'affichage
                        self.view.draw_board(self.game.board)
                        self.view.update_display()
                        
                        # Vérification de la fin de partie
                        if self.game.is_game_over():
                            self._handle_game_over()
                            game_over = True
                            continue
                else:
                    print("[CONTROLLER DEBUG] ERREUR : IA n'a pas pu choisir de coup")
            
            # === GESTION DES ÉVÉNEMENTS HUMAIN ===
            for event in pygame.event.get():
                # Fermeture de la fenêtre
                if event.type == pygame.QUIT:
                    game_over = True
                    break
                
                # Mouvement de la souris : affichage du pion fantôme (uniquement pour le joueur humain)
                if event.type == pygame.MOUSEMOTION:
                    # Ne pas afficher le pion fantôme pendant le tour de l'IA
                    if self.gamemode == "PvAI" and self.game.get_current_player() == self.ai_player:
                        continue
                    
                    x_pos = event.pos[0]
                    col = self.view.get_column_from_mouse_pos(x_pos)
                    
                    # Mise à jour uniquement si la colonne a changé
                    if col != current_hover_col:
                        current_hover_col = col
                        
                        # Redessin complet
                        self.view.draw_board(self.game.board)
                        
                        # Affichage du pion fantôme si colonne valide
                        if col is not None and self.game.board.is_valid_location(col):
                            self.view.draw_preview_piece(col, self.game.get_current_player())
                        
                        self.view.update_display()
                
                # Clic de souris : tentative de placement du pion (uniquement pour le joueur humain)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Ignorer les clics pendant le tour de l'IA
                    if self.gamemode == "PvAI" and self.game.get_current_player() == self.ai_player:
                        print("[CONTROLLER DEBUG] Clic ignoré - C'est le tour de l'IA")
                        continue
                    
                    # Effacement du pion fantôme
                    self.view.draw_board(self.game.board)
                    self.view.update_display()
                    
                    # Récupération de la colonne cliquée
                    x_pos = event.pos[0]
                    col = self.view.get_column_from_mouse_pos(x_pos)
                    
                    if col is not None:
                        # Tentative de jouer le coup
                        success = self.game.play_turn(col)
                        
                        if success:
                            # Mise à jour de l'affichage
                            self.view.draw_board(self.game.board)
                            self.view.update_display()
                            
                            # Vérification de la fin de partie
                            if self.game.is_game_over():
                                self._handle_game_over()
                                game_over = True
        
        # Fermeture propre
        self.view.quit()
    
    def _handle_game_over(self) -> None:
        """
        Gère l'affichage de fin de partie.
        
        Centralise la logique d'affichage de victoire/égalité.
        """
        # Force un dernier rafraîchissement du plateau
        self.view.draw_board(self.game.board)
        
        # Surbrillance des pions gagnants si applicable
        winner = self.game.get_winner()
        if winner is not None:
            winning_positions = self.game.get_winning_positions()
            self.view.draw_winning_positions(winning_positions)
        
        # Affichage du message de game over
        self.view.show_game_over(winner)
        
        # Mise à jour de l'affichage
        self.view.update_display()
        
        # Message console pour débogage
        if winner is not None:
            player_name = "ROUGE" if winner == 1 else "JAUNE"
            print(f"🎉 Le joueur {player_name} a gagné!")
        else:
            print("🤝 Égalité - Plateau rempli!")
        
        # Attente de 4 secondes avant de quitter
        pygame.time.wait(4000)
    
    def run_with_ai(self, ai_player: int) -> None:
        """
        Lance une partie contre l'IA (préparation pour Mission 2).
        
        À implémenter ultérieurement avec les modules IA.
        
        Args:
            ai_player: PLAYER1 ou PLAYER2 pour définir qui est l'IA
        """
        raise NotImplementedError("Mode IA à implémenter dans la Mission 2")
