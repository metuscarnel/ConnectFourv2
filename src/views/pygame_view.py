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
    SQUARESIZE, WIDTH, HEIGHT,
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
    
    def draw_board(self, board: Board) -> None:
        """
        Dessine le plateau de jeu avec tous les pions actuels.
        
        Convention stricte : row=0 de la matrice = BAS physique de l'écran.
        
        Style graphique :
        - Zone de prévisualisation noire en haut (Y: 0 à SQUARESIZE)
        - Grand rectangle BLEU pour le plateau (Y: SQUARESIZE à HEIGHT)
        - Cercles BLANCS pour cases vides, ROUGES pour joueur 1, JAUNES pour joueur 2
        
        Formule d'inversion Y obligatoire :
        pos_y = HEIGHT - (row * SQUARESIZE + SQUARESIZE / 2)
        
        Args:
            board: Instance du plateau à afficher
        """
        # Fond de la zone de prévisualisation (noir)
        pygame.draw.rect(
            self.screen,
            BLACK,
            (0, 0, self.width, SQUARESIZE)
        )
        
        # Grand rectangle BLEU pour le plateau (masque)
        pygame.draw.rect(
            self.screen,
            BLUE,
            (0, SQUARESIZE, self.width, self.height - SQUARESIZE)
        )
        
        # Dessin des cercles (pions et cases vides)
        for row in range(ROWS):
            for col in range(COLS):
                # Position centrale X (pas d'inversion)
                center_x = int(col * SQUARESIZE + SQUARESIZE / 2)
                
                # Position centrale Y - INVERSION OBLIGATOIRE
                # row=0 -> Y grand (bas de l'écran)
                # row=ROWS-1 -> Y petit (haut du plateau)
                center_y = int(self.height - (row * SQUARESIZE + SQUARESIZE / 2))
                
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
    
    def draw_winning_positions(self, winning_positions: list[tuple[int, int]]) -> None:
        """
        Met en surbrillance les pions formant l'alignement gagnant.
        
        Mission 1.1 Bonus : Dessine un contour vert épais autour des 4 pions gagnants.
        
        Args:
            winning_positions: Liste des coordonnées (row, col) des pions gagnants
        """
        if not winning_positions:
            return
        
        for row, col in winning_positions:
            # Calcul des coordonnées avec correction de l'axe Y
            center_x = int(col * SQUARESIZE + SQUARESIZE / 2)
            center_y = int(self.height - (row * SQUARESIZE + SQUARESIZE / 2))
            
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
        
        # Message de fermeture
        close_text = "Fermeture dans 4 secondes..."
        close_label = self.small_font.render(close_text, True, WHITE)
        close_rect = close_label.get_rect(center=(self.width // 2, self.height // 2 + 100))
        self.screen.blit(close_label, close_rect)
    
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
    
    def draw_menu(self) -> tuple[pygame.Rect, pygame.Rect]:
        """
        Affiche le menu principal avec les options de jeu.
        
        Dessine un écran de menu avec :
        - Titre "PUISSANCE 4" en haut
        - Bouton "Joueur vs Joueur"
        - Bouton "Joueur vs IA"
        
        Returns:
            Tuple contenant (rect_pvp, rect_pvai) pour la détection des clics
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
        button_width = 400
        button_height = 70
        button_spacing = 30
        
        # Position du premier bouton (centré verticalement)
        start_y = self.height // 2 - 50
        
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
        
        # Instructions en bas
        info_font = pygame.font.SysFont("monospace", 20)
        info_text = "Cliquez sur un mode pour commencer"
        info_label = info_font.render(info_text, True, WHITE)
        info_rect = info_label.get_rect(center=(self.width // 2, self.height - 50))
        self.screen.blit(info_label, info_rect)
        
        return pvp_rect, pvai_rect
    
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
