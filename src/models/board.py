"""
Module gérant la logique du plateau de jeu.
Implémente les règles de placement et de détection de victoire.

CONVENTION STRICTE : Row 0 = BAS physique du plateau, Row ROWS-1 = HAUT
"""

from typing import Optional
import numpy as np
from numpy.typing import NDArray

from ..utils.constants import ROWS, COLS, EMPTY, WIN_LENGTH, DIRECTIONS


class Board:
    """
    Représente le plateau de jeu Puissance 4.
    
    CONVENTION : self.grid[0][col] = bas du plateau (fond)
                 self.grid[ROWS-1][col] = haut du plateau (sommet)
    
    Gère la grille de jeu, le placement des pions avec gravité,
    et la détection des conditions de victoire dans toutes les directions.
    
    Attributes:
        grid: Matrice numpy (ROWS x COLS) représentant l'état du plateau
    """
    
    def __init__(self) -> None:
        """
        Initialise un plateau vide de dimensions ROWS x COLS.
        Toutes les cellules sont initialisées à EMPTY (0).
        
        Convention : grid[0] = ligne du bas, grid[ROWS-1] = ligne du haut
        """
        self.grid: NDArray[np.int_] = np.zeros((ROWS, COLS), dtype=np.int_)
        print(f"[BOARD DEBUG] Plateau initialisé : {ROWS} lignes x {COLS} colonnes")
    
    def is_valid_location(self, col: int) -> bool:
        """
        Vérifie si une colonne peut encore accueillir un pion.
        
        LOGIQUE CRITIQUE : 
        - Convention : grid[ROWS-1] = ligne du HAUT
        - Une colonne est valide si la case du HAUT (grid[ROWS-1][col]) est vide (0)
        
        Args:
            col: Index de la colonne à vérifier (0-indexed)
            
        Returns:
            True si un pion peut être placé dans cette colonne, False sinon
        """
        # Vérification des bornes
        if col < 0 or col >= COLS:
            print(f"[BOARD DEBUG] is_valid_location({col}) : FAUX (hors limites)")
            return False
        
        # CORRECTION CRITIQUE : La colonne est valide si le HAUT (ROWS-1) est vide
        is_valid = self.grid[ROWS - 1][col] == EMPTY
        print(f"[BOARD DEBUG] is_valid_location({col}) : {is_valid} (grid[{ROWS-1}][{col}] = {self.grid[ROWS-1][col]})")
        return is_valid
    
    def get_next_open_row(self, col: int) -> Optional[int]:
        """
        Trouve la première ligne vide dans une colonne (simulation de la gravité).
        
        LOGIQUE CRITIQUE :
        - Convention : row=0 = BAS physique (fond), row=ROWS-1 = HAUT
        - Parcourt de row=0 (fond) vers row=ROWS-1 (haut)
        - Retourne le PREMIER r où grid[r][col] == 0 (vide)
        
        Args:
            col: Index de la colonne
            
        Returns:
            L'index de la ligne vide la plus basse, ou None si la colonne est pleine
        """
        print(f"[BOARD DEBUG] get_next_open_row({col}) : recherche case vide...")
        
        # PARCOURS CRUCIAL : De 0 (bas) vers ROWS-1 (haut)
        for row in range(ROWS):
            if self.grid[row][col] == EMPTY:
                print(f"[BOARD DEBUG] -> Trouvé case vide : row={row}")
                return row
        
        print(f"[BOARD DEBUG] -> Colonne {col} PLEINE (aucune case vide)")
        return None
    
    def drop_piece(self, row: int, col: int, piece: int) -> None:
        """
        Place un pion dans la grille à la position spécifiée.
        
        Args:
        # DEBUG : Affichage avant placement
        print(f"\n[BOARD DEBUG] === drop_piece APPELÉ ===")
        print(f"[BOARD DEBUG] Position : row={row}, col={col}, piece={piece}")
        print(f"[BOARD DEBUG] Valeur AVANT placement : grid[{row}][{col}] = {self.grid[row][col]}")
        
        # Placement du pion
        self.grid[row][col] = piece
        
        # DEBUG : Affichage après placement
        print(f"[BOARD DEBUG] Valeur APRÈS placement : grid[{row}][{col}] = {self.grid[row][col]}")
        
        # DEBUG : Affichage de l'état complet de la colonne (de bas en haut)
        column_state = [self.grid[r][col] for r in range(ROWS)]
        print(f"[BOARD DEBUG] État colonne {col} (bas->haut) : {column_state}")
        print(f"[BOARD DEBUG] === drop_piece TERMINÉ ===\n")
            col: Index de la colonne
            piece: Valeur du joueur (PLAYER1 ou PLAYER2)
        """
        self.grid[row][col] = piece
    
    def check_win(self, piece: int) -> bool:
        """
        Vérifie si le joueur spécifié a gagné la partie.
        
        Parcourt toutes les positions possibles et vérifie dans les 4 directions :
        - Horizontale (→)
        - Verticale (↓)
        - Diagonale descendante (\)
        - Diagonale montante (/)
        
        Args:
            piece: Valeur du joueur à vérifier (PLAYER1 ou PLAYER2)
            
        Returns:
            True si le joueur a aligné WIN_LENGTH pions, False sinon
        """
        # Parcours de chaque cellule de la grille
        for row in range(ROWS):
            for col in range(COLS):
                # Si la cellule contient le pion du joueur
                if self.grid[row][col] == piece:
                    # Vérification dans les 4 directions
                    for dy, dx in DIRECTIONS:
                        if self._check_direction(row, col, dy, dx, piece):
                            return True
        
        return False
    
    def _check_direction(
        self, 
        start_row: int, 
        start_col: int, 
        dy: int, 
        dx: int, 
        piece: int
    ) -> bool:
        """
        Vérifie l'alignement de WIN_LENGTH pions dans une direction donnée.
        
        Méthode privée utilisée par check_win pour éviter la duplication de code.
        
        Args:
            start_row: Ligne de départ
            start_col: Colonne de départ
            dy: Déplacement vertical (-1, 0, ou 1)
            dx: Déplacement horizontal (-1, 0, ou 1)
            piece: Valeur du joueur à vérifier
            
        Returns:
            True si WIN_LENGTH pions consécutifs sont trouvés, False sinon
        """
        count = 0
        
        # Vérification des WIN_LENGTH positions consécutives dans la direction
        for i in range(WIN_LENGTH):
            row = start_row + i * dy
            col = start_col + i * dx
            
            # Vérification des limites du plateau
            if row < 0 or row >= ROWS or col < 0 or col >= COLS:
                return False
            
            # Vérification si le pion correspond
            if self.grid[row][col] == piece:
                count += 1
            else:
                return False
        
        return count == WIN_LENGTH
    
    def get_winning_positions(self, piece: int) -> list[tuple[int, int]]:
        """
        Retourne les coordonnées des pions formant l'alignement gagnant.
        
        Mission 1.1 Bonus : Permet de mettre en surbrillance les pions gagnants
        dans l'interface graphique future.
        
        Args:
            piece: Valeur du joueur à vérifier
            
        Returns:
            Liste des coordonnées (row, col) des WIN_LENGTH pions alignés,
            ou liste vide si aucun alignement gagnant n'est trouvé
        """
        # Parcours de chaque cellule de la grille
        for row in range(ROWS):
            for col in range(COLS):
                # Si la cellule contient le pion du joueur
                if self.grid[row][col] == piece:
                    # Vérification dans les 4 directions
                    for dy, dx in DIRECTIONS:
                        positions = self._get_positions_in_direction(
                            row, col, dy, dx, piece
                        )
                        if positions:
                            return positions
        
        return []
    
    def _get_positions_in_direction(
        self,
        start_row: int,
        start_col: int,
        dy: int,
        dx: int,
        piece: int
    ) -> list[tuple[int, int]]:
        """
        Collecte les positions d'un alignement gagnant dans une direction.
        
        Méthode privée utilisée par get_winning_positions.
        
        Args:
            start_row: Ligne de départ
            start_col: Colonne de départ
            dy: Déplacement vertical
            dx: Déplacement horizontal
            piece: Valeur du joueur
            
        Returns:
            Liste des coordonnées si WIN_LENGTH pions sont alignés, liste vide sinon
        """
        positions: list[tuple[int, int]] = []
        
        for i in range(WIN_LENGTH):
            row = start_row + i * dy
            col = start_col + i * dx
            
            # Vérification des limites
            if row < 0 or row >= ROWS or col < 0 or col >= COLS:
                return []
            
            # Vérification du pion
            if self.grid[row][col] == piece:
                positions.append((row, col))
            else:
                return []
        
        return positions if len(positions) == WIN_LENGTH else []
    
    def is_full(self) -> bool:
        """
        Vérifie si le plateau est complètement rempli (cas d'égalité).
        
        Convention : row=0 = BAS, row=ROWS-1 = HAUT.
        Le plateau est plein si la ligne du HAUT (row=ROWS-1) ne contient aucune case vide,
        ou plus sûrement, si AUCUNE case du plateau entier ne contient EMPTY (0).
        
        Returns:
            True si toutes les cases sont remplies, False sinon
        """
        # Méthode robuste : vérifier qu'il n'existe aucun 0 dans toute la grille
        return not (self.grid == EMPTY).any()
    
    def get_valid_locations(self) -> list[int]:
        """
        Retourne la liste des colonnes où un coup peut être joué.
        
        Utile pour l'IA qui doit connaître les coups possibles.
        
        Returns:
            Liste des indices de colonnes valides
        """
        return [col for col in range(COLS) if self.is_valid_location(col)]
    
    def reset(self) -> None:
        """
        Réinitialise le plateau à l'état initial (toutes cellules vides).
        """
        self.grid = np.zeros((ROWS, COLS), dtype=np.int_)
    
    def copy(self) -> 'Board':
        """
        Crée une copie profonde du plateau.
        
        Utile pour l'algorithme Minimax qui doit simuler des coups
        sans modifier le plateau réel.
        
        Returns:
            Nouvelle instance de Board avec l'état identique
        """
        new_board = Board()
        new_board.grid = np.copy(self.grid)
        return new_board
    
    def __str__(self) -> str:
        """
        Représentation textuelle du plateau pour le débogage.
        
        Returns:
            String formaté avec la grille retournée (ligne 0 en bas)
        """
        # Retourner la grille pour affichage intuitif (ligne 0 = bas)
        return str(np.flip(self.grid, axis=0))
