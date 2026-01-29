"""
Module implémentant l'IA Minimax avec élagage Alpha-Beta.
Fournit une IA compétitive pour le jeu Puissance 4.
"""

import random
from typing import Optional, Tuple
from copy import deepcopy

from ..models.board import Board
from ..utils.constants import EMPTY, PLAYER1, PLAYER2, WIN_LENGTH


class MinimaxAI:
    """
    Intelligence Artificielle basée sur l'algorithme Minimax avec élagage Alpha-Beta.
    
    L'algorithme explore l'arbre des coups possibles jusqu'à une certaine profondeur
    et choisit le coup optimal en supposant que l'adversaire joue aussi de manière optimale.
    L'élagage Alpha-Beta permet de réduire le nombre de branches explorées.
    
    Attributes:
        depth: Profondeur maximale de recherche dans l'arbre (plus c'est haut, plus c'est fort mais lent)
        name: Nom de l'IA pour l'affichage
        piece: Numéro du joueur que l'IA contrôle (PLAYER1 ou PLAYER2)
        opponent_piece: Numéro du joueur adverse
        last_scores: Dictionnaire stockant les scores de chaque colonne lors de la dernière recherche
    """
    
    def __init__(self, depth: int = 4, name: str = "Minimax AI") -> None:
        """
        Initialise l'IA Minimax.
        
        Args:
            depth: Profondeur de recherche (recommandé: 4-6). Plus élevé = plus fort mais plus lent
            name: Nom de l'IA pour l'affichage
        """
        self.depth: int = depth
        self.name: str = name
        self.piece: int = PLAYER2  # Par défaut, l'IA est le joueur 2
        self.opponent_piece: int = PLAYER1
        self.last_scores: dict[int, float] = {}  # Scores de chaque colonne (pour debug/affichage)
        
        print(f"[MINIMAX AI] Initialisée - Profondeur: {depth}, Nom: {name}")
    
    def set_player(self, piece: int) -> None:
        """
        Configure quel joueur l'IA contrôle.
        
        Args:
            piece: PLAYER1 ou PLAYER2
        """
        self.piece = piece
        self.opponent_piece = PLAYER1 if piece == PLAYER2 else PLAYER2
        print(f"[MINIMAX AI] Configuration : IA = Joueur {self.piece}, Adversaire = Joueur {self.opponent_piece}")
    
    def evaluate_window(self, window: list[int], piece: int) -> int:
        """
        Évalue une fenêtre de 4 cases et retourne un score.
        
        Cette fonction attribue des points en fonction de la composition de la fenêtre :
        - 4 pions alignés : victoire (+100)
        - 3 pions + 1 vide : très bon (+5)
        - 2 pions + 2 vides : prometteur (+2)
        - 3 pions adverses + 1 vide : danger, il faut bloquer (-4)
        
        Args:
            window: Liste de 4 valeurs (EMPTY, PLAYER1, ou PLAYER2)
            piece: Le joueur pour lequel on évalue (self.piece)
            
        Returns:
            Score de la fenêtre (positif = bon pour 'piece', négatif = bon pour l'adversaire)
        """
        score = 0
        opponent = self.opponent_piece
        
        # Comptage des pions dans la fenêtre
        piece_count = window.count(piece)
        empty_count = window.count(EMPTY)
        opponent_count = window.count(opponent)
        
        # Évaluation selon la composition
        if piece_count == 4:
            score += 100  # Victoire !
        elif piece_count == 3 and empty_count == 1:
            score += 5    # Presque gagné, très prometteur
        elif piece_count == 2 and empty_count == 2:
            score += 2    # Début d'alignement
        
        # Pénalité si l'adversaire est menaçant
        if opponent_count == 3 and empty_count == 1:
            score -= 4    # L'adversaire peut gagner au prochain coup, c'est critique !
        
        return score
    
    def score_position(self, board: Board, piece: int) -> int:
        """
        Évalue l'état global du plateau pour un joueur donné.
        
        Parcourt toutes les fenêtres possibles de 4 cases (horizontales, verticales, diagonales)
        et somme leurs scores. Ajoute également un bonus pour les pions au centre du plateau.
        
        Args:
            board: Instance du plateau à évaluer
            piece: Le joueur pour lequel on évalue
            
        Returns:
            Score total du plateau (plus élevé = meilleur pour 'piece')
        """
        score = 0
        rows = board.rows
        cols = board.cols
        
        # === BONUS CENTRE ===
        # Les pions au centre offrent plus de possibilités d'alignements
        center_col = cols // 2
        center_array = [int(board.grid[row][center_col]) for row in range(rows)]
        center_count = center_array.count(piece)
        score += center_count * 3  # Bonus de 3 points par pion au centre
        
        # === ÉVALUATION HORIZONTALE ===
        # Parcourt chaque ligne et crée des fenêtres de 4 cases
        for row in range(rows):
            row_array = [int(board.grid[row][col]) for col in range(cols)]
            for col in range(cols - 3):
                window = row_array[col:col + WIN_LENGTH]
                score += self.evaluate_window(window, piece)
        
        # === ÉVALUATION VERTICALE ===
        # Parcourt chaque colonne et crée des fenêtres de 4 cases
        for col in range(cols):
            col_array = [int(board.grid[row][col]) for row in range(rows)]
            for row in range(rows - 3):
                window = col_array[row:row + WIN_LENGTH]
                score += self.evaluate_window(window, piece)
        
        # === ÉVALUATION DIAGONALE ASCENDANTE (/) ===
        # Diagonales qui montent de gauche à droite
        for row in range(rows - 3):
            for col in range(cols - 3):
                window = [board.grid[row + i][col + i] for i in range(WIN_LENGTH)]
                score += self.evaluate_window(window, piece)
        
        # === ÉVALUATION DIAGONALE DESCENDANTE (\) ===
        # Diagonales qui descendent de gauche à droite
        for row in range(3, rows):
            for col in range(cols - 3):
                window = [board.grid[row - i][col + i] for i in range(WIN_LENGTH)]
                score += self.evaluate_window(window, piece)
        
        return score
    
    def is_terminal_node(self, board: Board) -> bool:
        """
        Vérifie si un nœud est terminal (fin de partie ou plateau plein).
        
        Args:
            board: Plateau à vérifier
            
        Returns:
            True si la partie est terminée ou le plateau est plein
        """
        return (board.check_win(self.piece) or 
                board.check_win(self.opponent_piece) or 
                board.is_full())
    
    def minimax(
        self, 
        board: Board, 
        depth: int, 
        alpha: float, 
        beta: float, 
        maximizing_player: bool
    ) -> Tuple[Optional[int], float]:
        """
        Algorithme Minimax avec élagage Alpha-Beta.
        
        Explore récursivement l'arbre des coups possibles jusqu'à une profondeur donnée
        et retourne le meilleur coup à jouer. L'élagage Alpha-Beta permet d'éviter
        d'explorer des branches qui ne peuvent pas améliorer le résultat.
        
        Args:
            board: État actuel du plateau
            depth: Profondeur restante à explorer
            alpha: Meilleur score garanti pour le joueur MAX (élagage)
            beta: Meilleur score garanti pour le joueur MIN (élagage)
            maximizing_player: True si c'est le tour de l'IA (MAX), False pour l'adversaire (MIN)
            
        Returns:
            Tuple (colonne, score) où :
            - colonne: Index de la meilleure colonne à jouer (None si nœud terminal)
            - score: Score évalué pour cette position
        """
        # Récupération des coups valides
        valid_locations = board.get_valid_locations()
        is_terminal = self.is_terminal_node(board)
        
        # === CAS DE BASE : Profondeur 0 ou fin de partie ===
        if depth == 0 or is_terminal:
            if is_terminal:
                # Fin de partie détectée
                if board.check_win(self.piece):
                    return (None, 100000)  # Victoire de l'IA : score maximal
                elif board.check_win(self.opponent_piece):
                    return (None, -100000)  # Victoire de l'adversaire : score minimal
                else:
                    return (None, 0)  # Match nul
            else:
                # Profondeur maximale atteinte : évaluation heuristique
                return (None, self.score_position(board, self.piece))
        
        # === CAS RÉCURSIF : Joueur MAX (IA) ===
        if maximizing_player:
            value = float('-inf')
            # Sélection aléatoire d'une colonne valide par défaut
            column = random.choice(valid_locations)
            
            for col in valid_locations:
                # Simulation du coup
                row = board.get_next_open_row(col)
                if row is None:
                    continue
                
                # Copie du plateau pour simulation
                temp_board = board.copy()
                temp_board.drop_piece(row, col, self.piece)
                
                # Appel récursif pour l'adversaire (MIN)
                new_score = self.minimax(temp_board, depth - 1, alpha, beta, False)[1]
                
                # Mise à jour du meilleur score
                if new_score > value:
                    value = new_score
                    column = col
                
                # Mise à jour d'alpha et élagage
                alpha = max(alpha, value)
                if alpha >= beta:
                    break  # Élagage Beta : l'adversaire ne choisira jamais cette branche
            
            return column, value
        
        # === CAS RÉCURSIF : Joueur MIN (Adversaire) ===
        else:
            value = float('inf')
            column = random.choice(valid_locations)
            
            for col in valid_locations:
                # Simulation du coup
                row = board.get_next_open_row(col)
                if row is None:
                    continue
                
                # Copie du plateau pour simulation
                temp_board = board.copy()
                temp_board.drop_piece(row, col, self.opponent_piece)
                
                # Appel récursif pour l'IA (MAX)
                new_score = self.minimax(temp_board, depth - 1, alpha, beta, True)[1]
                
                # Mise à jour du pire score (du point de vue de l'IA)
                if new_score < value:
                    value = new_score
                    column = col
                
                # Mise à jour de beta et élagage
                beta = min(beta, value)
                if alpha >= beta:
                    break  # Élagage Alpha : l'IA ne choisira jamais cette branche
            
            return column, value
    
    def get_move(self, board: Board) -> Optional[int]:
        """
        Méthode publique pour obtenir le coup de l'IA.
        
        Lance l'algorithme Minimax avec la profondeur configurée et retourne
        l'index de la colonne où l'IA souhaite jouer.
        
        Args:
            board: État actuel du plateau
            
        Returns:
            Index de la colonne choisie (0-indexed), ou None si aucun coup possible
        """
        print(f"\n[MINIMAX AI] Réflexion en cours (profondeur {self.depth})...")
        
        # Réinitialisation des scores
        self.last_scores = {}
        
        # Obtention des coups valides
        valid_locations = board.get_valid_locations()
        
        if not valid_locations:
            print("[MINIMAX AI] ❌ Aucun coup valide disponible")
            return None
        
        # === DÉTECTION VICTOIRE IMMÉDIATE ===
        # Si l'IA peut gagner en un coup, jouer immédiatement sans calcul
        for col in valid_locations:
            row = board.get_next_open_row(col)
            if row is not None:
                temp_board = board.copy()
                temp_board.drop_piece(row, col, self.piece)
                if temp_board.check_win(self.piece):
                    print(f"[MINIMAX AI] 🎯 Coup gagnant détecté : colonne {col}")
                    return col
        
        # === DÉTECTION BLOCAGE IMMÉDIAT ===
        # Si l'adversaire peut gagner au prochain coup, bloquer
        for col in valid_locations:
            row = board.get_next_open_row(col)
            if row is not None:
                temp_board = board.copy()
                temp_board.drop_piece(row, col, self.opponent_piece)
                if temp_board.check_win(self.opponent_piece):
                    print(f"[MINIMAX AI] 🛡️ Blocage nécessaire : colonne {col}")
                    return col
        
        # === CALCUL MINIMAX AVEC ALPHA-BETA ===
        # Calcul des scores pour chaque colonne valide (pour debug/affichage)
        for col in valid_locations:
            row = board.get_next_open_row(col)
            if row is not None:
                temp_board = board.copy()
                temp_board.drop_piece(row, col, self.piece)
                score = self.score_position(temp_board, self.piece)
                self.last_scores[col] = score
        
        # Lancement de l'algorithme Minimax
        column, minimax_score = self.minimax(
            board, 
            self.depth, 
            float('-inf'),  # Alpha initial
            float('inf'),   # Beta initial
            True            # L'IA est le joueur maximisant
        )
        
        print(f"[MINIMAX AI] ✅ Coup choisi : colonne {column} (score: {minimax_score})")
        print(f"[MINIMAX AI] Scores calculés : {self.last_scores}")
        
        return column
    
    def get_last_scores(self) -> dict[int, float]:
        """
        Retourne les scores calculés pour chaque colonne lors de la dernière recherche.
        
        Utile pour l'affichage ou le debug.
        
        Returns:
            Dictionnaire {colonne: score}
        """
        return self.last_scores
