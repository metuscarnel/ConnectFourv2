"""
Constantes globales du jeu Puissance 4.
Définit les dimensions du plateau et les valeurs des joueurs.
"""

# Dimensions du plateau de jeu
ROWS: int = 8  # Nombre de lignes
COLS: int = 9  # Nombre de colonnes

# Valeurs des cellules du plateau
EMPTY: int = 0      # Cellule vide
PLAYER1: int = 1    # Joueur 1 (Rouge)
PLAYER2: int = 2    # Joueur 2 (Jaune)

# Règles du jeu
WIN_LENGTH: int = 4  # Nombre de pions alignés requis pour gagner

# Dimensions graphiques (Pygame)
SQUARESIZE: int = 70  # Taille d'une case en pixels
HEADER_HEIGHT: int = 100  # Hauteur de la zone d'en-tête (pour UI)
WIDTH: int = COLS * SQUARESIZE  # Largeur de la fenêtre
HEIGHT: int = 750  # Hauteur totale optimisée pour l'historique et les menus

# Couleurs (RGB)
BLUE: tuple[int, int, int] = (0, 100, 200)      # Fond du plateau
BLACK: tuple[int, int, int] = (0, 0, 0)         # Arrière-plan
RED: tuple[int, int, int] = (230, 50, 50)       # Joueur 1
YELLOW: tuple[int, int, int] = (255, 220, 50)   # Joueur 2
WHITE: tuple[int, int, int] = (255, 255, 255)   # Cases vides
GREEN: tuple[int, int, int] = (50, 200, 100)    # Surbrillance victoire

# Directions de vérification pour la victoire (dy, dx)
# Utilisées pour parcourir les 4 directions : horizontale, verticale, diagonales
DIRECTIONS: list[tuple[int, int]] = [
    (0, 1),   # Horizontale (droite)
    (1, 0),   # Verticale (bas)
    (1, 1),   # Diagonale descendante (\)
    (1, -1),  # Diagonale montante (/)
]
