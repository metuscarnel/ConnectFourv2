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
    
    def __init__(self) -> None:
        """
        Initialise la fenêtre Pygame avec les dimensions calculées dynamiquement.
        
        La fenêtre comprend :
        - Une ligne en haut pour afficher le pion de prévisualisation
        - Le plateau de jeu (ROWS x COLS)
        """
        pygame.init()
        
        # Utilisation des dimensions depuis constants.py
        self.width: int = WIDTH
        self.height: int = HEIGHT
        self.radius: int = self.RADIUS
        
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
    
    def draw_board(self, board: Board, mouse_x: Optional[int] = None, current_player: int = PLAYER1, ai_scores: Optional[dict] = None, ai_player: int = 2) -> None:
        """
        Dessine le plateau de jeu avec tous les pions actuels en 3 couches distinctes.
        
        Convention stricte : row=0 de la matrice = BAS physique de l'écran.
        
        Architecture en couches :
        - COUCHE 0 : Header (zone réservée pour l'UI en haut)
        - COUCHE 1 : Plateau bleu + pions existants (décalé de HEADER_HEIGHT)
        - COUCHE 2 : Pion fantôme (optionnel, si mouse_x fourni)
        - COUCHE 3 : UI fixe (bouton Annuler dans la zone header)
        - COUCHE 4 : Scores IA (optionnel, si ai_scores fourni)
        
        Args:
            board: Instance du plateau à afficher
            mouse_x: Position X de la souris (optionnel) pour afficher le pion fantôme
            current_player: Joueur actuel (pour la couleur du pion fantôme)
            ai_scores: Scores calculés par l'IA (optionnel) pour affichage avant le coup
            ai_player: Numéro du joueur IA (pour la couleur des scores)
        """
        # ========================================
        # COUCHE 0 : ZONE HEADER (FOND NOIR)
        # ========================================
        
        # Fond noir pour la zone d'en-tête
        pygame.draw.rect(
            self.screen,
            BLACK,
            (0, 0, self.width, HEADER_HEIGHT)
        )
        
        # ========================================
        # COUCHE 1 : PLATEAU + PIONS (DÉCALÉ)
        # ========================================
        
        # Grand rectangle BLEU pour le plateau (décalé vers le bas)
        pygame.draw.rect(
            self.screen,
            BLUE,
            (0, HEADER_HEIGHT, self.width, self.height - HEADER_HEIGHT)
        )
        
        # Dessin des cercles (pions et cases vides)
        for row in range(board.rows):
            for col in range(board.cols):
                # Position centrale X (pas d'inversion)
                center_x = int(col * SQUARESIZE + SQUARESIZE / 2)
                
                # Position centrale Y - INVERSION OBLIGATOIRE + DÉCALAGE HEADER
                # row=0 -> Y grand (bas du plateau, juste au-dessus du bord inférieur)
                # row=rows-1 -> Y petit (haut du plateau, juste en dessous du header)
                # Formule : HEADER_HEIGHT + (rows * SQUARESIZE) - (row * SQUARESIZE + SQUARESIZE/2)
                center_y = int(HEADER_HEIGHT + (board.rows * SQUARESIZE) - (row * SQUARESIZE + SQUARESIZE / 2))
                
                # Récupération de la valeur de la case
                cell_value = board.grid[row][col]
                
                # Choix de la couleur selon la valeur
                if cell_value == EMPTY:
                    color = WHITE  # Case vide = cercle blanc
                elif cell_value == PLAYER1:
                    color = RED    # Joueur 1 = rouge
                elif cell_value == PLAYER2:
                    color = YELLOW # Joueur 2 = jaune
                else:
                    color = WHITE  # Sécurité
                
                # Dessin du cercle
                pygame.draw.circle(self.screen, color, (center_x, center_y), self.radius)
        
        # ========================================
        # COUCHE 2 : PION FANTÔME (OPTIONNEL)
        # ========================================
        
        if mouse_x is not None:
            # Calcul de la colonne survolée
            col = mouse_x // SQUARESIZE
            
            # Vérification que la colonne est dans les limites ET valide
            if 0 <= col < board.cols and board.is_valid_location(col):
                # Couleur du pion selon le joueur actuel
                ghost_color = RED if current_player == PLAYER1 else YELLOW
                
                # Position centrale du pion fantôme au-dessus de la colonne
                # Placé juste au-dessus du plateau (dans la partie basse du header)
                center_x = int(col * SQUARESIZE + SQUARESIZE / 2)
                center_y = int(HEADER_HEIGHT - SQUARESIZE / 2)
                
                # Dessin du pion fantôme dans le header
                pygame.draw.circle(self.screen, ghost_color, (center_x, center_y), self.radius)
        
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
    
    def draw_ui(self) -> None:
        """
        Dessine les éléments d'interface utilisateur dans la zone header.
        
        Zone header : De y=0 à y=HEADER_HEIGHT
        Contient :
        - Bouton "ANNULER" en haut à gauche
        - Bouton "SAUVER" au centre-gauche
        - Bouton "CHARGER" au centre
        - Bouton "RECOMMENCER" au centre-droit
        
        Les rectangles des boutons sont stockés dans self.*_button_rect
        pour la détection des clics par le contrôleur.
        
        IMPORTANT : Les coordonnées sont STATIQUES (jamais liées à la souris)
        pour garantir que les boutons restent fixes.
        """
        # Dimensions des boutons (tous identiques)
        button_width = 110  # Taille réduite pour 4 boutons
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
        pygame.draw.rect(
            self.screen,
            BLACK,
            (0, 0, self.width, SQUARESIZE)
        )
        
        # Couleur du pion selon le joueur
        color = RED if player == PLAYER1 else YELLOW
        
        # Position centrale
        center_x = int(col * SQUARESIZE + SQUARESIZE / 2)
        center_y = int(SQUARESIZE / 2)
        
        # Dessin du pion fantôme
        pygame.draw.circle(self.screen, color, (center_x, center_y), self.radius)
    
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
        
        for row, col in winning_positions:
            # Calcul des coordonnées avec correction de l'axe Y + décalage header
            center_x = int(col * SQUARESIZE + SQUARESIZE / 2)
            center_y = int(HEADER_HEIGHT + (rows * SQUARESIZE) - (row * SQUARESIZE + SQUARESIZE / 2))
            
            # Dessin d'un cercle vert épais autour du pion
            pygame.draw.circle(
                self.screen,
                GREEN,
                (center_x, center_y),
                self.radius + 5,
                8  # Épaisseur du contour
            )
    
    def draw_winner_message(self, winner: Optional[int]) -> None:
        """
        Affiche le message de fin de partie dans la zone de prévisualisation.
        
        Args:
            winner: PLAYER1, PLAYER2 si victoire, None si égalité
        """
        # Effacement de la zone de prévisualisation
        pygame.draw.rect(
            self.screen,
            BLACK,
            (0, 0, self.width, SQUARESIZE)
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
        
        # Centrage du texte
        text_rect = label.get_rect(center=(self.width // 2, SQUARESIZE // 2))
        
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
        
        Args:
            x_pos: Position X de la souris en pixels
            
        Returns:
            Index de la colonne (0 à COLS-1), ou None si hors limites
        """
        col = x_pos // SQUARESIZE
        
        if 0 <= col < COLS:
            return col
        
        return None
    
    def draw_menu(self) -> tuple[pygame.Rect, pygame.Rect, pygame.Rect, pygame.Rect]:
        """
        Affiche le menu principal avec les options de jeu.
        
        Dessine un écran de menu avec :
        - Titre "PUISSANCE 4" en haut
        - Bouton "Joueur vs Joueur"
        - Bouton "Joueur vs IA"
        - Bouton "MODE DÉMO (IA vs IA)"
        - Bouton "Paramètres"
        
        Returns:
            Tuple contenant (rect_pvp, rect_pvai, rect_demo, rect_settings) pour la détection des clics
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
        button_font = pygame.font.SysFont("monospace", 35, bold=True)
        button_width = 500
        button_height = 65
        button_spacing = 25
        
        # Position du premier bouton (centré verticalement)
        start_y = self.height // 2 - 120
        
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
        
        # Bouton 4 : Paramètres
        settings_rect = pygame.Rect(
            self.width // 2 - button_width // 2,
            start_y + (button_height + button_spacing) * 3,
            button_width,
            button_height
        )
        pygame.draw.rect(self.screen, (100, 100, 100), settings_rect)  # Gris
        pygame.draw.rect(self.screen, WHITE, settings_rect, 3)  # Contour blanc
        
        settings_text = "Parametres"
        settings_label = button_font.render(settings_text, True, WHITE)
        settings_text_rect = settings_label.get_rect(center=settings_rect.center)
        self.screen.blit(settings_label, settings_text_rect)
        
        # Instructions en bas
        info_font = pygame.font.SysFont("monospace", 20)
        info_text = "Cliquez sur un mode pour commencer"
        info_label = info_font.render(info_text, True, WHITE)
        info_rect = info_label.get_rect(center=(self.width // 2, self.height - 50))
        self.screen.blit(info_label, info_rect)
        
        return pvp_rect, pvai_rect, demo_rect, settings_rect
    
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
        for col, score in column_scores.items():
            # Position X centrée sur la colonne
            center_x = int(col * SQUARESIZE + SQUARESIZE / 2)
            # Position Y dans le header (légèrement en dessous du haut)
            y_pos = HEADER_HEIGHT - 35
            
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
