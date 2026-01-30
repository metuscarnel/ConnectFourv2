"""
Module du contrôleur principal du jeu.
Orchestre les interactions entre le modèle (logique) et la vue (affichage).
Gère une machine à états (Menu -> Jeu -> Retour au Menu).
"""

from typing import Optional
import pygame
import sys
import time
import subprocess
import platform

from ..models.game import Game
from ..views.pygame_view import PygameView
from ..ai.random_ai import RandomAI
from ..ai.minimax_ai import MinimaxAI
from ..utils.enums import AppState
from ..utils import data_manager
from ..utils.config_manager import ConfigManager
from ..utils.settings_manager import SettingsManager


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
        self.settings_manager: SettingsManager = SettingsManager()  # Gestionnaire de paramètres
        
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
            
            elif self.state == AppState.HISTORY_MENU:
                print("[CONTROLLER DEBUG] État : HISTORY_MENU")
                self.run_history_menu()
            
            elif self.state == AppState.REPLAY_MODE:
                print("[CONTROLLER DEBUG] État : REPLAY_MODE")
                self.run_replay_mode()
        
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
    
    def _select_import_file(self) -> Optional[str]:
        """
        Ouvre un explorateur de fichiers pour sélectionner un fichier .txt à importer.
        
        Utilise osascript (AppleScript) sur macOS pour éviter les problèmes de tkinter.
        
        Returns:
            Chemin du fichier sélectionné, ou None si annulé
        """
        try:
            if platform.system() == "Darwin":  # macOS
                # Utilisation d'AppleScript natif pour macOS
                script = '''
                tell application "System Events"
                    activate
                    set filePath to choose file with prompt "Sélectionner un fichier .txt à importer" of type {"txt"} default location (path to home folder)
                    return POSIX path of filePath
                end tell
                '''
                
                result = subprocess.run(
                    ['osascript', '-e', script],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    file_path = result.stdout.strip()
                    print(f"[CONTROLLER DEBUG] Fichier sélectionné : {file_path}")
                    return file_path
                else:
                    print("[CONTROLLER DEBUG] Sélection annulée")
                    return None
            else:
                # Pour d'autres systèmes, retourner None
                print("[CONTROLLER DEBUG] Sélection de fichier non supportée sur ce système")
                return None
                
        except subprocess.TimeoutExpired:
            print("[CONTROLLER ERROR] Timeout lors de la sélection du fichier")
            return None
        except Exception as e:
            print(f"[CONTROLLER ERROR] Erreur lors de la sélection du fichier : {e}")
            return None
    
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
        
        # Import du DatabaseManager pour l'importation
        from ..utils.db_manager import DatabaseManager
        
        while menu_active and self.state == AppState.MENU:
            self.clock.tick(self.fps)
            
            # Affichage du menu et récupération des rectangles de boutons (7 boutons maintenant)
            pvp_rect, pvai_rect, demo_rect, history_rect, settings_rect, import_rect, quit_rect = self.view.draw_menu()
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
                    
                    # Clic sur "Historique"
                    elif history_rect.collidepoint(mouse_pos):
                        print("[CONTROLLER DEBUG] Ouverture de l'historique")
                        self.state = AppState.HISTORY_MENU
                        menu_active = False
                    
                    # Clic sur "PARAMÈTRES"
                    elif settings_rect.collidepoint(mouse_pos):
                        print("[CONTROLLER DEBUG] Ouverture des paramètres")
                        self.state = AppState.SETTINGS
                        menu_active = False
                    
                    # Clic sur "IMPORTER (.txt)"
                    elif import_rect.collidepoint(mouse_pos):
                        print("[CONTROLLER DEBUG] Bouton IMPORTER cliqué")
                        
                        # Ouverture de l'explorateur de fichiers
                        file_path = self._select_import_file()
                        
                        if file_path:
                            print(f"[CONTROLLER DEBUG] Fichier sélectionné : {file_path}")
                            
                            # Affichage du message "Importation en cours..."
                            self.view.draw_status_message(
                                "Importation en cours...",
                                "info"
                            )
                            self.view.update_display()
                            
                            # Connexion à la base et import
                            db = DatabaseManager()
                            db.connect()
                            db.create_tables()
                            
                            try:
                                # Appel de la fonction d'importation avec le fichier sélectionné
                                result = db.import_from_txt_file(file_path)
                                
                                # Affichage du résultat
                                if result['success']:
                                    message = f"Import réussi ! Partie ID {result['game_id']} ajoutée."
                                    msg_type = "success"
                                else:
                                    message = f"Erreur : {result['error']}"
                                    msg_type = "error" if "Erreur" in result['error'] else "warning"
                                
                                self.view.draw_status_message(message, msg_type)
                                self.view.update_display()
                                time.sleep(3)  # Pause de 3 secondes
                                
                            except Exception as e:
                                print(f"[CONTROLLER ERROR] Erreur d'importation : {e}")
                                self.view.draw_status_message(
                                    f"Erreur d'importation : {str(e)}",
                                    "error"
                                )
                                self.view.update_display()
                                time.sleep(3)
                            
                            finally:
                                db.disconnect()
                        else:
                            print("[CONTROLLER DEBUG] Sélection de fichier annulée")
                    
                    # Clic sur "QUITTER"
                    elif quit_rect.collidepoint(mouse_pos):
                        print("[CONTROLLER DEBUG] Bouton QUITTER cliqué")
                        print("[CONTROLLER DEBUG] Fermeture propre de l'application...")
                        
                        # Fermeture de la connexion MySQL si elle existe
                        try:
                            db = DatabaseManager()
                            if db.connection and db.connection.is_connected():
                                db.disconnect()
                                print("[CONTROLLER DEBUG] Connexion MySQL fermée")
                        except Exception as e:
                            print(f"[CONTROLLER DEBUG] Note : {e}")
                        
                        # Fermeture de Pygame
                        pygame.quit()
                        print("[CONTROLLER DEBUG] Pygame fermé")
                        
                        # Sortie de Python
                        print("[CONTROLLER DEBUG] Au revoir !")
                        sys.exit(0)
    
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
                    # BRANCHE 5 : CLIC SUR BOUTON MENU (RETOUR)
                    # ========================================
                    elif self.view.menu_button_rect and self.view.menu_button_rect.collidepoint(mouse_pos):
                        print("\n[CONTROLLER DEBUG] === CLIC SUR BOUTON MENU ===")
                        print("[CONTROLLER DEBUG] Retour au menu principal (partie interrompue)")
                        self.state = AppState.MENU
                        game_over = True  # Sortir de la boucle
                        break
                    
                    # ========================================
                    # BRANCHE 6 : CLIC SUR LE PLATEAU
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
    
    def run_history_menu(self) -> None:
        """
        Affiche la liste des parties enregistrées dans la base de données.
        Permet de sélectionner une partie pour la visualiser en mode replay.
        """
        from ..utils.db_manager import DatabaseManager
        
        print("\n[CONTROLLER DEBUG] === CHARGEMENT HISTORIQUE ===")
        
        # Chargement des parties depuis la base de données
        db = DatabaseManager()
        db.connect()
        games = db.get_all_games()
        db.disconnect()
        
        print(f"[CONTROLLER DEBUG] {len(games)} partie(s) chargée(s)")
        
        history_active = True
        
        while history_active and self.state == AppState.HISTORY_MENU:
            self.clock.tick(self.fps)
            
            # Affichage de l'historique
            rects = self.view.draw_history_menu(games)
            self.view.update_display()
            
            # Gestion des événements
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.state = AppState.QUIT
                    history_active = False
                    break
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.state = AppState.MENU
                        history_active = False
                        break
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    
                    # Clic sur "RETOUR"
                    if rects['back'].collidepoint(mouse_pos):
                        print("[CONTROLLER DEBUG] Retour au menu")
                        self.state = AppState.MENU
                        history_active = False
                        break
                    
                    # Clic sur une partie
                    for i in range(len(games[:10])):
                        if i in rects and rects[i].collidepoint(mouse_pos):
                            print(f"[CONTROLLER DEBUG] Partie {games[i]['id']} sélectionnée")
                            self._load_replay(games[i])
                            history_active = False
                            break
    
    def _load_replay(self, game_data: dict) -> None:
        """
        Charge une partie pour le mode replay.
        
        Args:
            game_data: Dictionnaire contenant les données de la partie
        """
        # Stockage des données de replay
        self.replay_game_data = game_data
        self.replay_current_move = 0
        self.replay_show_symmetric = False
        self.replay_auto_play = False
        
        # Création d'un plateau vide
        from ..models.board import Board
        config = self.config_manager.get_config()
        self.replay_board = Board(rows=config['rows'], cols=config['cols'])
        
        print(f"[REPLAY DEBUG] Chargement partie ID {game_data['id']}")
        print(f"[REPLAY DEBUG] Coups: {game_data['coups']}")
        
        # Transition vers le mode replay
        self.state = AppState.REPLAY_MODE
    
    def run_replay_mode(self) -> None:
        """
        Mode visualisation d'une partie enregistrée avec navigation pas-à-pas.
        """
        print("\n[CONTROLLER DEBUG] === MODE REPLAY ===")
        
        replay_active = True
        coups = self.replay_game_data['coups'] if not self.replay_show_symmetric else self.replay_game_data['coups_symetrique']
        total_moves = len(coups)
        
        # Conversion des coups en liste (colonnes en base 1)
        moves_list = [int(c) - 1 for c in coups]  # Conversion en base 0
        
        while replay_active and self.state == AppState.REPLAY_MODE:
            self.clock.tick(self.fps)
            
            # Vérification des voisins dans le chaînage
            has_prev = self.replay_game_data['id_antecedent'] is not None
            has_next = self.replay_game_data['id_suivant'] is not None
            
            # Affichage du replay
            rects = self.view.draw_replay_interface(
                self.replay_board,
                self.replay_current_move,
                total_moves,
                self.replay_game_data,
                has_prev,
                has_next,
                self.replay_show_symmetric
            )
            
            # Affichage de la ligne gagnante si on est à la fin
            if self.replay_current_move == total_moves and self.replay_game_data['ligne_gagnante']:
                try:
                    import json
                    import ast
                    
                    # Parsing robuste depuis la base de données
                    coords_brutes = self.replay_game_data['ligne_gagnante']
                    
                    # Tentative de parsing JSON
                    try:
                        winning_line_raw = json.loads(coords_brutes)
                    except (json.JSONDecodeError, TypeError):
                        # Fallback: tentative de parsing avec ast.literal_eval
                        try:
                            winning_line_raw = ast.literal_eval(coords_brutes)
                        except (ValueError, SyntaxError):
                            print(f"[REPLAY ERROR] Impossible de parser les coordonnées: {coords_brutes}")
                            winning_line_raw = None
                    
                    if winning_line_raw:
                        # Conversion robuste en liste de tuples d'entiers
                        # Format attendu: [(row, col), ...] en Base 0 (index Python)
                        winning_line_converted = []
                        for coord in winning_line_raw:
                            if isinstance(coord, (list, tuple)) and len(coord) == 2:
                                # Les coordonnées sont déjà en Base 0 depuis get_winning_positions()
                                row, col = int(coord[0]), int(coord[1])
                                # Vérification de sécurité
                                if 0 <= row < 8 and 0 <= col < 9:
                                    winning_line_converted.append((row, col))
                                else:
                                    print(f"[REPLAY WARNING] Coordonnée hors limites ignorée: ({row}, {col})")
                        
                        if winning_line_converted:
                            self.view.draw_winning_highlight(winning_line_converted, self.replay_board)
                        else:
                            print("[REPLAY WARNING] Aucune coordonnée valide après conversion")
                    
                except Exception as e:
                    print(f"[REPLAY ERROR] Erreur lors du surlignement: {e}")
            
            self.view.update_display()
            
            # Gestion des événements
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.state = AppState.QUIT
                    replay_active = False
                    break
                
                if event.type == pygame.KEYDOWN:
                    # ECHAP : Retour à l'historique
                    if event.key == pygame.K_ESCAPE:
                        self.state = AppState.HISTORY_MENU
                        replay_active = False
                        break
                    
                    # Flèche GAUCHE : Coup précédent
                    elif event.key == pygame.K_LEFT:
                        if self.replay_current_move > 0:
                            self._replay_undo_move()
                            print(f"[REPLAY DEBUG] Coup {self.replay_current_move}/{total_moves}")
                    
                    # Flèche DROITE : Coup suivant
                    elif event.key == pygame.K_RIGHT:
                        if self.replay_current_move < total_moves:
                            self._replay_play_move(moves_list[self.replay_current_move])
                            print(f"[REPLAY DEBUG] Coup {self.replay_current_move}/{total_moves}")
                    
                    # M : Basculer vers symétrie
                    elif event.key == pygame.K_m:
                        self._toggle_symmetric()
                    
                    # ESPACE : Lecture automatique
                    elif event.key == pygame.K_SPACE:
                        self.replay_auto_play = not self.replay_auto_play
                        print(f"[REPLAY DEBUG] Lecture auto: {self.replay_auto_play}")
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    
                    # Bouton PRÉCÉDENT (partie antécédente)
                    if rects['prev'] and rects['prev'].collidepoint(mouse_pos):
                        self._load_neighbor_game('prev')
                        # Recharger les coups
                        coups = self.replay_game_data['coups'] if not self.replay_show_symmetric else self.replay_game_data['coups_symetrique']
                        total_moves = len(coups)
                        moves_list = [int(c) - 1 for c in coups]
                    
                    # Bouton SUIVANT (partie suivante)
                    elif rects['next'] and rects['next'].collidepoint(mouse_pos):
                        self._load_neighbor_game('next')
                        # Recharger les coups
                        coups = self.replay_game_data['coups'] if not self.replay_show_symmetric else self.replay_game_data['coups_symetrique']
                        total_moves = len(coups)
                        moves_list = [int(c) - 1 for c in coups]
                    
                    # Bouton SYMÉTRIE
                    elif rects['symmetric'].collidepoint(mouse_pos):
                        self._toggle_symmetric()
                        coups = self.replay_game_data['coups'] if not self.replay_show_symmetric else self.replay_game_data['coups_symetrique']
                        total_moves = len(coups)
                        moves_list = [int(c) - 1 for c in coups]
                    
                    # Bouton RETOUR
                    elif rects['back'].collidepoint(mouse_pos):
                        self.state = AppState.HISTORY_MENU
                        replay_active = False
                        break
            
            # Lecture automatique
            if self.replay_auto_play and self.replay_current_move < total_moves:
                pygame.time.wait(500)  # Pause de 500ms entre chaque coup
                self._replay_play_move(moves_list[self.replay_current_move])
    
    def _replay_play_move(self, col: int) -> None:
        """Joue un coup dans le replay."""
        if self.replay_board.is_valid_location(col):
            row = self.replay_board.get_next_open_row(col)
            player = 1 if (self.replay_current_move % 2 == 0) else 2
            self.replay_board.drop_piece(row, col, player)
            self.replay_current_move += 1
    
    def _replay_undo_move(self) -> None:
        """Annule le dernier coup du replay."""
        if self.replay_current_move > 0:
            self.replay_board.undo_last_move()
            self.replay_current_move -= 1
    
    def _toggle_symmetric(self) -> None:
        """Bascule entre affichage normal et symétrique."""
        self.replay_show_symmetric = not self.replay_show_symmetric
        print(f"[REPLAY DEBUG] Mode symétrique: {self.replay_show_symmetric}")
        
        # Réinitialiser le plateau et rejouer avec la nouvelle séquence
        config = self.config_manager.get_config()
        from ..models.board import Board
        self.replay_board = Board(rows=config['rows'], cols=config['cols'])
        
        coups = self.replay_game_data['coups_symetrique'] if self.replay_show_symmetric else self.replay_game_data['coups']
        moves_list = [int(c) - 1 for c in coups]
        
        # Rejouer tous les coups jusqu'à la position actuelle
        current_pos = self.replay_current_move
        self.replay_current_move = 0
        
        for i in range(current_pos):
            self._replay_play_move(moves_list[i])
    
    def _load_neighbor_game(self, direction: str) -> None:
        """
        Charge la partie voisine dans le chaînage.
        
        Args:
            direction: 'prev' pour id_antecedent, 'next' pour id_suivant
        """
        from ..utils.db_manager import DatabaseManager
        
        neighbor_id = None
        if direction == 'prev':
            neighbor_id = self.replay_game_data['id_antecedent']
        else:
            neighbor_id = self.replay_game_data['id_suivant']
        
        if neighbor_id is None:
            print(f"[REPLAY DEBUG] Pas de partie {direction}")
            return
        
        # Chargement de la partie voisine
        db = DatabaseManager()
        db.connect()
        neighbor_game = db.get_game_by_id(neighbor_id)
        db.disconnect()
        
        if neighbor_game:
            print(f"[REPLAY DEBUG] Chargement partie {neighbor_id} ({direction})")
            self._load_replay(neighbor_game)
    
    def run_settings_menu(self) -> None:
        """
        Gère l'affichage et les interactions du menu des paramètres.
        
        Permet de configurer :
        - Les couleurs des joueurs et de la grille
        - Le volume sonore
        - La réinitialisation de la base de données
        """
        settings_active = True
        showing_confirmation = False
        confirmation_rects = None
        
        while settings_active and self.state == AppState.SETTINGS:
            self.clock.tick(self.fps)
            
            # Affichage du menu des paramètres
            rects = self.view.draw_settings_menu(self.settings_manager)
            
            # Si une confirmation est en cours, afficher le dialogue par-dessus
            if showing_confirmation:
                yes_rect, no_rect = self.view.draw_confirmation_dialog(
                    "Voulez-vous vraiment effacer tout l'historique des parties ?"
                )
                confirmation_rects = (yes_rect, no_rect)
            
            self.view.update_display()
            
            # Gestion des événements
            for event in pygame.event.get():
                # Fermeture de la fenêtre
                if event.type == pygame.QUIT:
                    self.state = AppState.QUIT
                    settings_active = False
                    break
                
                # Clic de souris
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    
                    # Si dialogue de confirmation affiché
                    if showing_confirmation and confirmation_rects:
                        yes_rect, no_rect = confirmation_rects
                        
                        if yes_rect.collidepoint(mouse_pos):
                            # Confirmation : vider la BDD
                            print("[SETTINGS DEBUG] Réinitialisation de la BDD confirmée")
                            from ..utils.db_manager import DatabaseManager
                            
                            db = DatabaseManager()
                            db.connect()
                            success = db.truncate_games()
                            db.disconnect()
                            
                            if success:
                                self.view.draw_status_message(
                                    "Base de données vidée avec succès !",
                                    "success"
                                )
                            else:
                                self.view.draw_status_message(
                                    "Erreur lors de la réinitialisation",
                                    "error"
                                )
                            
                            self.view.update_display()
                            pygame.time.wait(2000)
                            showing_confirmation = False
                        
                        elif no_rect.collidepoint(mouse_pos):
                            # Annulation
                            print("[SETTINGS DEBUG] Réinitialisation annulée")
                            showing_confirmation = False
                    
                    # Sinon, gestion des clics normaux
                    else:
                        # Bouton RETOUR
                        if rects['back'].collidepoint(mouse_pos):
                            print("[SETTINGS DEBUG] Retour au menu principal")
                            self.state = AppState.MENU
                            settings_active = False
                        
                        # Bouton Réinitialiser BDD
                        elif rects['reset_db'].collidepoint(mouse_pos):
                            print("[SETTINGS DEBUG] Demande de réinitialisation BDD")
                            showing_confirmation = True
                        
                        # Clic sur preview de couleur (pour info, extension future)
                        elif 'player1_preview' in rects and rects['player1_preview'].collidepoint(mouse_pos):
                            print("[SETTINGS DEBUG] Clic sur couleur Joueur 1 (à implémenter)")
                        
                        elif 'player2_preview' in rects and rects['player2_preview'].collidepoint(mouse_pos):
                            print("[SETTINGS DEBUG] Clic sur couleur Joueur 2 (à implémenter)")
                        
                        elif 'grid_preview' in rects and rects['grid_preview'].collidepoint(mouse_pos):
                            print("[SETTINGS DEBUG] Clic sur couleur Grille (à implémenter)")
                        
                        # Slider de volume (clic pour ajuster)
                        elif 'volume_slider' in rects and rects['volume_slider'].collidepoint(mouse_pos):
                            slider_rect = rects['volume_slider']
                            # Calcul de la position relative dans le slider
                            relative_x = mouse_pos[0] - slider_rect.x
                            new_volume = int((relative_x / slider_rect.width) * 100)
                            new_volume = max(0, min(100, new_volume))  # Clamp entre 0 et 100
                            
                            self.settings_manager.update_setting("volume", "master", new_volume)
                            print(f"[SETTINGS DEBUG] Volume ajusté à {new_volume}%")
                
                # Déplacement de souris (pour slider continu)
                elif event.type == pygame.MOUSEMOTION:
                    # Si le bouton gauche est enfoncé
                    if pygame.mouse.get_pressed()[0]:  # Bouton gauche enfoncé
                        mouse_pos = event.pos
                        
                        # Vérifier si on est sur le slider de volume
                        if 'volume_slider' in rects and rects['volume_slider'].collidepoint(mouse_pos):
                            slider_rect = rects['volume_slider']
                            relative_x = mouse_pos[0] - slider_rect.x
                            new_volume = int((relative_x / slider_rect.width) * 100)
                            new_volume = max(0, min(100, new_volume))
                            
                            self.settings_manager.update_setting("volume", "master", new_volume)
