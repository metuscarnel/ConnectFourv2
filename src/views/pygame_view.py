"""
Module de la vue Pygame pour l'interface graphique du jeu.
Gère l'affichage du plateau, des pions et des animations.
"""

from typing import Optional
import pygame
import numpy as np
from numpy.typing import NDArray

from ..models.board import Board
from ..utils.constants import (
    ROWS, COLS, EMPTY, PLAYER1, PLAYER2,
    SQUARESIZE, WIDTH, HEIGHT, HEADER_HEIGHT,
    BLUE, BLACK, RED, YELLOW, WHITE, GREEN
)
from ..utils.settings_manager import SettingsManager


class PygameView:
    """
    Vue graphique utilisant Pygame pour afficher le jeu Puissance 4.
    
    Gère le rendu visuel du plateau, des pions et des éléments d'interface.
    Respecte le pattern MVC : cette classe ne contient aucune logique de jeu.
    
    Attributes:
        width: Largeur totale de la fenêtre
        height: Hauteur totale de la fenêtre (inclut zone de prévisualisation)
        radius: Rayon des pions
        screen: Surface Pygame principale
        font: Police pour les textes
    """
    
    # Constantes visuelles calculées
    RADIUS: int = int(SQUARESIZE / 2 - 5)  # Rayon des pions (marge de 5px)
    
    # Constantes de layout pour séparation grille/panneau
    GAME_AREA_RATIO: float = 0.75  # 75% pour la zone de jeu
    NAV_AREA_RATIO: float = 0.25   # 25% pour le panneau de navigation
    
    def __init__(self, settings_manager: Optional[SettingsManager] = None) -> None:
        """
        Initialise la fenêtre Pygame avec les dimensions calculées dynamiquement.
        
        Args:
            settings_manager: Gestionnaire de paramètres pour les couleurs personnalisées
        
        La fenêtre comprend :
        - Une ligne en haut pour afficher le pion de prévisualisation
        - Le plateau de jeu (ROWS x COLS)
        """
        pygame.init()
        
        # Gestionnaire de paramètres
        self.settings_manager = settings_manager if settings_manager else SettingsManager()
        
        # Utilisation des dimensions depuis constants.py
        self.width: int = WIDTH
        self.height: int = HEIGHT
        self.radius: int = self.RADIUS
        
        # Calcul des zones de layout
        self._update_layout()
        
        # Création de la fenêtre
        self.screen: pygame.Surface = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Puissance 4 - Connect Four")
        
        # Police pour les textes (tailles adaptées)
        self.font: pygame.font.Font = pygame.font.SysFont("monospace", 55)
        self.small_font: pygame.font.Font = pygame.font.SysFont("monospace", 30)
        
        # Rectangles des boutons pour détection des clics
        self.undo_button_rect: Optional[pygame.Rect] = None
        self.save_button_rect: Optional[pygame.Rect] = None
        self.load_button_rect: Optional[pygame.Rect] = None
        self.restart_button_rect: Optional[pygame.Rect] = None
        self.menu_button_rect: Optional[pygame.Rect] = None
    
    def _update_layout(self) -> None:
        """
        Calcule les zones de layout pour séparer la grille du panneau de navigation.
        
        Divise l'écran en deux zones :
        - GAME_RECT (75% largeur) : Zone centrée pour la grille de jeu
        - NAV_RECT (25% largeur) : Zone fixe pour le panneau de navigation/contrôles
        
        Calcule aussi CELL_SIZE dynamiquement pour que la grille tienne dans GAME_RECT.
        """
        # Zone de jeu (75% de la largeur)
        game_width = int(self.width * self.GAME_AREA_RATIO)
        self.game_rect = pygame.Rect(0, 0, game_width, self.height)
        
        # Zone de navigation (25% de la largeur, à droite)
        nav_width = int(self.width * self.NAV_AREA_RATIO)
        self.nav_rect = pygame.Rect(game_width, 0, nav_width, self.height)
        
        # Calcul dynamique de la taille des cellules
        # La grille fait 9 colonnes + 1 pour les marges = 10 cellules en largeur
        # La grille fait 8 lignes + 1 pour preview = 9 cellules en hauteur
        cell_width = (game_width - 40) / 10  # -40px pour marges
        cell_height = (self.height - 40) / 9  # -40px pour marges
        
        self.cell_size = int(min(cell_width, cell_height))
        self.cell_radius = int(self.cell_size / 2 - 5)
        
        # Position de départ pour centrer la grille dans game_rect
        grid_width = self.cell_size * COLS
        grid_height = self.cell_size * (ROWS + 1)  # +1 pour preview
        
        self.grid_start_x = (game_width - grid_width) // 2
        self.grid_start_y = (self.height - grid_height) // 2
    
    def draw_board(self, board: Board, mouse_x: Optional[int] = None, current_player: int = PLAYER1, ai_scores: Optional[dict] = None, ai_player: int = 2, winning_line: Optional[list[tuple[int, int]]] = None) -> None:
        """
        Dessine le plateau de jeu avec tous les pions actuels en 3 couches distinctes.
        
        Convention stricte : row=0 de la matrice = BAS physique de l'écran.
        
        Architecture en couches :
        - COUCHE 0 : Header (zone réservée pour l'UI en haut)
        - COUCHE 1 : Plateau bleu + pions existants (décalé de HEADER_HEIGHT)
        - COUCHE 2 : Pion fantôme (optionnel, si mouse_x fourni)
        - COUCHE 3 : UI fixe (bouton Annuler dans la zone header)
        - COUCHE 4 : Scores IA (optionnel, si ai_scores fourni)
        - COUCHE 5 : Ligne gagnante (optionnel, si winning_line fourni)
        
        Args:
            board: Instance du plateau à afficher
            mouse_x: Position X de la souris (optionnel) pour afficher le pion fantôme
            current_player: Joueur actuel (pour la couleur du pion fantôme)
            ai_scores: Scores calculés par l'IA (optionnel) pour affichage avant le coup
            ai_player: Numéro du joueur IA (pour la couleur des scores)
            winning_line: Liste des coordonnées gagnantes (optionnel)
        """
        # ========================================
        # COUCHE 0 : ZONE HEADER (FOND NOIR)
        # ========================================
        
        # Fond noir pour la zone d'en-tête
        header_height = self.cell_size  # Header a la même hauteur qu'une cellule
        pygame.draw.rect(
            self.screen,
            BLACK,
            (self.grid_start_x, self.grid_start_y, self.cell_size * COLS, header_height)
        )
        
        # ========================================
        # COUCHE 1 : PLATEAU + PIONS (DÉCALÉ)
        # ========================================
        
        # Récupération des couleurs personnalisées
        grid_color = self.settings_manager.get_color("grid")
        player1_color = self.settings_manager.get_color("player1")
        player2_color = self.settings_manager.get_color("player2")
        empty_color = self.settings_manager.get_color("empty_slot")
        
        # Grand rectangle BLEU pour le plateau (décalé vers le bas)
        pygame.draw.rect(
            self.screen,
            grid_color,
            (self.grid_start_x, self.grid_start_y + header_height, self.cell_size * COLS, self.cell_size * ROWS)
        )
        
        # Dessin des cercles (pions et cases vides)
        for row in range(board.rows):
            for col in range(board.cols):
                # Position centrale X (pas d'inversion)
                center_x = int(self.grid_start_x + col * self.cell_size + self.cell_size / 2)
                
                # Position centrale Y - INVERSION OBLIGATOIRE + DÉCALAGE HEADER
                # row=0 -> Y grand (bas du plateau, juste au-dessus du bord inférieur)
                # row=rows-1 -> Y petit (haut du plateau, juste en dessous du header)
                center_y = int(self.grid_start_y + header_height + (board.rows * self.cell_size) - (row * self.cell_size + self.cell_size / 2))
                
                # Récupération de la valeur de la case
                cell_value = board.grid[row][col]
                
                # Choix de la couleur selon la valeur
                if cell_value == EMPTY:
                    color = empty_color  # Case vide
                elif cell_value == PLAYER1:
                    color = player1_color  # Joueur 1
                elif cell_value == PLAYER2:
                    color = player2_color  # Joueur 2
                else:
                    color = empty_color  # Sécurité
                
                # Dessin du cercle
                pygame.draw.circle(self.screen, color, (center_x, center_y), self.cell_radius)
        
        # ========================================
        # COUCHE 2 : PION FANTÔME (OPTIONNEL)
        # ========================================
        
        if mouse_x is not None:
            # Calcul de la colonne survolée (relatif à la grille)
            col = (mouse_x - self.grid_start_x) // self.cell_size
            
            # Vérification que la colonne est dans les limites ET valide
            if 0 <= col < board.cols and board.is_valid_location(col):
                # Couleur du pion selon le joueur actuel
                ghost_color = player1_color if current_player == PLAYER1 else player2_color
                
                # Position centrale du pion fantôme au-dessus de la colonne
                # Placé juste au-dessus du plateau (dans la partie basse du header)
                center_x = int(self.grid_start_x + col * self.cell_size + self.cell_size / 2)
                center_y = int(self.grid_start_y + header_height / 2)
                
                # Dessin du pion fantôme dans le header
                pygame.draw.circle(self.screen, ghost_color, (center_x, center_y), self.cell_radius)
        
        # ========================================
        # COUCHE 3 : UI FIXE (TOUJOURS EN DERNIER)
        # ========================================
        
        # Dessin de l'interface utilisateur (bouton Annuler dans le header)
        # IMPORTANT : Toujours appeler à la fin pour dessiner par-dessus tout le reste
        self.draw_ui()
        
        # ========================================
        # COUCHE 4 : SCORES IA (SI FOURNIS)
        # ========================================
        
        # Affichage des scores IA si fournis (pour visualisation avant le coup)
        if ai_scores is not None and ai_scores:
            self.draw_ai_analysis(ai_scores, board, ai_player)
        
        # ========================================
        # COUCHE 5 : LIGNE GAGNANTE (SI FOURNIE)
        # ========================================
        
        # Mise en valeur des pions gagnants avec contour doré
        if winning_line and len(winning_line) > 0:
            self.draw_winning_highlight(winning_line, board)
    
    def draw_ui(self) -> None:
        """
        Dessine les éléments d'interface utilisateur dans la zone header.
        
        Zone header : De y=0 à y=HEADER_HEIGHT
        Contient :
        - Bouton "ANNULER" en haut à gauche
        - Bouton "SAUVER" au centre-gauche
        - Bouton "CHARGER" au centre
        - Bouton "RECOMMENCER" au centre-droit
        - Bouton "MENU" à droite
        
        Les rectangles des boutons sont stockés dans self.*_button_rect
        pour la détection des clics par le contrôleur.
        
        IMPORTANT : Les coordonnées sont STATIQUES (jamais liées à la souris)
        pour garantir que les boutons restent fixes.
        """
        # Dimensions des boutons (tous identiques)
        button_width = 110  # Taille réduite pour 5 boutons
        button_height = 40
        button_spacing = 10  # Espacement entre les boutons
        button_y = 10  # 10px de marge en haut (dans le header)
        
        # Police pour les boutons
        button_font = pygame.font.SysFont("monospace", 16)
        
        # ========================================
        # BOUTON 1 : ANNULER
        # ========================================
        button_x1 = 10
        undo_rect = pygame.Rect(button_x1, button_y, button_width, button_height)
        
        # Dessin du fond (gris)
        pygame.draw.rect(self.screen, (100, 100, 100), undo_rect)
        pygame.draw.rect(self.screen, WHITE, undo_rect, 3)
        
        # Texte
        text_surface = button_font.render("ANNULER", True, WHITE)
        text_rect = text_surface.get_rect(center=undo_rect.center)
        self.screen.blit(text_surface, text_rect)
        
        self.undo_button_rect = undo_rect
        
        # ========================================
        # BOUTON 2 : SAUVER
        # ========================================
        button_x2 = button_x1 + button_width + button_spacing
        save_rect = pygame.Rect(button_x2, button_y, button_width, button_height)
        
        # Dessin du fond (vert foncé)
        pygame.draw.rect(self.screen, (50, 120, 50), save_rect)
        pygame.draw.rect(self.screen, WHITE, save_rect, 3)
        
        # Texte
        text_surface = button_font.render("SAUVER", True, WHITE)
        text_rect = text_surface.get_rect(center=save_rect.center)
        self.screen.blit(text_surface, text_rect)
        
        self.save_button_rect = save_rect
        
        # ========================================
        # BOUTON 3 : CHARGER
        # ========================================
        button_x3 = button_x2 + button_width + button_spacing
        load_rect = pygame.Rect(button_x3, button_y, button_width, button_height)
        
        # Dessin du fond (bleu foncé)
        pygame.draw.rect(self.screen, (50, 80, 150), load_rect)
        pygame.draw.rect(self.screen, WHITE, load_rect, 3)
        
        # Texte
        text_surface = button_font.render("CHARGER", True, WHITE)
        text_rect = text_surface.get_rect(center=load_rect.center)
        self.screen.blit(text_surface, text_rect)
        
        self.load_button_rect = load_rect
        
        # ========================================
        # BOUTON 4 : RECOMMENCER
        # ========================================
        button_x4 = button_x3 + button_width + button_spacing
        restart_rect = pygame.Rect(button_x4, button_y, button_width, button_height)
        
        # Dessin du fond (orange)
        pygame.draw.rect(self.screen, (200, 100, 0), restart_rect)
        pygame.draw.rect(self.screen, WHITE, restart_rect, 3)
        
        # Texte
        text_surface = button_font.render("RECOMMENCER", True, WHITE)
        text_rect = text_surface.get_rect(center=restart_rect.center)
        self.screen.blit(text_surface, text_rect)
        
        self.restart_button_rect = restart_rect
        
        # ========================================
        # BOUTON 5 : MENU (RETOUR)
        # ========================================
        button_x5 = button_x4 + button_width + button_spacing
        menu_rect = pygame.Rect(button_x5, button_y, button_width, button_height)
        
        # Dessin du fond (rouge foncé pour indiquer sortie)
        pygame.draw.rect(self.screen, (150, 50, 50), menu_rect)
        pygame.draw.rect(self.screen, WHITE, menu_rect, 3)
        
        # Texte
        text_surface = button_font.render("MENU", True, WHITE)
        text_rect = text_surface.get_rect(center=menu_rect.center)
        self.screen.blit(text_surface, text_rect)
        
        self.menu_button_rect = menu_rect
    
    def draw_game_info(self, game_id: int, move_count: int) -> None:
        """
        Affiche les informations de la partie en cours dans le header (côté droit).
        
        Affiche :
        - L'ID de la partie actuelle (ex: "Partie #42")
        - Le nombre de coups joués (ex: "Coups : 15")
        
        Args:
            game_id: Identifiant unique de la partie
            move_count: Nombre de coups joués dans la partie
        """
        # Police pour les infos
        info_font = pygame.font.SysFont("monospace", 18, bold=True)
        
        # Texte pour l'ID de partie
        id_text = f"Partie #{game_id}"
        id_label = info_font.render(id_text, True, WHITE)
        
        # Texte pour le nombre de coups
        moves_text = f"Coups: {move_count}"
        moves_label = info_font.render(moves_text, True, YELLOW)
        
        # Positionnement à droite dans le header
        # ID en haut à droite
        id_x = self.width - id_label.get_width() - 15
        id_y = 10
        self.screen.blit(id_label, (id_x, id_y))
        
        # Nombre de coups juste en dessous
        moves_x = self.width - moves_label.get_width() - 15
        moves_y = 35
        self.screen.blit(moves_label, (moves_x, moves_y))
    
    def draw_preview_piece(self, col: Optional[int], player: int) -> None:
        """
        Dessine un pion "fantôme" dans la zone de prévisualisation.
        
        Affiche un aperçu du pion au-dessus de la colonne survolée par la souris.
        
        Args:
            col: Index de la colonne survolée (None si aucune)
            player: Joueur actuel (PLAYER1 ou PLAYER2)
        """
        if col is None:
            return
        
        # Effacement de la zone de prévisualisation
        header_height = self.cell_size
        pygame.draw.rect(
            self.screen,
            BLACK,
            (self.grid_start_x, self.grid_start_y, self.cell_size * COLS, header_height)
        )
        
        # Couleur du pion selon le joueur
        color = RED if player == PLAYER1 else YELLOW
        
        # Position centrale (relative à la grille)
        center_x = int(self.grid_start_x + col * self.cell_size + self.cell_size / 2)
        center_y = int(self.grid_start_y + header_height / 2)
        
        # Dessin du pion fantôme
        pygame.draw.circle(self.screen, color, (center_x, center_y), self.cell_radius)
    
    def draw_winning_positions(self, winning_positions: list[tuple[int, int]], board: Optional[Board] = None) -> None:
        """
        Met en surbrillance les pions formant l'alignement gagnant.
        
        Mission 1.1 Bonus : Dessine un contour vert épais autour des 4 pions gagnants.
        
        Args:
            winning_positions: Liste des coordonnées (row, col) des pions gagnants
            board: Instance du plateau (utilisé pour récupérer les dimensions)
        """
        if not winning_positions:
            return
        
        # Si board n'est pas fourni, utiliser ROWS par défaut (compatibilité arrière)
        rows = board.rows if board else ROWS
        header_height = self.cell_size
        
        for row, col in winning_positions:
            # Calcul des coordonnées avec correction de l'axe Y + décalage header (relatif à la grille)
            center_x = int(self.grid_start_x + col * self.cell_size + self.cell_size / 2)
            center_y = int(self.grid_start_y + header_height + (rows * self.cell_size) - (row * self.cell_size + self.cell_size / 2))
            
            # Dessin d'un cercle vert épais autour du pion
            pygame.draw.circle(
                self.screen,
                GREEN,
                (center_x, center_y),
                self.cell_radius + 5,
                8  # Épaisseur du contour
            )
    
    def draw_winner_message(self, winner: Optional[int]) -> None:
        """
        Affiche le message de fin de partie dans la zone de prévisualisation.
        
        Args:
            winner: PLAYER1, PLAYER2 si victoire, None si égalité
        """
        # Effacement de la zone de prévisualisation
        header_height = self.cell_size
        pygame.draw.rect(
            self.screen,
            BLACK,
            (self.grid_start_x, self.grid_start_y, self.cell_size * COLS, header_height)
        )
        
        # Création du message
        if winner == PLAYER1:
            text = "ROUGE GAGNE!"
            color = RED
        elif winner == PLAYER2:
            text = "JAUNE GAGNE!"
            color = YELLOW
        else:
            text = "EGALITE!"
            color = WHITE
        
        # Rendu du texte
        label = self.font.render(text, True, color)
        
        # Centrage du texte dans la zone de header
        grid_center_x = self.grid_start_x + (self.cell_size * COLS) // 2
        text_rect = label.get_rect(center=(grid_center_x, self.grid_start_y + header_height // 2))
        
        self.screen.blit(label, text_rect)
    
    def draw_instructions(self) -> None:
        """
        Affiche les instructions du jeu en bas de l'écran (optionnel).
        
        Peut être utilisé pour aider les nouveaux joueurs.
        """
        instruction_text = "Cliquez pour jouer"
        label = self.small_font.render(instruction_text, True, WHITE)
        
        # Position en bas de l'écran
        self.screen.blit(label, (10, self.height - 35))
    
    def show_game_over(self, winner_id: Optional[int]) -> None:
        """
        Affiche un message de fin de partie en grand au centre de l'écran.
        
        Crée un overlay semi-transparent avec le message de victoire ou d'égalité,
        avec une couleur adaptée au résultat.
        
        Args:
            winner_id: PLAYER1, PLAYER2 si victoire, None si égalité
        """
        # Création d'un overlay semi-transparent
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(180)  # Transparence
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Création du texte principal selon le résultat
        if winner_id == PLAYER1:
            main_text = "JOUEUR ROUGE"
            sub_text = "A GAGNE !"
            text_color = RED
        elif winner_id == PLAYER2:
            main_text = "JOUEUR JAUNE"
            sub_text = "A GAGNE !"
            text_color = YELLOW
        else:
            main_text = "MATCH NUL"
            sub_text = "Plateau rempli"
            text_color = WHITE
        
        # Police pour le message principal (très grande)
        big_font = pygame.font.SysFont("monospace", 60, bold=True)
        medium_font = pygame.font.SysFont("monospace", 45, bold=True)
        
        # Rendu du texte principal
        main_label = big_font.render(main_text, True, text_color)
        main_rect = main_label.get_rect(center=(self.width // 2, self.height // 2 - 40))
        
        # Rendu du sous-texte
        sub_label = medium_font.render(sub_text, True, text_color)
        sub_rect = sub_label.get_rect(center=(self.width // 2, self.height // 2 + 30))
        
        # Affichage des textes
        self.screen.blit(main_label, main_rect)
        self.screen.blit(sub_label, sub_rect)
    
    def draw_game_over_instructions(self) -> None:
        """
        Affiche les instructions pour les actions disponibles après la fin de partie.
        
        Affiche en bas de l'écran :
        - ECHAP pour retourner au menu
        - R pour recommencer une partie
        """
        # Police pour les instructions
        instruction_font = pygame.font.SysFont("monospace", 28, bold=True)
        
        # Textes d'instructions
        esc_text = "ECHAP : Retour au menu"
        restart_text = "R : Recommencer"
        
        # Rendu des textes
        esc_label = instruction_font.render(esc_text, True, WHITE)
        restart_label = instruction_font.render(restart_text, True, WHITE)
        
        # Positionnement en bas de l'écran (centré)
        y_position = self.height // 2 + 100
        
        esc_rect = esc_label.get_rect(center=(self.width // 2, y_position))
        restart_rect = restart_label.get_rect(center=(self.width // 2, y_position + 40))
        
        # Affichage
        self.screen.blit(esc_label, esc_rect)
        self.screen.blit(restart_label, restart_rect)
    
    def get_column_from_mouse_pos(self, x_pos: int) -> Optional[int]:
        """
        Convertit une position X de souris en index de colonne.
        
        Méthode utilitaire pour traduire les coordonnées écran en logique de jeu.
        Prend en compte la position décalée de la grille.
        
        Args:
            x_pos: Position X de la souris en pixels
            
        Returns:
            Index de la colonne (0 à COLS-1), ou None si hors limites
        """
        # Calcul relatif à la position de la grille
        col = (x_pos - self.grid_start_x) // self.cell_size
        
        if 0 <= col < COLS:
            return col
        
        return None
    
    def draw_menu(self) -> tuple[pygame.Rect, pygame.Rect, pygame.Rect, pygame.Rect, pygame.Rect, pygame.Rect, pygame.Rect]:
        """
        Affiche le menu principal avec les options de jeu.
        
        Dessine un écran de menu avec :
        - Titre "PUISSANCE 4" en haut
        - Bouton "Joueur vs Joueur"
        - Bouton "Joueur vs IA"
        - Bouton "MODE DÉMO (IA vs IA)"
        - Bouton "Historique"
        - Bouton "PARAMÈTRES"
        - Bouton "IMPORTER (.txt)"
        - Bouton "QUITTER"
        
        Returns:
            Tuple contenant (pvp, pvai, demo, history, settings, import, quit) pour la détection des clics
        """
        # Fond bleu foncé
        self.screen.fill((20, 40, 80))
        
        # === TITRE ===
        title_font = pygame.font.SysFont("monospace", 70, bold=True)
        title_text = "PUISSANCE 4"
        title_label = title_font.render(title_text, True, YELLOW)
        title_rect = title_label.get_rect(center=(self.width // 2, 100))
        self.screen.blit(title_label, title_rect)
        
        # Sous-titre
        subtitle_font = pygame.font.SysFont("monospace", 30)
        subtitle_text = "Connect Four"
        subtitle_label = subtitle_font.render(subtitle_text, True, WHITE)
        subtitle_rect = subtitle_label.get_rect(center=(self.width // 2, 160))
        self.screen.blit(subtitle_label, subtitle_rect)
        
        # === BOUTONS ===
        button_font = pygame.font.SysFont("monospace", 30, bold=True)
        button_width = 500
        button_height = 55
        button_spacing = 20
        
        # Position du premier bouton (plus haut pour que tous soient visibles)
        start_y = 220
        
        # Bouton 1 : Joueur vs Joueur
        pvp_rect = pygame.Rect(
            self.width // 2 - button_width // 2,
            start_y,
            button_width,
            button_height
        )
        pygame.draw.rect(self.screen, RED, pvp_rect)
        pygame.draw.rect(self.screen, WHITE, pvp_rect, 3)  # Contour blanc
        
        pvp_text = "Joueur vs Joueur"
        pvp_label = button_font.render(pvp_text, True, WHITE)
        pvp_text_rect = pvp_label.get_rect(center=pvp_rect.center)
        self.screen.blit(pvp_label, pvp_text_rect)
        
        # Bouton 2 : Joueur vs IA
        pvai_rect = pygame.Rect(
            self.width // 2 - button_width // 2,
            start_y + button_height + button_spacing,
            button_width,
            button_height
        )
        pygame.draw.rect(self.screen, YELLOW, pvai_rect)
        pygame.draw.rect(self.screen, WHITE, pvai_rect, 3)  # Contour blanc
        
        pvai_text = "Joueur vs IA"
        pvai_label = button_font.render(pvai_text, True, BLACK)
        pvai_text_rect = pvai_label.get_rect(center=pvai_rect.center)
        self.screen.blit(pvai_label, pvai_text_rect)
        
        # Bouton 3 : MODE DÉMO (IA vs IA)
        demo_rect = pygame.Rect(
            self.width // 2 - button_width // 2,
            start_y + (button_height + button_spacing) * 2,
            button_width,
            button_height
        )
        pygame.draw.rect(self.screen, (50, 200, 50), demo_rect)  # Vert
        pygame.draw.rect(self.screen, WHITE, demo_rect, 3)  # Contour blanc
        
        demo_text = "MODE DEMO (IA vs IA)"
        demo_label = button_font.render(demo_text, True, WHITE)
        demo_text_rect = demo_label.get_rect(center=demo_rect.center)
        self.screen.blit(demo_label, demo_text_rect)
        
        # Bouton 4 : Historique
        history_rect = pygame.Rect(
            self.width // 2 - button_width // 2,
            start_y + (button_height + button_spacing) * 3,
            button_width,
            button_height
        )
        pygame.draw.rect(self.screen, (150, 100, 200), history_rect)  # Violet
        pygame.draw.rect(self.screen, WHITE, history_rect, 3)  # Contour blanc
        
        history_text = "Historique"
        history_label = button_font.render(history_text, True, WHITE)
        history_text_rect = history_label.get_rect(center=history_rect.center)
        self.screen.blit(history_label, history_text_rect)
        
        # Bouton 5 : PARAMÈTRES
        settings_rect = pygame.Rect(
            self.width // 2 - button_width // 2,
            start_y + (button_height + button_spacing) * 4,
            button_width,
            button_height
        )
        pygame.draw.rect(self.screen, (100, 100, 100), settings_rect)  # Gris
        pygame.draw.rect(self.screen, WHITE, settings_rect, 3)  # Contour blanc
        
        settings_text = "PARAMETRES"
        settings_label = button_font.render(settings_text, True, WHITE)
        settings_text_rect = settings_label.get_rect(center=settings_rect.center)
        self.screen.blit(settings_label, settings_text_rect)
        
        # Bouton 6 : IMPORTER (.txt)
        import_rect = pygame.Rect(
            self.width // 2 - button_width // 2,
            start_y + (button_height + button_spacing) * 5,
            button_width,
            button_height
        )
        pygame.draw.rect(self.screen, (50, 150, 200), import_rect)  # Bleu
        pygame.draw.rect(self.screen, WHITE, import_rect, 3)  # Contour blanc
        
        import_text = "IMPORTER (.txt)"
        import_label = button_font.render(import_text, True, WHITE)
        import_text_rect = import_label.get_rect(center=import_rect.center)
        self.screen.blit(import_label, import_text_rect)
        
        # Bouton 7 : QUITTER
        quit_rect = pygame.Rect(
            self.width // 2 - button_width // 2,
            start_y + (button_height + button_spacing) * 6,
            button_width,
            button_height
        )
        pygame.draw.rect(self.screen, (200, 50, 50), quit_rect)  # Rouge
        pygame.draw.rect(self.screen, WHITE, quit_rect, 3)  # Contour blanc
        
        quit_text = "QUITTER"
        quit_label = button_font.render(quit_text, True, WHITE)
        quit_text_rect = quit_label.get_rect(center=quit_rect.center)
        self.screen.blit(quit_label, quit_text_rect)
        
        # Instructions en bas
        info_font = pygame.font.SysFont("monospace", 20)
        info_text = "Cliquez sur un mode pour commencer"
        info_label = info_font.render(info_text, True, WHITE)
        info_rect = info_label.get_rect(center=(self.width // 2, self.height - 50))
        self.screen.blit(info_label, info_rect)
        
        return pvp_rect, pvai_rect, demo_rect, history_rect, settings_rect, import_rect, quit_rect
    
    def draw_status_message(self, message: str, msg_type: str = "info") -> None:
        """
        Affiche un message de statut semi-transparent au centre de l'écran.
        
        Utilisé pour afficher des notifications temporaires (importation, sauvegarde, etc.)
        
        Args:
            message: Le texte du message à afficher
            msg_type: Type de message - "info", "success", "error", "warning"
        """
        # Couleurs selon le type
        colors = {
            "info": (50, 150, 200),      # Bleu
            "success": (50, 180, 50),    # Vert
            "error": (200, 50, 50),      # Rouge
            "warning": (220, 180, 50)    # Jaune/Orange
        }
        
        bg_color = colors.get(msg_type, colors["info"])
        
        # Police pour le message
        msg_font = pygame.font.SysFont("monospace", 32, bold=True)
        
        # Découpage du message en lignes si trop long (word wrapping simple)
        max_width = self.width - 200
        words = message.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            test_surface = msg_font.render(test_line, True, WHITE)
            if test_surface.get_width() <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Calcul de la taille de la boîte
        line_height = 45
        box_height = len(lines) * line_height + 40
        box_width = max_width + 100
        
        # Position centrée
        box_x = (self.width - box_width) // 2
        box_y = (self.height - box_height) // 2
        
        # Surface semi-transparente
        overlay = pygame.Surface((box_width, box_height))
        overlay.set_alpha(220)  # Légère transparence
        overlay.fill(bg_color)
        
        # Dessiner l'overlay
        self.screen.blit(overlay, (box_x, box_y))
        
        # Contour blanc
        pygame.draw.rect(self.screen, WHITE, (box_x, box_y, box_width, box_height), 4)
        
        # Affichage du texte ligne par ligne
        for i, line in enumerate(lines):
            text_surface = msg_font.render(line, True, WHITE)
            text_rect = text_surface.get_rect(
                center=(self.width // 2, box_y + 20 + i * line_height + line_height // 2)
            )
            self.screen.blit(text_surface, text_rect)
    
    def draw_settings(self, config: dict) -> dict[str, pygame.Rect]:
        """
        Affiche l'écran de paramètres/configuration du jeu.
        
        Permet de modifier :
        - Le nombre de lignes (4-10)
        - Le nombre de colonnes (4-12)
        - Le joueur qui commence (Rouge ou Jaune)
        
        Args:
            config: Dictionnaire contenant rows, cols, start_player
            
        Returns:
            Dictionnaire de rectangles pour la détection des clics
        """
        # Fond bleu foncé
        self.screen.fill((20, 40, 80))
        
        # Titre
        title_font = pygame.font.SysFont("monospace", 60, bold=True)
        title_text = "PARAMETRES"
        title_label = title_font.render(title_text, True, YELLOW)
        title_rect = title_label.get_rect(center=(self.width // 2, 80))
        self.screen.blit(title_label, title_rect)
        
        # Polices
        label_font = pygame.font.SysFont("monospace", 35)
        value_font = pygame.font.SysFont("monospace", 40, bold=True)
        button_font = pygame.font.SysFont("monospace", 45, bold=True)
        
        # Dimensions des boutons
        button_size = 50
        spacing_y = 80
        start_y = 180
        
        rects = {}
        
        # OPTION 1 : LIGNES
        y_pos = start_y
        
        label_text = "Lignes :"
        label_surface = label_font.render(label_text, True, WHITE)
        label_rect = label_surface.get_rect(midleft=(50, y_pos))
        self.screen.blit(label_surface, label_rect)
        
        minus_rect = pygame.Rect(self.width // 2 - 120, y_pos - button_size // 2, button_size, button_size)
        pygame.draw.rect(self.screen, RED, minus_rect)
        pygame.draw.rect(self.screen, WHITE, minus_rect, 2)
        minus_text = button_font.render("-", True, WHITE)
        minus_text_rect = minus_text.get_rect(center=minus_rect.center)
        self.screen.blit(minus_text, minus_text_rect)
        rects['rows_minus'] = minus_rect
        
        value_text = str(config['rows'])
        value_surface = value_font.render(value_text, True, YELLOW)
        value_rect = value_surface.get_rect(center=(self.width // 2, y_pos))
        self.screen.blit(value_surface, value_rect)
        
        plus_rect = pygame.Rect(self.width // 2 + 70, y_pos - button_size // 2, button_size, button_size)
        pygame.draw.rect(self.screen, GREEN, plus_rect)
        pygame.draw.rect(self.screen, WHITE, plus_rect, 2)
        plus_text = button_font.render("+", True, WHITE)
        plus_text_rect = plus_text.get_rect(center=plus_rect.center)
        self.screen.blit(plus_text, plus_text_rect)
        rects['rows_plus'] = plus_rect
        
        # OPTION 2 : COLONNES
        y_pos = start_y + spacing_y
        
        label_text = "Colonnes :"
        label_surface = label_font.render(label_text, True, WHITE)
        label_rect = label_surface.get_rect(midleft=(50, y_pos))
        self.screen.blit(label_surface, label_rect)
        
        minus_rect = pygame.Rect(self.width // 2 - 120, y_pos - button_size // 2, button_size, button_size)
        pygame.draw.rect(self.screen, RED, minus_rect)
        pygame.draw.rect(self.screen, WHITE, minus_rect, 2)
        minus_text = button_font.render("-", True, WHITE)
        minus_text_rect = minus_text.get_rect(center=minus_rect.center)
        self.screen.blit(minus_text, minus_text_rect)
        rects['cols_minus'] = minus_rect
        
        value_text = str(config['cols'])
        value_surface = value_font.render(value_text, True, YELLOW)
        value_rect = value_surface.get_rect(center=(self.width // 2, y_pos))
        self.screen.blit(value_surface, value_rect)
        
        plus_rect = pygame.Rect(self.width // 2 + 70, y_pos - button_size // 2, button_size, button_size)
        pygame.draw.rect(self.screen, GREEN, plus_rect)
        pygame.draw.rect(self.screen, WHITE, plus_rect, 2)
        plus_text = button_font.render("+", True, WHITE)
        plus_text_rect = plus_text.get_rect(center=plus_rect.center)
        self.screen.blit(plus_text, plus_text_rect)
        rects['cols_plus'] = plus_rect
        
        # OPTION 3 : JOUEUR QUI COMMENCE
        y_pos = start_y + spacing_y * 2
        
        label_text = "Commence :"
        label_surface = label_font.render(label_text, True, WHITE)
        label_rect = label_surface.get_rect(midleft=(50, y_pos))
        self.screen.blit(label_surface, label_rect)
        
        player_text = "Rouge" if config['start_player'] == 1 else "Jaune"
        player_color = RED if config['start_player'] == 1 else YELLOW
        text_color = WHITE if config['start_player'] == 1 else BLACK
        
        toggle_rect = pygame.Rect(self.width // 2 - 80, y_pos - 30, 160, 60)
        pygame.draw.rect(self.screen, player_color, toggle_rect)
        pygame.draw.rect(self.screen, WHITE, toggle_rect, 3)
        
        player_surface = value_font.render(player_text, True, text_color)
        player_text_rect = player_surface.get_rect(center=toggle_rect.center)
        self.screen.blit(player_surface, player_text_rect)
        rects['player_toggle'] = toggle_rect
        
        # BOUTON RETOUR
        button_width = 300
        button_height = 60
        back_rect = pygame.Rect(
            self.width // 2 - button_width // 2,
            self.height - 100,
            button_width,
            button_height
        )
        pygame.draw.rect(self.screen, (100, 100, 100), back_rect)
        pygame.draw.rect(self.screen, WHITE, back_rect, 3)
        
        back_text = "RETOUR"
        back_surface = label_font.render(back_text, True, WHITE)
        back_text_rect = back_surface.get_rect(center=back_rect.center)
        self.screen.blit(back_surface, back_text_rect)
        rects['back'] = back_rect
        
        settings_button_width = 400
        settings_button_height = 70
        settings_rect = pygame.Rect(
            self.width // 2 - settings_button_width // 2,
            0,
            settings_button_width,
            settings_button_height
        )
        rects['settings'] = settings_rect
        
        return rects
    
    def draw_ai_analysis(self, column_scores: dict[int, float], board: Board, ai_player: int = 2) -> None:
        """
        Affiche les scores calculés par l'IA au-dessus de chaque colonne.
        
        Permet de visualiser la "pensée" de l'IA en montrant l'évaluation
        de chaque colonne après l'analyse Minimax.
        
        Args:
            column_scores: Dictionnaire {colonne: score}
            board: Instance du plateau pour obtenir les dimensions
            ai_player: Numéro du joueur IA (1=Rouge, 2=Jaune) pour la couleur d'affichage
        """
        if not column_scores:
            return
        
        # Police pour les scores (plus grande pour être visible dans le header)
        score_font = pygame.font.SysFont("monospace", 20, bold=True)
        
        # Couleur selon le joueur IA
        score_color = RED if ai_player == 1 else YELLOW
        
        # Affichage au-dessus de chaque colonne dans le header
        header_height = self.cell_size
        for col, score in column_scores.items():
            # Position X centrée sur la colonne (relatif à la grille)
            center_x = int(self.grid_start_x + col * self.cell_size + self.cell_size / 2)
            # Position Y dans le header (légèrement en dessous du haut)
            y_pos = self.grid_start_y + header_height - 35
            
            # Formatage du score
            score_text = f"{int(score)}"
            
            # Rendu du texte avec la couleur du joueur IA
            text_surface = score_font.render(score_text, True, score_color)
            text_rect = text_surface.get_rect(center=(center_x, y_pos))
            self.screen.blit(text_surface, text_rect)
    
    def draw_depth_selector(self, current_depth: int) -> dict:
        """
        Affiche le sélecteur de profondeur dans le header.
        
        Permet de modifier dynamiquement la profondeur de recherche de l'IA.
        Affiche "Profondeur: [ - ] {depth} [ + ]" dans le coin supérieur droit.
        
        Args:
            current_depth: Profondeur actuelle de l'IA
            
        Returns:
            Dictionnaire contenant les Rects des boutons 'minus' et 'plus'
        """
        # Police
        font = pygame.font.SysFont("monospace", 20, bold=True)
        button_font = pygame.font.SysFont("monospace", 24, bold=True)
        
        # Position dans le coin supérieur droit
        right_margin = 20
        y_pos = 15
        
        # Texte "Profondeur:"
        label_text = font.render("Profondeur:", True, WHITE)
        label_rect = label_text.get_rect()
        label_rect.topright = (self.width - right_margin - 200, y_pos)
        self.screen.blit(label_text, label_rect)
        
        # Bouton [ - ]
        button_size = 30
        minus_x = self.width - right_margin - 160
        minus_rect = pygame.Rect(minus_x, y_pos, button_size, button_size)
        pygame.draw.rect(self.screen, (80, 80, 80), minus_rect)
        pygame.draw.rect(self.screen, WHITE, minus_rect, 2)
        minus_text = button_font.render("-", True, WHITE)
        minus_text_rect = minus_text.get_rect(center=minus_rect.center)
        self.screen.blit(minus_text, minus_text_rect)
        
        # Valeur de profondeur
        depth_text = font.render(str(current_depth), True, YELLOW)
        depth_rect = depth_text.get_rect()
        depth_rect.center = (minus_x + button_size + 25, y_pos + button_size // 2)
        self.screen.blit(depth_text, depth_rect)
        
        # Bouton [ + ]
        plus_x = minus_x + button_size + 50
        plus_rect = pygame.Rect(plus_x, y_pos, button_size, button_size)
        pygame.draw.rect(self.screen, (80, 80, 80), plus_rect)
        pygame.draw.rect(self.screen, WHITE, plus_rect, 2)
        plus_text = button_font.render("+", True, WHITE)
        plus_text_rect = plus_text.get_rect(center=plus_rect.center)
        self.screen.blit(plus_text, plus_text_rect)
        
        return {
            'minus': minus_rect,
            'plus': plus_rect
        }
    
    def draw_thinking_bar(self, progress: float = 0, message: str = "IA reflechit...") -> None:
        """
        Affiche une barre de progression et un message dans le header.
        
        Utilisé pendant que l'IA calcule son coup pour donner un retour visuel
        à l'utilisateur.
        
        Args:
            progress: Pourcentage de progression (0-100)
            message: Message à afficher
        """
        # Zone de la barre de progression (dans le header)
        bar_width = 300
        bar_height = 30
        bar_x = (self.width - bar_width) // 2
        bar_y = HEADER_HEIGHT // 2 - bar_height // 2
        
        # Fond de la barre (gris foncé)
        pygame.draw.rect(self.screen, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height))
        
        # Barre de progression (bleu)
        if progress > 0:
            fill_width = int((bar_width - 4) * (progress / 100))
            pygame.draw.rect(self.screen, (50, 150, 255), (bar_x + 2, bar_y + 2, fill_width, bar_height - 4))
        
        # Contour blanc
        pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Message
        message_font = pygame.font.SysFont("monospace", 22, bold=True)
        text_surface = message_font.render(message, True, YELLOW)
        text_rect = text_surface.get_rect(center=(self.width // 2, bar_y - 20))
        self.screen.blit(text_surface, text_rect)
    
    def update_display(self) -> None:
        """
        Rafraîchit l'affichage à l'écran.
        
        Doit être appelé après chaque modification graphique pour rendre visible
        les changements effectués.
        """
        pygame.display.update()
    
    def draw_winning_highlight(self, winning_line: list[tuple[int, int]], board: Board) -> None:
        """
        Met en valeur les pions gagnants avec un contour doré animé.
        
        IMPORTANT : Les coordonnées doivent être au format Base 0 (index Python).
        Format attendu : [(row, col), ...] où row ∈ [0, 7] et col ∈ [0, 8]
        
        Args:
            winning_line: Liste des coordonnées (row, col) des pions gagnants en Base 0
            board: Instance du plateau pour calculer les positions
        """
        if not winning_line:
            return
        
        # Couleur dorée avec effet de brillance
        GOLD = (255, 215, 0)
        WHITE = (255, 255, 255)
        header_height = self.cell_size
        
        for coord in winning_line:
            # Vérification du format
            if not isinstance(coord, (list, tuple)) or len(coord) != 2:
                print(f"[VIEW WARNING] Format de coordonnée invalide: {coord}")
                continue
            
            row, col = coord[0], coord[1]
            
            # SÉCURITÉ : Vérification des limites (grille 8x9, Base 0)
            if not (0 <= row < board.rows and 0 <= col < board.cols):
                print(f"[VIEW WARNING] Coordonnée hors limites ignorée: ({row}, {col}) pour grille {board.rows}x{board.cols}")
                continue
            
            # Calcul de la position centrale du pion (relatif à la grille centrée)
            # col = position X (horizontal)
            # row = position Y (vertical, avec inversion car row=0 est en BAS)
            center_x = int(self.grid_start_x + col * self.cell_size + self.cell_size / 2)
            center_y = int(self.grid_start_y + header_height + (board.rows * self.cell_size) - (row * self.cell_size + self.cell_size / 2))
            
            # Dessin de plusieurs cercles concentriques pour effet de brillance
            pygame.draw.circle(self.screen, GOLD, (center_x, center_y), self.cell_radius + 8, 6)
            pygame.draw.circle(self.screen, WHITE, (center_x, center_y), self.cell_radius + 4, 3)
    
    def draw_victory_overlay(self, winner: Optional[int], winning_line: list[tuple[int, int]]) -> None:
        """
        Affiche un overlay élégant avec le résultat de la partie.
        
        Args:
            winner: Numéro du joueur gagnant (1 ou 2), ou None en cas d'égalité
            winning_line: Liste des coordonnées gagnantes
        """
        # Surface semi-transparente pour l'overlay
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(180)  # Transparence
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Rectangle central pour le message
        box_width = 500
        box_height = 250
        box_x = (self.width - box_width) // 2
        box_y = (self.height - box_height) // 2 - 50
        
        # Fond du rectangle (avec bordure)
        box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
        pygame.draw.rect(self.screen, (30, 30, 30), box_rect)
        pygame.draw.rect(self.screen, (255, 215, 0), box_rect, 5)
        
        # Texte principal
        title_font = pygame.font.SysFont("monospace", 48, bold=True)
        subtitle_font = pygame.font.SysFont("monospace", 24)
        
        if winner is not None:
            # Message de victoire
            player_name = "ROUGE" if winner == 1 else "JAUNE"
            player_color = RED if winner == 1 else YELLOW
            
            title_text = f"VICTOIRE !"
            subtitle_text = f"Joueur {player_name}"
            
            title_surface = title_font.render(title_text, True, player_color)
            subtitle_surface = subtitle_font.render(subtitle_text, True, WHITE)
        else:
            # Message d'égalité
            title_text = "MATCH NUL"
            title_surface = title_font.render(title_text, True, WHITE)
            subtitle_surface = subtitle_font.render("Plateau rempli", True, (150, 150, 150))
        
        # Centrage du texte principal
        title_rect = title_surface.get_rect(center=(self.width // 2, box_y + 70))
        subtitle_rect = subtitle_surface.get_rect(center=(self.width // 2, box_y + 130))
        
        self.screen.blit(title_surface, title_rect)
        self.screen.blit(subtitle_surface, subtitle_rect)
        
        # Instructions
        instructions_font = pygame.font.SysFont("monospace", 20)
        
        restart_text = "[R] Recommencer"
        menu_text = "[ECHAP] Menu Principal"
        
        restart_surface = instructions_font.render(restart_text, True, GREEN)
        menu_surface = instructions_font.render(menu_text, True, (150, 150, 255))
        
        restart_rect = restart_surface.get_rect(center=(self.width // 2 - 120, box_y + 190))
        menu_rect = menu_surface.get_rect(center=(self.width // 2 + 120, box_y + 190))
        
        self.screen.blit(restart_surface, restart_rect)
        self.screen.blit(menu_surface, menu_rect)
    
    def wait(self, milliseconds: int) -> None:
        """
        Pause l'exécution pendant un nombre de millisecondes.
        
        Args:
            milliseconds: Durée de la pause en ms
        """
        pygame.time.wait(milliseconds)
    
    def draw_history_menu(self, games: list) -> dict:
        """
        Affiche l'écran d'historique avec la liste des parties enregistrées.
        
        Args:
            games: Liste des parties récupérées depuis la base de données
            
        Returns:
            Dictionnaire des rectangles cliquables {index: rect, 'back': rect}
        """
        # Fond noir
        self.screen.fill(BLACK)
        
        # Titre
        title_font = pygame.font.SysFont("monospace", 42, bold=True)
        title_text = title_font.render("HISTORIQUE DES PARTIES", True, (255, 215, 0))
        title_rect = title_text.get_rect(center=(self.width // 2, 40))
        self.screen.blit(title_text, title_rect)
        
        # Sous-titre avec nombre de parties
        subtitle_font = pygame.font.SysFont("monospace", 20)
        subtitle_text = subtitle_font.render(f"{len(games)} partie(s) enregistrée(s)", True, WHITE)
        subtitle_rect = subtitle_text.get_rect(center=(self.width // 2, 85))
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # Liste des parties (scrollable)
        game_font = pygame.font.SysFont("monospace", 16)
        start_y = 130
        item_height = 60
        rects = {}
        
        for i, game in enumerate(games[:10]):  # Limiter à 10 parties visibles
            y = start_y + i * item_height
            
            # Rectangle de sélection
            rect = pygame.Rect(50, y, self.width - 100, item_height - 10)
            pygame.draw.rect(self.screen, (40, 40, 40), rect)
            pygame.draw.rect(self.screen, (100, 100, 255), rect, 2)
            
            # Informations de la partie
            text_x = 70
            
            # Ligne 1: ID et Date
            id_text = game_font.render(f"ID: {game['id']} - {game['created_at']}", True, (200, 200, 200))
            self.screen.blit(id_text, (text_x, y + 5))
            
            # Ligne 2: Coups et Mode
            coups_display = game['coups'][:20] + "..." if len(game['coups']) > 20 else game['coups']
            info_text = game_font.render(f"Coups: {coups_display} | Mode: {game['mode_jeu']}", True, WHITE)
            self.screen.blit(info_text, (text_x, y + 25))
            
            rects[i] = rect
        
        # Bouton RETOUR
        back_button = pygame.Rect(self.width // 2 - 100, self.height - 80, 200, 50)
        pygame.draw.rect(self.screen, (100, 50, 50), back_button)
        pygame.draw.rect(self.screen, WHITE, back_button, 3)
        
        back_text = pygame.font.SysFont("monospace", 22, bold=True).render("RETOUR", True, WHITE)
        back_text_rect = back_text.get_rect(center=back_button.center)
        self.screen.blit(back_text, back_text_rect)
        
        rects['back'] = back_button
        
        return rects
    
    def draw_replay_interface(self, board: Board, current_move: int, total_moves: int, 
                             game_info: dict, has_prev: bool, has_next: bool, 
                             show_symmetric: bool = False) -> dict:
        """
        Affiche l'interface de replay avec contrôles de navigation.
        
        Args:
            board: Plateau de jeu actuel
            current_move: Numéro du coup actuel (0-indexed)
            total_moves: Nombre total de coups
            game_info: Informations sur la partie (ID, coups, mode, etc.)
            has_prev: True si une partie précédente existe (id_antecedent)
            has_next: True si une partie suivante existe (id_suivant)
            show_symmetric: True pour afficher la version symétrique
            
        Returns:
            Dictionnaire des rectangles cliquables
        """
        # Affichage du plateau dans la zone de jeu
        self.draw_board(board)
        
        # Panneau latéral droit (zone NAV_RECT)
        panel_x = self.nav_rect.x
        panel_y = self.nav_rect.y + 10
        panel_width = self.nav_rect.width - 20
        panel_height = self.nav_rect.height - 20
        
        # Fond opaque du panneau
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(self.screen, (30, 30, 30), panel_rect)
        pygame.draw.rect(self.screen, (255, 215, 0), panel_rect, 3)
        
        # Taille de police adaptative
        title_size = max(14, min(20, panel_width // 15))
        info_size = max(10, min(14, panel_width // 20))
        
        # Titre du panneau
        title_font = pygame.font.SysFont("monospace", title_size, bold=True)
        mode_text = "MODE MIROIR" if show_symmetric else "MODE REPLAY"
        title_surface = title_font.render(mode_text, True, (255, 215, 0))
        title_rect = title_surface.get_rect(centerx=panel_x + panel_width // 2, y=panel_y + 10)
        self.screen.blit(title_surface, title_rect)
        
        # Informations de la partie
        info_font = pygame.font.SysFont("monospace", info_size)
        info_y = panel_y + 50
        
        infos = [
            f"ID: {game_info['id']}",
            f"Mode: {game_info['mode_jeu']}",
            f"Coups: {current_move}/{total_moves}",
            "",
            "NAVIGATION:",
            "[←] Précédent",
            "[→] Suivant",
            "[Espace] Auto",
            "[M] Symétrie",
            "[Echap] Retour"
        ]
        
        line_height = max(18, info_size + 4)
        for i, line in enumerate(infos):
            color = (255, 215, 0) if line == "NAVIGATION:" else WHITE
            text = info_font.render(line, True, color)
            self.screen.blit(text, (panel_x + 10, info_y + i * line_height))
        
        # Boutons de navigation entre parties
        button_y = panel_y + panel_height - 200
        button_width = (panel_width - 30) // 2
        button_height = max(35, min(50, panel_height // 12))
        button_spacing = 10
        
        rects = {}
        
        # Bouton PRÉCÉDENT
        prev_button = pygame.Rect(panel_x + 10, button_y, button_width, button_height)
        prev_color = (50, 100, 50) if has_prev else (50, 50, 50)
        pygame.draw.rect(self.screen, prev_color, prev_button)
        pygame.draw.rect(self.screen, WHITE, prev_button, 2)
        
        prev_label = "← PRÉC" if panel_width < 200 else "← PRÉCÉDENT"
        prev_text = info_font.render(prev_label, True, WHITE if has_prev else (100, 100, 100))
        prev_text_rect = prev_text.get_rect(center=prev_button.center)
        self.screen.blit(prev_text, prev_text_rect)
        
        rects['prev'] = prev_button if has_prev else None
        
        # Bouton SUIVANT
        next_button = pygame.Rect(panel_x + button_width + 20, button_y, button_width, button_height)
        next_color = (50, 100, 50) if has_next else (50, 50, 50)
        pygame.draw.rect(self.screen, next_color, next_button)
        pygame.draw.rect(self.screen, WHITE, next_button, 2)
        
        next_label = "SUIV →" if panel_width < 200 else "SUIVANT →"
        next_text = info_font.render(next_label, True, WHITE if has_next else (100, 100, 100))
        next_text_rect = next_text.get_rect(center=next_button.center)
        self.screen.blit(next_text, next_text_rect)
        
        rects['next'] = next_button if has_next else None
        
        # Bouton SYMÉTRIE
        sym_button = pygame.Rect(panel_x + 10, button_y + button_height + button_spacing, 
                                panel_width - 20, button_height)
        sym_color = (100, 50, 150) if show_symmetric else (50, 50, 100)
        pygame.draw.rect(self.screen, sym_color, sym_button)
        pygame.draw.rect(self.screen, WHITE, sym_button, 2)
        
        sym_label = "⇄ SYM" if panel_width < 200 else "⇄ VOIR SYMÉTRIE"
        sym_text = info_font.render(sym_label, True, WHITE)
        sym_text_rect = sym_text.get_rect(center=sym_button.center)
        self.screen.blit(sym_text, sym_text_rect)
        
        rects['symmetric'] = sym_button
        
        # Bouton RETOUR
        back_button = pygame.Rect(panel_x + 10, button_y + 2 * (button_height + button_spacing), 
                                 panel_width - 20, button_height)
        pygame.draw.rect(self.screen, (100, 50, 50), back_button)
        pygame.draw.rect(self.screen, WHITE, back_button, 2)
        
        back_label = "RETOUR" if panel_width < 200 else "RETOUR MENU"
        back_text = info_font.render(back_label, True, WHITE)
        back_text_rect = back_text.get_rect(center=back_button.center)
        self.screen.blit(back_text, back_text_rect)
        
        rects['back'] = back_button
        
        return rects
    
    def draw_settings_menu(self, settings_manager) -> dict[str, any]:
        """
        Affiche l'écran de paramètres avec options de personnalisation.
        
        Args:
            settings_manager: Instance de SettingsManager pour récupérer les valeurs actuelles
            
        Returns:
            Dictionnaire contenant les rectangles cliquables et les sliders
        """
        # Fond bleu foncé
        self.screen.fill((20, 40, 80))
        
        # Titre
        title_font = pygame.font.SysFont("monospace", 60, bold=True)
        title_text = "PARAMETRES"
        title_label = title_font.render(title_text, True, YELLOW)
        title_rect = title_label.get_rect(center=(self.width // 2, 80))
        self.screen.blit(title_label, title_rect)
        
        # Police pour les labels
        label_font = pygame.font.SysFont("monospace", 24, bold=True)
        value_font = pygame.font.SysFont("monospace", 22)
        
        # Dictionnaire pour stocker les rectangles et sliders
        rects = {}
        
        start_y = 180
        section_spacing = 80
        
        # === SECTION COULEURS ===
        section_title_font = pygame.font.SysFont("monospace", 30, bold=True)
        colors_title = section_title_font.render("COULEURS", True, WHITE)
        self.screen.blit(colors_title, (80, start_y))
        
        current_y = start_y + 50
        
        # Liste des couleurs configurables
        color_options = [
            ("player1", "Joueur 1 (Rouge)", 200),
            ("player2", "Joueur 2 (Jaune)", 200),
            ("grid", "Grille", 200)
        ]
        
        for color_key, color_label, label_x in color_options:
            # Label
            label = label_font.render(color_label, True, WHITE)
            self.screen.blit(label, (label_x, current_y))
            
            # Couleur actuelle
            current_color = settings_manager.get_color(color_key)
            
            # Carrés de couleur avec sliders RGB
            color_preview_x = label_x + 320
            color_preview = pygame.Rect(color_preview_x, current_y - 5, 50, 40)
            pygame.draw.rect(self.screen, current_color, color_preview)
            pygame.draw.rect(self.screen, WHITE, color_preview, 2)
            
            # Valeurs RGB à côté
            rgb_text = value_font.render(f"R:{current_color[0]} G:{current_color[1]} B:{current_color[2]}", 
                                        True, WHITE)
            self.screen.blit(rgb_text, (color_preview_x + 60, current_y + 5))
            
            # Stocker les infos pour les sliders
            rects[f"{color_key}_preview"] = color_preview
            rects[f"{color_key}_current"] = current_color
            
            current_y += 50
        
        # === SECTION VOLUME ===
        current_y += section_spacing
        volume_title = section_title_font.render("VOLUME", True, WHITE)
        self.screen.blit(volume_title, (80, current_y))
        
        current_y += 50
        
        # Volume principal
        volume_label = label_font.render("Volume principal", True, WHITE)
        self.screen.blit(volume_label, (200, current_y))
        
        volume_value = settings_manager.get_setting("volume", "master") or 50
        
        # Slider simple (barre + curseur)
        slider_x = 400
        slider_y = current_y + 5
        slider_width = 200
        slider_height = 20
        
        slider_bg = pygame.Rect(slider_x, slider_y, slider_width, slider_height)
        pygame.draw.rect(self.screen, (100, 100, 100), slider_bg)
        pygame.draw.rect(self.screen, WHITE, slider_bg, 2)
        
        # Remplissage selon la valeur
        fill_width = int((volume_value / 100) * slider_width)
        if fill_width > 0:
            fill_rect = pygame.Rect(slider_x, slider_y, fill_width, slider_height)
            pygame.draw.rect(self.screen, (0, 200, 0), fill_rect)
        
        # Valeur affichée
        vol_text = value_font.render(f"{volume_value}%", True, WHITE)
        self.screen.blit(vol_text, (slider_x + slider_width + 20, current_y + 5))
        
        rects['volume_slider'] = slider_bg
        rects['volume_value'] = volume_value
        
        # === SECTION BASE DE DONNÉES ===
        current_y += section_spacing + 30
        db_title = section_title_font.render("BASE DE DONNEES", True, WHITE)
        self.screen.blit(db_title, (80, current_y))
        
        current_y += 50
        
        # Bouton Réinitialiser BDD
        reset_button = pygame.Rect(200, current_y, 400, 50)
        pygame.draw.rect(self.screen, (150, 30, 30), reset_button)
        pygame.draw.rect(self.screen, WHITE, reset_button, 3)
        
        reset_text = label_font.render("VIDER L'HISTORIQUE", True, WHITE)
        reset_text_rect = reset_text.get_rect(center=reset_button.center)
        self.screen.blit(reset_text, reset_text_rect)
        
        rects['reset_db'] = reset_button
        
        # === BOUTON RETOUR ===
        current_y += 80  # Espacement après le bouton BDD
        back_button = pygame.Rect(self.width // 2 - 150, current_y, 300, 60)
        pygame.draw.rect(self.screen, (100, 100, 100), back_button)
        pygame.draw.rect(self.screen, WHITE, back_button, 3)
        
        back_text = section_title_font.render("RETOUR", True, WHITE)
        back_text_rect = back_text.get_rect(center=back_button.center)
        self.screen.blit(back_text, back_text_rect)
        
        rects['back'] = back_button
        
        return rects
    
    def draw_confirmation_dialog(self, message: str) -> tuple[pygame.Rect, pygame.Rect]:
        """
        Affiche une boîte de dialogue de confirmation avec Oui/Non.
        
        Args:
            message: Message de confirmation à afficher
            
        Returns:
            Tuple (yes_button_rect, no_button_rect)
        """
        # Overlay semi-transparent sur tout l'écran
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Boîte de dialogue
        dialog_width = 600
        dialog_height = 300
        dialog_x = (self.width - dialog_width) // 2
        dialog_y = (self.height - dialog_height) // 2
        
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        pygame.draw.rect(self.screen, (40, 60, 100), dialog_rect)
        pygame.draw.rect(self.screen, YELLOW, dialog_rect, 4)
        
        # Message
        msg_font = pygame.font.SysFont("monospace", 26, bold=True)
        
        # Word wrapping simple
        words = message.split()
        lines = []
        current_line = []
        max_width = dialog_width - 60
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            test_surface = msg_font.render(test_line, True, WHITE)
            if test_surface.get_width() <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Affichage du message
        line_y = dialog_y + 60
        for line in lines:
            line_surface = msg_font.render(line, True, WHITE)
            line_rect = line_surface.get_rect(center=(self.width // 2, line_y))
            self.screen.blit(line_surface, line_rect)
            line_y += 40
        
        # Boutons OUI et NON
        button_width = 150
        button_height = 60
        button_y = dialog_y + dialog_height - 90
        
        # Bouton OUI (vert)
        yes_button = pygame.Rect(dialog_x + 80, button_y, button_width, button_height)
        pygame.draw.rect(self.screen, (50, 180, 50), yes_button)
        pygame.draw.rect(self.screen, WHITE, yes_button, 3)
        
        yes_font = pygame.font.SysFont("monospace", 32, bold=True)
        yes_text = yes_font.render("OUI", True, WHITE)
        yes_text_rect = yes_text.get_rect(center=yes_button.center)
        self.screen.blit(yes_text, yes_text_rect)
        
        # Bouton NON (rouge)
        no_button = pygame.Rect(dialog_x + dialog_width - 80 - button_width, button_y, 
                               button_width, button_height)
        pygame.draw.rect(self.screen, (180, 50, 50), no_button)
        pygame.draw.rect(self.screen, WHITE, no_button, 3)
        
        no_text = yes_font.render("NON", True, WHITE)
        no_text_rect = no_text.get_rect(center=no_button.center)
        self.screen.blit(no_text, no_text_rect)
        
        return yes_button, no_button
    
    def draw_color_picker(self, color_key: str, current_color: tuple, position: tuple) -> dict:
        """
        Affiche un sélecteur de couleur RGB simple avec sliders.
        
        Args:
            color_key: Clé de la couleur (player1, player2, grid)
            current_color: Couleur RGB actuelle
            position: Position (x, y) du sélecteur
            
        Returns:
            Dictionnaire avec les rectangles des sliders RGB
        """
        x, y = position
        rects = {}
        
        slider_font = pygame.font.SysFont("monospace", 20)
        slider_width = 200
        slider_height = 20
        spacing = 40
        
        rgb_labels = ["R", "G", "B"]
        rgb_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
        
        for i, (label, color, value) in enumerate(zip(rgb_labels, rgb_colors, current_color)):
            slider_y = y + i * spacing
            
            # Label
            label_text = slider_font.render(f"{label}:", True, WHITE)
            self.screen.blit(label_text, (x, slider_y))
            
            # Slider
            slider_x = x + 30
            slider_rect = pygame.Rect(slider_x, slider_y, slider_width, slider_height)
            pygame.draw.rect(self.screen, (80, 80, 80), slider_rect)
            pygame.draw.rect(self.screen, WHITE, slider_rect, 1)
            
            # Remplissage
            fill_width = int((value / 255) * slider_width)
            if fill_width > 0:
                fill_rect = pygame.Rect(slider_x, slider_y, fill_width, slider_height)
                pygame.draw.rect(self.screen, color, fill_rect)
            
            # Valeur
            value_text = slider_font.render(str(value), True, WHITE)
            self.screen.blit(value_text, (slider_x + slider_width + 10, slider_y))
            
            rects[f"{color_key}_{label.lower()}_slider"] = slider_rect
        
        return rects
    
    def wait(self, milliseconds: int) -> None:
        """
        Pause l'exécution pendant un nombre de millisecondes.
        
        Args:
            milliseconds: Durée de la pause en ms
        """
        pygame.time.wait(milliseconds)
    
    def quit(self) -> None:
        """
        Ferme proprement la fenêtre Pygame.
        """
        pygame.quit()
