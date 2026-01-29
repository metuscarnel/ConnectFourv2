"""
Module gérant la logique globale du jeu.
Orchestre les tours, les états de partie et les conditions de fin.
"""

from typing import Optional

from .board import Board
from ..utils.constants import PLAYER1, PLAYER2
from ..utils.enums import GameState


class Game:
    """
    Gère l'état global d'une partie de Puissance 4.
    
    Orchestre le déroulement de la partie : initialisation du plateau,
    alternance des tours, détection des conditions de victoire et d'égalité.
    
    Attributes:
        board: Instance du plateau de jeu
        current_player: Joueur dont c'est le tour (PLAYER1 ou PLAYER2)
        state: État actuel de la partie (GameState)
        winner: Joueur gagnant si la partie est terminée, None sinon
        move_history: Historique des coups joués [(col, player), ...]
    """
    
    def __init__(self, rows: int = 6, cols: int = 7, start_player: int = PLAYER1) -> None:
        """
        Initialise une nouvelle partie avec des paramètres configurables.
        
        Args:
            rows: Nombre de lignes du plateau (par défaut 6)
            cols: Nombre de colonnes du plateau (par défaut 7)
            start_player: Joueur qui commence (par défaut PLAYER1)
        """
        self.board: Board = Board(rows=rows, cols=cols)
        self.current_player: int = start_player
        self.state: GameState = GameState.IN_PROGRESS
        self.winner: Optional[int] = None
        self.move_history: list[tuple[int, int]] = []  # Historique (col, player)
    
    def play_turn(self, col: int) -> bool:
        """
        Tente de jouer un coup dans la colonne spécifiée.
        
        Exécute le coup si la colonne est valide, vérifie les conditions de fin,
        et change de joueur si le jeu continue.
        
        Args:
            col: Index de la colonne où jouer (0-indexed)
            
        Returns:
            True si le coup a été joué avec succès, False sinon
            (colonne invalide ou partie terminée)
        """
        # === DEBUG LOG ===
        print(f"\n[DEBUG] play_turn appelé : col={col}, joueur={self.current_player}")
        
        # Vérification : la partie doit être en cours
        if self.state != GameState.IN_PROGRESS:
            print(f"[DEBUG] Partie déjà terminée (état={self.state.name})")
            return False
        
        # Vérification : la colonne doit être valide
        if not self.board.is_valid_location(col):
            print(f"[DEBUG] Colonne {col} invalide (pleine ou hors limites)")
            return False
        
        # Placement du pion avec gravité
        row = self.board.get_next_open_row(col)
        if row is None:
            print(f"[DEBUG] Erreur : get_next_open_row a retourné None")
            return False  # Sécurité supplémentaire
        
        print(f"[DEBUG] Placement du pion : row={row}, col={col}, player={self.current_player}")
        self.board.drop_piece(row, col, self.current_player)
        
        # Enregistrement du coup dans l'historique
        self.move_history.append((col, self.current_player))
        print(f"[DEBUG] Coup enregistré. Total coups joués : {len(self.move_history)}")
        
        # Vérification de la victoire
        has_won = self.board.check_win(self.current_player)
        print(f"[DEBUG] Vérification victoire pour joueur {self.current_player} : {has_won}")
        
        if has_won:
            self.state = GameState.FINISHED
            self.winner = self.current_player
            print(f"[DEBUG] 🎉 VICTOIRE détectée pour le joueur {self.current_player}")
            return True
        
        # Vérification de l'égalité (plateau plein)
        is_draw = self.board.is_full()
        print(f"[DEBUG] Vérification plateau plein : {is_draw}")
        
        if is_draw:
            self.state = GameState.FINISHED
            self.winner = None  # Aucun gagnant en cas d'égalité
            print(f"[DEBUG] 🤝 ÉGALITÉ détectée (plateau plein)")
            return True
        
        # Changement de joueur pour le prochain tour
        print(f"[DEBUG] Changement de joueur : {self.current_player} -> ", end="")
        self._switch_player()
        print(f"{self.current_player}")
        
        return True
    
    def _switch_player(self) -> None:
        """
        Alterne entre PLAYER1 et PLAYER2.
        
        Méthode privée appelée après chaque coup valide.
        """
        self.current_player = PLAYER2 if self.current_player == PLAYER1 else PLAYER1
    
    def get_current_player(self) -> int:
        """
        Retourne le joueur dont c'est le tour.
        
        Returns:
            PLAYER1 ou PLAYER2
        """
        return self.current_player
    
    def get_winner(self) -> Optional[int]:
        """
        Retourne le joueur gagnant si la partie est terminée.
        
        Returns:
            PLAYER1, PLAYER2 si victoire, None si égalité ou partie en cours
        """
        return self.winner
    
    def is_game_over(self) -> bool:
        """
        Vérifie si la partie est terminée (victoire ou égalité).
        
        Returns:
            True si la partie est terminée, False sinon
        """
        return self.state == GameState.FINISHED
    
    def get_winning_positions(self) -> list[tuple[int, int]]:
        """
        Retourne les positions des pions formant l'alignement gagnant.
        
        Returns:
            Liste des coordonnées (row, col) des pions gagnants,
            ou liste vide si pas de gagnant
        """
        if self.winner is None:
            return []
        
        return self.board.get_winning_positions(self.winner)
    
    def undo(self) -> bool:
        """
        Annule le dernier coup joué.
        
        Appelle Board.undo_last_move() pour retirer le pion de la grille,
        puis inverse le tour pour revenir au joueur précédent.
        Réinitialise également l'état de la partie si elle était terminée.
        
        Returns:
            True si l'annulation a réussi, False si impossible (historique vide)
        """
        print(f"\n[GAME DEBUG] === UNDO APPELÉ ===")
        print(f"[GAME DEBUG] Joueur actuel AVANT undo : {self.current_player}")
        print(f"[GAME DEBUG] État de la partie : {self.state.name}")
        
        # Tentative d'annulation sur le plateau
        success = self.board.undo_last_move()
        
        if success:
            # Changement de joueur (retour au joueur précédent)
            self._switch_player()
            
            # Réinitialisation de l'état si la partie était terminée
            if self.state == GameState.FINISHED:
                self.state = GameState.IN_PROGRESS
                self.winner = None
                print(f"[GAME DEBUG] Partie réactivée (était terminée)")
            
            print(f"[GAME DEBUG] Joueur actuel APRÈS undo : {self.current_player}")
            print(f"[GAME DEBUG] === UNDO RÉUSSI ===\n")
            return True
        else:
            print(f"[GAME DEBUG] === UNDO ÉCHOUÉ ===\n")
            return False
    
    def get_valid_moves(self) -> list[int]:
        """
        Retourne la liste des colonnes jouables.
        
        Utile pour l'IA et la validation des inputs utilisateur.
        
        Returns:
            Liste des indices de colonnes valides
        """
        return self.board.get_valid_locations()
    
    def undo_last_move(self) -> bool:
        """
        Annule le dernier coup joué (utile pour l'IA Minimax).
        
        Restaure l'état de la partie avant le dernier coup.
        
        Returns:
            True si l'annulation a réussi, False si aucun coup à annuler
        """
        if not self.move_history:
            return False
        
        # Récupération du dernier coup
        col, player = self.move_history.pop()
        
        # Recherche de la case à vider (la plus haute dans la colonne)
        for row in range(len(self.board.grid)):
            if self.board.grid[row][col] != 0:
                self.board.grid[row][col] = 0
                break
        
        # Restauration de l'état de la partie
        self.current_player = player
        self.state = GameState.IN_PROGRESS
        self.winner = None
        
        return True
    
    def reset(self) -> None:
        """
        Réinitialise la partie pour une nouvelle manche.
        
        Remet le plateau à zéro et redémarre avec le joueur 1.
        """
        self.board.reset()
        self.current_player = PLAYER1
        self.state = GameState.IN_PROGRESS
        self.winner = None
        self.move_history = []
    
    def get_board_copy(self) -> Board:
        """
        Retourne une copie du plateau actuel.
        
        Utile pour l'IA qui doit simuler des coups sans modifier le jeu réel.
        
        Returns:
            Copie profonde du plateau actuel
        """
        return self.board.copy()
    
    def get_move_count(self) -> int:
        """
        Retourne le nombre de coups joués depuis le début de la partie.
        
        Returns:
            Nombre de coups dans l'historique
        """
        return len(self.move_history)
    
    def to_dict(self) -> dict:
        """
        Convertit le jeu en dictionnaire pour la sérialisation JSON.
        
        Returns:
            Dictionnaire contenant l'état complet de la partie
        """
        return {
            'board': self.board.to_dict(),
            'current_player': self.current_player,
            'state': self.state.name,  # Conversion enum -> string
            'winner': self.winner,
            'move_history': self.move_history
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Game':
        """
        Crée une instance de Game à partir d'un dictionnaire.
        
        Args:
            data: Dictionnaire contenant l'état complet de la partie
            
        Returns:
            Nouvelle instance de Game avec les données restaurées
        """
        game = cls()
        game.board = Board.from_dict(data['board'])
        game.current_player = data['current_player']
        game.state = GameState[data['state']]  # Conversion string -> enum
        game.winner = data['winner']
        game.move_history = [tuple(item) for item in data['move_history']]
        print(f"[GAME DEBUG] Partie restaurée : joueur {game.current_player}, état {game.state.name}")
        return game
    
    def __str__(self) -> str:
        """
        Représentation textuelle de l'état du jeu pour le débogage.
        
        Returns:
            String formaté avec les informations de la partie
        """
        status = f"État: {self.state.name}"
        player = f"Joueur actuel: {self.current_player}"
        winner = f"Gagnant: {self.winner if self.winner else 'Aucun'}"
        moves = f"Coups joués: {len(self.move_history)}"
        
        return f"{status} | {player} | {winner} | {moves}\n{self.board}"
