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
from ..ai.minimax_ai import MinimaxAI
from ..utils.enums import AppState
from ..utils import data_manager
from ..utils.config_manager import ConfigManager


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
        self.ai2: Optional[RandomAI] = None  # Deuxième IA pour le mode AIvsAI
        self.ai2_player: int = 2  # Numéro du joueur contrôlé par la deuxième IA
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.fps: int = 60  # Limite de rafraîchissement
        self.config_manager: ConfigManager = ConfigManager()  # Gestionnaire de configuration
        
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
            
            elif self.state == AppState.SETTINGS:
                print("[CONTROLLER DEBUG] État : SETTINGS")
                self.run_settings()
            
            elif self.state == AppState.GAME:
                print(f"[CONTROLLER DEBUG] État : GAME (Mode: {self.gamemode})")
                self.run_game()
            
            elif self.state == AppState.GAME_OVER:
                print("[CONTROLLER DEBUG] État : GAME_OVER")
                self.run_game_over()
        
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
        
        # Affichage des informations de la partie (ID et nombre de coups)
        move_count = len(self.game.move_history)
        self.view.draw_game_info(self.game.game_id, move_count)
        
        # Affichage du sélecteur de profondeur en mode PvAI
        if self.gamemode == "PvAI" and hasattr(self.ai, 'depth'):
            self.depth_selector_rects = self.view.draw_depth_selector(self.ai.depth)
        
        self.view.update_display()
    
    def run_menu(self) -> None:
        """
        Gère l'affichage et les interactions du menu principal.
        
        Affiche les options :
        - Joueur vs Joueur
        - Joueur vs IA
        - MODE DÉMO (IA vs IA)
        - Paramètres
        
        Transitions possibles :
        - Clic sur un bouton -> GAME
        - Fermeture de la fenêtre -> QUIT
        """
        menu_active = True
        
        while menu_active and self.state == AppState.MENU:
            self.clock.tick(self.fps)
            
            # Affichage du menu et récupération des rectangles de boutons
            pvp_rect, pvai_rect, demo_rect, settings_rect = self.view.draw_menu()
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
                        self.ai2 = None
                        self.state = AppState.GAME
                        menu_active = False
                    
                    # Clic sur "Joueur vs IA"
                    elif pvai_rect.collidepoint(mouse_pos):
                        print("[CONTROLLER DEBUG] Mode sélectionné : PvAI")
                        self.gamemode = "PvAI"
                        # Utilisation de MinimaxAI avec profondeur 4 (configurable)
                        ai_depth = 4  # Peut être récupéré depuis la config si besoin
                        self.ai = MinimaxAI(depth=ai_depth, name="Minimax AI")
                        self.ai_player = 2
                        self.ai2 = None
                        self.state = AppState.GAME
                        menu_active = False
                    
                    # Clic sur "MODE DÉMO (IA vs IA)"
                    elif demo_rect.collidepoint(mouse_pos):
                        print("[CONTROLLER DEBUG] Mode sélectionné : AIvsAI (MODE DÉMO)")
                        self.gamemode = "AIvsAI"
                        # Création de deux IAs : IA1 (Joueur 1) et IA2 (Joueur 2)
                        self.ai = MinimaxAI(depth=4, name="Minimax IA Rouge")
                        self.ai_player = 1
                        self.ai2 = MinimaxAI(depth=4, name="Minimax IA Jaune")
                        self.ai2_player = 2
                        self.state = AppState.GAME
                        menu_active = False
                    
                    # Clic sur "Paramètres"
                    elif settings_rect.collidepoint(mouse_pos):
                        print("[CONTROLLER DEBUG] Ouverture des paramètres")
                        self.state = AppState.SETTINGS
                        menu_active = False
    
    def run_settings(self) -> None:
        """
        Gère l'affichage et les interactions de l'écran de paramètres.
        
        Permet de modifier :
        - Le nombre de lignes (4-10)
        - Le nombre de colonnes (4-12)
        - Le joueur qui commence (Rouge ou Jaune)
        
        Transitions possibles :
        - Clic sur "RETOUR" -> MENU (après sauvegarde)
        - Fermeture de la fenêtre -> QUIT
        """
        settings_active = True
        
        while settings_active and self.state == AppState.SETTINGS:
            self.clock.tick(self.fps)
            
            # Récupération de la configuration actuelle
            config = self.config_manager.get_config()
            
            # Affichage de l'écran de paramètres
            rects = self.view.draw_settings(config)
            self.view.update_display()
            
            # Gestion des événements
            for event in pygame.event.get():
                # Fermeture de la fenêtre
                if event.type == pygame.QUIT:
                    self.state = AppState.QUIT
                    settings_active = False
                    break
                
                # Clic de souris sur les boutons
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    
                    # Bouton [-] pour les lignes
                    if rects['rows_minus'].collidepoint(mouse_pos):
                        if self.config_manager.decrement_rows():
                            print(f"[SETTINGS DEBUG] Lignes : {self.config_manager.rows}")
                    
                    # Bouton [+] pour les lignes
                    elif rects['rows_plus'].collidepoint(mouse_pos):
                        if self.config_manager.increment_rows():
                            print(f"[SETTINGS DEBUG] Lignes : {self.config_manager.rows}")
                    
                    # Bouton [-] pour les colonnes
                    elif rects['cols_minus'].collidepoint(mouse_pos):
                        if self.config_manager.decrement_cols():
                            print(f"[SETTINGS DEBUG] Colonnes : {self.config_manager.cols}")
                    
                    # Bouton [+] pour les colonnes
                    elif rects['cols_plus'].collidepoint(mouse_pos):
                        if self.config_manager.increment_cols():
                            print(f"[SETTINGS DEBUG] Colonnes : {self.config_manager.cols}")
                    
                    # Bouton toggle pour le joueur qui commence
                    elif rects['player_toggle'].collidepoint(mouse_pos):
                        self.config_manager.toggle_start_player()
                        player_name = "Rouge" if self.config_manager.start_player == 1 else "Jaune"
                        print(f"[SETTINGS DEBUG] Joueur qui commence : {player_name}")
                    
                    # Bouton RETOUR
                    elif rects['back'].collidepoint(mouse_pos):
                        print("[SETTINGS DEBUG] Sauvegarde de la configuration et retour au menu")
                        self.config_manager.save_config()
                        self.state = AppState.MENU
                        settings_active = False
    
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
        # Récupération de la configuration actuelle
        config = self.config_manager.get_config()
        rows = config['rows']
        cols = config['cols']
        start_player = config['start_player']
        
        # Stockage des rectangles du sélecteur de profondeur
        self.depth_selector_rects = None
        
        # Stockage des rectangles du sélecteur de profondeur
        self.depth_selector_rects = None
        
        # Redimensionnement de la fenêtre si nécessaire
        from ..utils.constants import SQUARESIZE, HEADER_HEIGHT
        new_width = cols * SQUARESIZE
        new_height = rows * SQUARESIZE + HEADER_HEIGHT
        
        if new_width != self.view.width or new_height != self.view.height:
            print(f"[CONTROLLER DEBUG] Redimensionnement de la fenêtre : {new_width}x{new_height}")
            self.view.width = new_width
            self.view.height = new_height
            self.view.screen = pygame.display.set_mode((new_width, new_height))
        
        # Initialisation d'une nouvelle partie avec les paramètres configurés
        self.game = Game(rows=rows, cols=cols, start_player=start_player)
        
        print(f"\n[CONTROLLER DEBUG] === NOUVELLE PARTIE ({self.gamemode}) ===")
        print(f"[CONTROLLER DEBUG] Configuration : {rows}x{cols}, Joueur {start_player} commence")
        if self.gamemode == "PvAI":
            print(f"[CONTROLLER DEBUG] IA : {self.ai.name}")
            print(f"[CONTROLLER DEBUG] IA contrôle le joueur {self.ai_player}\n")
        elif self.gamemode == "AIvsAI":
            print(f"[CONTROLLER DEBUG] MODE DÉMO - IA1 : {self.ai.name} (Joueur {self.ai_player})")
            print(f"[CONTROLLER DEBUG] MODE DÉMO - IA2 : {self.ai2.name} (Joueur {self.ai2_player})\n")
        
        # Dessin initial du plateau vide avec bouton UI
        self._refresh_game_display()
        
        game_over = False
        current_hover_col: Optional[int] = None
        
        # Boucle de jeu
        while not game_over and self.state == AppState.GAME:
            # Limitation du framerate
            self.clock.tick(self.fps)
            
            # === GESTION DU MODE AI VS AI (DÉMO) ===
            if self.gamemode == "AIvsAI":
                current_player = self.game.get_current_player()
                print(f"\n[CONTROLLER DEBUG] === TOUR DE L'IA (Joueur {current_player}) ===")
                
                # Sélection de l'IA appropriée
                current_ai = self.ai if current_player == self.ai_player else self.ai2
                print(f"[CONTROLLER DEBUG] IA active : {current_ai.name}, Profondeur : {current_ai.depth}")
                
                # Étape 1 : Affichage "L'IA analyse..."
                self.view.draw_board(self.game.board)
                self.view.draw_thinking_bar(50, f"{current_ai.name} analyse...")
                self.view.update_display()
                
                # Pause courte
                pygame.time.wait(200)
                
                # Étape 2 : Calcul du coup par l'IA
                ai_column = current_ai.get_move(self.game.board)
                
                if ai_column is not None:
                    print(f"[CONTROLLER DEBUG] {current_ai.name} choisit la colonne {ai_column}")
                    
                    # Étape 3 : Récupération des scores
                    if hasattr(current_ai, 'get_last_scores'):
                        column_scores = current_ai.get_last_scores()
                    else:
                        column_scores = {}
                    
                    # Étape 4 : Affichage des scores AVANT de jouer
                    if column_scores and isinstance(current_ai, MinimaxAI):
                        self.view.draw_board(
                            self.game.board,
                            ai_scores=column_scores,
                            ai_player=current_player,
                            current_player=current_player
                        )
                        self.view.update_display()
                        
                        # Étape 5 : PAUSE pour suivre (500ms en mode démo)
                        pygame.time.wait(500)
                    
                    # Étape 6 : Placement du pion
                    print(f"[CONTROLLER DEBUG] Placement du pion en colonne {ai_column}")
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
                    print(f"[CONTROLLER DEBUG] ERREUR : {current_ai.name} n'a pas pu choisir de coup")
            
            # === GESTION DU TOUR DE L'IA (MODE PvAI) ===
            elif self.gamemode == "PvAI" and self.game.get_current_player() == self.ai_player:
                print(f"\n[CONTROLLER DEBUG] === TOUR DE L'IA ===")
                print(f"[CONTROLLER DEBUG] Profondeur actuelle : {self.ai.depth}")
                
                # Étape 1 : Affichage "L'IA analyse..."
                self.view.draw_board(self.game.board)
                self.view.draw_thinking_bar(50, "L'IA analyse...")
                self.view.update_display()
                
                # Pause pour rendre le jeu plus naturel
                pygame.time.wait(300)
                
                # Étape 2 : Calcul du coup par l'IA (Minimax)
                ai_column = self.ai.get_move(self.game.board)
                
                if ai_column is not None:
                    print(f"[CONTROLLER DEBUG] IA choisit la colonne {ai_column}")
                    
                    # Étape 3 : Récupération des scores calculés
                    if hasattr(self.ai, 'get_last_scores'):
                        column_scores = self.ai.get_last_scores()
                    else:
                        column_scores = {}
                    
                    # Étape 4 : Affichage des scores AVANT de jouer le coup
                    if column_scores and isinstance(self.ai, MinimaxAI):
                        print(f"[CONTROLLER DEBUG] Affichage des scores avant le coup")
                        # Rafraîchissement avec scores intégrés dans draw_board
                        self.view.draw_board(
                            self.game.board,
                            ai_scores=column_scores,
                            ai_player=self.ai_player,
                            current_player=self.game.get_current_player()
                        )
                        # Affichage du sélecteur de profondeur
                        if hasattr(self.ai, 'depth'):
                            self.depth_selector_rects = self.view.draw_depth_selector(self.ai.depth)
                        self.view.update_display()
                        
                        # Étape 5 : PAUSE pour lire les scores (1 seconde)
                        pygame.time.wait(1000)
                    
                    # Étape 6 : Placement du pion de l'IA
                    print(f"[CONTROLLER DEBUG] Placement du pion en colonne {ai_column}")
                    success = self.game.play_turn(ai_column)
                    
                    if success:
                        # Mise à jour de l'affichage après le coup
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
                
                # Gestion des touches clavier
                if event.type == pygame.KEYDOWN:
                    # Touche ECHAP : Retour au menu (utile en mode démo)
                    if event.key == pygame.K_ESCAPE:
                        print("[CONTROLLER DEBUG] Touche ÉCHAP pressée - Retour au menu")
                        self.state = AppState.MENU
                        game_over = True
                        break
                    
                    # Touche R : Recommencer la partie
                    elif event.key == pygame.K_r:
                        print("[CONTROLLER DEBUG] Touche R pressée - Reset de la partie")
                        self.reset_game()
                        continue
                
                # Mouvement de la souris : affichage du pion fantôme (uniquement pour le joueur humain)
                if event.type == pygame.MOUSEMOTION:
                    # Ne pas afficher le pion fantôme en mode AIvsAI ou pendant le tour de l'IA
                    if self.gamemode == "AIvsAI":
                        continue
                    if self.gamemode == "PvAI" and self.game.get_current_player() == self.ai_player:
                        continue
                    
                    # Rafraîchissement avec pion fantôme intégré
                    # draw_board() gère automatiquement le calcul de colonne et l'affichage
                    self._refresh_game_display(mouse_x=event.pos[0])
                
                # Clic de souris : gestion avec distinction stricte UI vs Plateau
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    
                    # ========================================
                    # BRANCHE 0 : CLIC SUR SÉLECTEUR DE PROFONDEUR (PvAI uniquement)
                    # ========================================
                    if self.gamemode == "PvAI" and self.depth_selector_rects:
                        # Clic sur bouton [ + ]
                        if self.depth_selector_rects['plus'].collidepoint(mouse_pos):
                            if self.ai.depth < 7:  # Limite max
                                self.ai.depth += 1
                                print(f"[CONTROLLER DEBUG] Profondeur augmentée à {self.ai.depth}")
                                self._refresh_game_display()
                            continue
                        
                        # Clic sur bouton [ - ]
                        elif self.depth_selector_rects['minus'].collidepoint(mouse_pos):
                            if self.ai.depth > 1:  # Limite min
                                self.ai.depth -= 1
                                print(f"[CONTROLLER DEBUG] Profondeur diminuée à {self.ai.depth}")
                                self._refresh_game_display()
                            continue
                    
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
                    # BRANCHE 4 : CLIC SUR BOUTON RECOMMENCER
                    # ========================================
                    elif self.view.restart_button_rect and self.view.restart_button_rect.collidepoint(mouse_pos):
                        print("\n[CONTROLLER DEBUG] === CLIC SUR BOUTON RECOMMENCER ===")
                        
                        # Réinitialisation de la partie
                        self.reset_game()
                        
                        print("[CONTROLLER DEBUG] === FIN TRAITEMENT RECOMMENCER ===\n")
                    
                    # ========================================
                    # BRANCHE 5 : CLIC SUR LE PLATEAU
                    # ========================================
                    else:
                        # Ignorer les clics si la partie est terminée
                        if self.game.game_state == "FINISHED":
                            print("[CONTROLLER DEBUG] Clic ignoré - Partie terminée")
                            continue
                        
                        # Ignorer les clics en mode AIvsAI (démo automatique)
                        if self.gamemode == "AIvsAI":
                            print("[CONTROLLER DEBUG] Clic ignoré - Mode DÉMO (AIvsAI)")
                            continue
                        
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
                                    # game_over = True  # Commenté: on reste dans la boucle pour gérer l'affichage
        
        # Note : La gestion des touches ECHAP et R continue même après game over
        # Cette ligne n'est exécutée que si la partie est interrompue sans game over
        if self.state == AppState.GAME:
            self.state = AppState.MENU
            print("\n[CONTROLLER DEBUG] Retour au menu principal (partie interrompue)\n")
    
    def run_game_over(self) -> None:
        """
        Gère l'état de fin de partie avec grille figée.
        
        Affiche la grille finale avec le résultat et attend une action utilisateur :
        - ECHAP : Retour au menu principal
        - R : Recommencer une nouvelle partie avec les mêmes paramètres
        
        Les joueurs ne peuvent plus poser de pions, la grille est figée.
        """
        print("\n[CONTROLLER DEBUG] === ÉTAT GAME_OVER (Grille figée) ===")
        
        game_over_active = True
        
        while game_over_active and self.state == AppState.GAME_OVER:
            # Limitation du framerate
            self.clock.tick(self.fps)
            
            # Gestion des événements
            for event in pygame.event.get():
                # Fermeture de la fenêtre
                if event.type == pygame.QUIT:
                    self.state = AppState.QUIT
                    game_over_active = False
                    break
                
                # Gestion des touches clavier
                if event.type == pygame.KEYDOWN:
                    # Touche ECHAP : Retour au menu
                    if event.key == pygame.K_ESCAPE:
                        print("[CONTROLLER DEBUG] Touche ÉCHAP pressée - Retour au menu")
                        self.state = AppState.MENU
                        game_over_active = False
                        break
                    
                    # Touche R : Recommencer une partie
                    elif event.key == pygame.K_r:
                        print("[CONTROLLER DEBUG] Touche R pressée - Recommencer une partie")
                        self.state = AppState.GAME
                        game_over_active = False
                        break
        
        print("[CONTROLLER DEBUG] === FIN ÉTAT GAME_OVER ===\n")
    
    def reset_game(self) -> None:
        """
        Réinitialise la partie en cours pour recommencer une nouvelle manche.
        
        Cette méthode :
        - Marque l'ancienne partie comme 'ABANDONNEE' (si en cours)
        - Appelle game.reset() pour vider le plateau et générer un nouvel ID
        - Rafraîchit l'affichage pour montrer le plateau vide
        
        Peut être appelée à tout moment pendant une partie (même non terminée).
        """
        if self.game is None:
            print("[CONTROLLER DEBUG] Impossible de reset : aucune partie en cours")
            return
        
        print("\n[CONTROLLER DEBUG] === RESET DE LA PARTIE ===")
        old_id = self.game.game_id
        
        # Reset du jeu (génère un nouvel ID et vide le plateau)
        self.game.reset()
        
        print(f"[CONTROLLER DEBUG] Partie {old_id} -> Nouvelle partie {self.game.game_id}")
        
        # Rafraîchissement de l'affichage
        self._refresh_game_display()
        
        print("[CONTROLLER DEBUG] === RESET TERMINÉ ===\n")
    
    def _handle_game_over(self) -> None:
        """
        Gère l'affichage de fin de partie et la sauvegarde en base de données.
        
        Centralise la logique d'affichage de victoire/égalité.
        Sauvegarde automatiquement la partie dans la base de données MySQL.
        """
        print("\n[CONTROLLER DEBUG] === GESTION FIN DE PARTIE ===")
        
        # Sauvegarde dans la base de données
        self._save_game_to_database()
        
        # Force un dernier rafraîchissement du plateau avec ligne gagnante
        winner = self.game.get_winner()
        winning_line = self.game.get_winning_positions()
        
        # Affichage du plateau final avec overlay de victoire
        self.view.draw_board(self.game.board, winning_line=winning_line)
        self.view.draw_victory_overlay(winner, winning_line)
        self.view.update_display()
        
        # Message console pour débogage
        if winner is not None:
            player_name = "ROUGE" if winner == 1 else "JAUNE"
            print(f"🎉 Le joueur {player_name} a gagné!")
            print(f"   Ligne gagnante : {winning_line}")
        else:
            print("🤝 Égalité - Plateau rempli!")
        
        print("[CONTROLLER DEBUG] === FIN GESTION ===\n")
    
    def _save_game_to_database(self) -> None:
        """
        Sauvegarde la partie terminée dans la base de données MySQL.
        
        Convertit l'historique des coups en chaîne et appelle le DatabaseManager
        pour insertion avec chaînage automatique.
        """
        try:
            from ..utils.db_manager import DatabaseManager
            import json
            
            # Conversion de l'historique en chaîne de colonnes
            coups = ''.join(str(col + 1) for col, _ in self.game.move_history)
            
            # Détermination du statut
            statut = 'TERMINEE'
            
            # Préparation de la ligne gagnante au format JSON
            ligne_gagnante = None
            if self.game.winner is not None:
                ligne_gagnante = json.dumps(self.game.winning_line)
            
            # Connexion et sauvegarde
            db = DatabaseManager()
            db.connect()
            db.create_tables()
            
            game_id = db.insert_game(
                coups=coups,
                mode_jeu=self.gamemode,
                statut=statut,
                ligne_gagnante=ligne_gagnante
            )
            
            db.disconnect()
            
            if game_id:
                print(f"[DB] ✅ Partie sauvegardée avec l'ID {game_id}")
            else:
                print(f"[DB] ⚠️ Partie non sauvegardée (doublon possible)")
                
        except Exception as e:
            print(f"[DB] ❌ Erreur lors de la sauvegarde : {e}")
        
        # Transition vers l'état GAME_OVER (grille figée)
        self.state = AppState.GAME_OVER
        print("[CONTROLLER DEBUG] Transition vers l'état GAME_OVER")
