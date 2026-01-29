"""
Module du contrôleur principal du jeu.
Orchestre les interactions entre le modèle (logique) et la vue (affichage).
Gère une machine à états (Menu -> Jeu -> Retour au Menu).
"""

from typing import Optional
import pygame

from ..models.game import Game
from ..views.pygame_view import PygameView
from ..ai.random_ai import RandomAI
from ..utils.enums import AppState
from ..utils import data_manager


class GameController:
    """
    Contrôleur principal gérant la boucle de jeu et les interactions utilisateur.
    
    Implémente une machine à états pour gérer le flux de l'application :
    - MENU : Affichage du menu principal
    - GAME : Partie en cours
    - QUIT : Fermeture de l'application
    
    Respecte le pattern MVC :
    - Ne contient pas de logique de jeu (délégué au Model)
    - Ne dessine pas directement (délégué à la View)
    - Coordonne les événements et met à jour Model et View
    
    Attributes:
        view: Instance de la vue Pygame
        game: Instance du modèle de jeu (créée au lancement d'une partie)
        state: État actuel de l'application (AppState)
        gamemode: Mode de jeu ("PvP" ou "PvAI")
        ai: Instance de l'IA (None si mode PvP)
        ai_player: Numéro du joueur contrôlé par l'IA (2 par défaut)
    """
    
    def __init__(self, view: PygameView) -> None:
        """
        Initialise le contrôleur avec une vue.
        
        Args:
            view: Instance de la vue (affichage)
        """
        self.view: PygameView = view
        self.game: Optional[Game] = None
        self.state: AppState = AppState.MENU  # Démarrage sur le menu
        self.gamemode: str = "PvP"
        self.ai: Optional[RandomAI] = None
        self.ai_player: int = 2
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.fps: int = 60  # Limite de rafraîchissement
        
        print("[CONTROLLER DEBUG] Contrôleur initialisé - État : MENU")
    
    def run(self) -> None:
        """
        Boucle principale de l'application avec machine à états.
        
        Gère les transitions entre :
        - MENU : Affichage et interaction avec le menu principal
        - GAME : Partie en cours
        - QUIT : Fermeture de l'application
        """
        print("[CONTROLLER DEBUG] === DÉMARRAGE DE L'APPLICATION ===\n")
        
        # Boucle principale de l'application
        while self.state != AppState.QUIT:
            if self.state == AppState.MENU:
                print("[CONTROLLER DEBUG] État : MENU")
                self.run_menu()
            
            elif self.state == AppState.GAME:
                print(f"[CONTROLLER DEBUG] État : GAME (Mode: {self.gamemode})")
                self.run_game()
        
        # Fermeture propre
        print("\n[CONTROLLER DEBUG] === FERMETURE DE L'APPLICATION ===")
        self.view.quit()
    
    def _refresh_game_display(self, mouse_x: Optional[int] = None) -> None:
        """
        Méthode helper pour rafraîchir l'affichage du jeu.
        
        IMPORTANT : draw_board() appelle automatiquement draw_ui() à la fin,
        donc le bouton est toujours dessiné. Le rect est accessible via
        self.view.undo_button_rect pour la détection des clics.
        
        Args:
            mouse_x: Position X de la souris (optionnel) pour afficher le pion fantôme
        """
        self.view.draw_board(self.game.board, mouse_x, self.game.get_current_player())
        self.view.update_display()
    
    def run_menu(self) -> None:
        """
        Gère l'affichage et les interactions du menu principal.
        
        Affiche les options :
        - Joueur vs Joueur
        - Joueur vs IA
        
        Transitions possibles :
        - Clic sur un bouton -> GAME
        - Fermeture de la fenêtre -> QUIT
        """
        menu_active = True
        
        while menu_active and self.state == AppState.MENU:
            self.clock.tick(self.fps)
            
            # Affichage du menu et récupération des rectangles de boutons
            pvp_rect, pvai_rect = self.view.draw_menu()
            self.view.update_display()
            
            # Gestion des événements
            for event in pygame.event.get():
                # Fermeture de la fenêtre
                if event.type == pygame.QUIT:
                    self.state = AppState.QUIT
                    menu_active = False
                    break
                
                # Clic de souris sur les boutons
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    
                    # Clic sur "Joueur vs Joueur"
                    if pvp_rect.collidepoint(mouse_pos):
                        print("[CONTROLLER DEBUG] Mode sélectionné : PvP")
                        self.gamemode = "PvP"
                        self.ai = None
                        self.state = AppState.GAME
                        menu_active = False
                    
                    # Clic sur "Joueur vs IA"
                    elif pvai_rect.collidepoint(mouse_pos):
                        print("[CONTROLLER DEBUG] Mode sélectionné : PvAI")
                        self.gamemode = "PvAI"
                        self.ai = RandomAI(name="Robot Aléatoire")
                        self.ai_player = 2
                        self.state = AppState.GAME
                        menu_active = False
    
    def run_game(self) -> None:
        """
        Lance la boucle de jeu (partie en cours).
        
        Gère :
        - Les événements utilisateur (souris, clavier)
        - Le tour de l'IA si mode PvAI
        - La mise à jour de l'affichage
        - La détection de fin de partie
        
        Transitions possibles :
        - Fin de partie -> Retour au MENU (après 4 secondes ou touche M)
        - Fermeture de la fenêtre -> QUIT
        """
        # Initialisation d'une nouvelle partie
        self.game = Game()
        
        print(f"\n[CONTROLLER DEBUG] === NOUVELLE PARTIE ({self.gamemode}) ===")
        if self.gamemode == "PvAI":
            print(f"[CONTROLLER DEBUG] IA : {self.ai.name}")
            print(f"[CONTROLLER DEBUG] IA contrôle le joueur {self.ai_player}\n")
        
        # Dessin initial du plateau vide avec bouton UI
        self._refresh_game_display()
        
        game_over = False
        current_hover_col: Optional[int] = None
        
        # Boucle de jeu
        while not game_over and self.state == AppState.GAME:
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
                        self._refresh_game_display()
                        
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
                    self.state = AppState.QUIT
                    game_over = True
                    break
                
                # Mouvement de la souris : affichage du pion fantôme (uniquement pour le joueur humain)
                if event.type == pygame.MOUSEMOTION:
                    # Ne pas afficher le pion fantôme pendant le tour de l'IA
                    if self.gamemode == "PvAI" and self.game.get_current_player() == self.ai_player:
                        continue
                    
                    # Rafraîchissement avec pion fantôme intégré
                    # draw_board() gère automatiquement le calcul de colonne et l'affichage
                    self._refresh_game_display(mouse_x=event.pos[0])
                
                # Clic de souris : gestion avec distinction stricte UI vs Plateau
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    
                    # ========================================
                    # BRANCHE 1 : CLIC SUR BOUTON UNDO
                    # ========================================
                    if self.view.undo_button_rect and self.view.undo_button_rect.collidepoint(mouse_pos):
                        print("\n[CONTROLLER DEBUG] === CLIC SUR BOUTON UNDO ===")
                        
                        # Garde-fou : vérifier qu'il y a au moins un coup à annuler
                        if len(self.game.board.history) == 0:
                            print("[CONTROLLER DEBUG] Impossible d'annuler : aucun coup joué")
                        else:
                            # Logique selon le mode de jeu
                            if self.gamemode == "PvP":
                                # Mode PvP : annuler 1 seul coup
                                print("[CONTROLLER DEBUG] Mode PvP : annulation de 1 coup")
                                self.game.undo()
                            
                            elif self.gamemode == "PvAI":
                                # Mode PvAI : annuler 2 coups (IA + Joueur)
                                print("[CONTROLLER DEBUG] Mode PvAI : annulation de 2 coups")
                                
                                # Premier undo : coup du joueur
                                if self.game.undo():
                                    print("[CONTROLLER DEBUG] Coup joueur annulé")
                                    
                                    # Second undo : coup de l'IA (si existe)
                                    if len(self.game.board.history) > 0:
                                        self.game.undo()
                                        print("[CONTROLLER DEBUG] Coup IA annulé")
                                    else:
                                        print("[CONTROLLER DEBUG] Pas de coup IA à annuler")
                            
                            # Rafraîchissement complet de l'écran
                            self._refresh_game_display()
                        
                        print("[CONTROLLER DEBUG] === FIN TRAITEMENT UNDO ===\n")
                    
                    # ========================================
                    # BRANCHE 2 : CLIC SUR BOUTON SAUVER
                    # ========================================
                    elif self.view.save_button_rect and self.view.save_button_rect.collidepoint(mouse_pos):
                        print("\n[CONTROLLER DEBUG] === CLIC SUR BOUTON SAUVER ===")
                        
                        # Sauvegarde de la partie
                        success = data_manager.save_game(self.game)
                        
                        if success:
                            print("[CONTROLLER DEBUG] ✅ Partie sauvegardée !")
                        else:
                            print("[CONTROLLER DEBUG] ❌ Échec de la sauvegarde")
                        
                        print("[CONTROLLER DEBUG] === FIN TRAITEMENT SAUVER ===\n")
                    
                    # ========================================
                    # BRANCHE 3 : CLIC SUR BOUTON CHARGER
                    # ========================================
                    elif self.view.load_button_rect and self.view.load_button_rect.collidepoint(mouse_pos):
                        print("\n[CONTROLLER DEBUG] === CLIC SUR BOUTON CHARGER ===")
                        
                        # Chargement de la partie
                        loaded_game = data_manager.load_game()
                        
                        if loaded_game is not None:
                            # Remplacement de la partie actuelle
                            self.game = loaded_game
                            print("[CONTROLLER DEBUG] ✅ Partie chargée !")
                            
                            # Rafraîchissement complet de l'écran
                            self._refresh_game_display()
                        else:
                            print("[CONTROLLER DEBUG] ❌ Aucune sauvegarde trouvée")
                        
                        print("[CONTROLLER DEBUG] === FIN TRAITEMENT CHARGER ===\n")
                    
                    # ========================================
                    # BRANCHE 4 : CLIC SUR LE PLATEAU
                    # ========================================
                    else:
                        # Ignorer les clics pendant le tour de l'IA
                        if self.gamemode == "PvAI" and self.game.get_current_player() == self.ai_player:
                            print("[CONTROLLER DEBUG] Clic ignoré - C'est le tour de l'IA")
                            continue
                        
                        # Effacement du pion fantôme et redessin
                        self._refresh_game_display()
                        
                        # Récupération de la colonne cliquée
                        x_pos = mouse_pos[0]
                        col = self.view.get_column_from_mouse_pos(x_pos)
                        
                        if col is not None:
                            print(f"[CONTROLLER DEBUG] Tentative de jouer en colonne {col}")
                            
                            # Tentative de jouer le coup
                            success = self.game.play_turn(col)
                            
                            if success:
                                # Mise à jour de l'affichage
                                self._refresh_game_display()
                                
                                # Vérification de la fin de partie
                                if self.game.is_game_over():
                                    self._handle_game_over()
                                    game_over = True
        
        # Retour au menu après la partie (si pas de demande de fermeture)
        if self.state == AppState.GAME:
            self.state = AppState.MENU
            print("\n[CONTROLLER DEBUG] Retour au menu principal\n")
    
    def _handle_game_over(self) -> None:
        """
        Gère l'affichage de fin de partie.
        
        Centralise la logique d'affichage de victoire/égalité.
        Attend 4 secondes avant de retourner au menu.
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
        
        # Attente de 4 secondes avant de retourner au menu
        pygame.time.wait(4000)
