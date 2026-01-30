"""
Module de gestion de la base de données MySQL pour Connect Four.
Gère l'enregistrement des parties avec chaînage intelligent et détection de symétries.
"""

import os
from typing import Optional, Dict, List, Tuple
import mysql.connector
from mysql.connector import Error, MySQLConnection
from mysql.connector.cursor import MySQLCursor
from dotenv import load_dotenv


class DatabaseManager:
    """
    Gestionnaire de base de données MySQL pour Connect Four.
    
    Fonctionnalités :
    - Connexion à MySQL via variables d'environnement
    - Création automatique de la table 'games'
    - Insertion avec détection de symétries et chaînage intelligent
    - Requêtes pour lecture et replay
    
    Le chaînage permet de naviguer entre les parties triées par leur séquence de coups.
    """
    
    def __init__(self) -> None:
        """
        Initialise le gestionnaire de base de données.
        Charge les variables d'environnement et configure la connexion.
        """
        # Chargement des variables d'environnement depuis .env
        load_dotenv()
        
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', 3306))
        self.user = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASSWORD', '')
        self.database = os.getenv('DB_NAME', 'connect4')
        
        # Connexion initialisée à None (sera créée lors de l'utilisation)
        self.connection: Optional[MySQLConnection] = None
        
        print(f"[DB_MANAGER DEBUG] Configuration chargée - Host: {self.host}, DB: {self.database}")
    
    def connect(self) -> bool:
        """
        Établit la connexion à la base de données MySQL.
        
        Returns:
            True si la connexion réussit, False sinon
        """
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                autocommit=False  # Contrôle manuel des transactions
            )
            
            if self.connection.is_connected():
                db_info = self.connection.get_server_info()
                print(f"[DB_MANAGER DEBUG] ✅ Connecté à MySQL Server version {db_info}")
                return True
            else:
                print("[DB_MANAGER ERROR] ❌ Échec de la connexion")
                return False
                
        except Error as e:
            print(f"[DB_MANAGER ERROR] Erreur de connexion MySQL : {e}")
            self.connection = None
            return False
    
    def disconnect(self) -> None:
        """
        Ferme la connexion à la base de données.
        """
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("[DB_MANAGER DEBUG] 🔌 Connexion MySQL fermée")
    
    def create_tables(self) -> bool:
        """
        Crée la table 'games' si elle n'existe pas déjà.
        
        Structure de la table :
        - id : Identifiant unique auto-incrémenté
        - coups : Séquence des colonnes jouées (ex: '431256')
        - coups_symetrique : Séquence miroir calculée (ex: '679854')
        - id_antecedent : ID de la partie précédente dans le chaînage
        - id_suivant : ID de la partie suivante dans le chaînage
        - mode_jeu : Mode de jeu (PvP, PvAI, AIvsAI)
        - statut : Statut de la partie (EN_COURS, TERMINEE, ABANDONNEE)
        - ligne_gagnante : Coordonnées de l'alignement gagnant (JSON)
        - numero : Numéro optionnel de la partie
        
        Returns:
            True si la création réussit, False sinon
        """
        if not self.connection or not self.connection.is_connected():
            print("[DB_MANAGER ERROR] Pas de connexion active")
            return False
        
        cursor: Optional[MySQLCursor] = None
        
        try:
            cursor = self.connection.cursor()
            
            # Création de la table games
            create_table_query = """
            CREATE TABLE IF NOT EXISTS games (
                id INT AUTO_INCREMENT PRIMARY KEY,
                coups VARCHAR(500) NOT NULL,
                coups_symetrique VARCHAR(500) NOT NULL,
                id_antecedent INT DEFAULT NULL,
                id_suivant INT DEFAULT NULL,
                mode_jeu VARCHAR(50) DEFAULT 'PvP',
                statut VARCHAR(50) DEFAULT 'EN_COURS',
                ligne_gagnante TEXT DEFAULT NULL,
                numero INT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_coups (coups(255)),
                INDEX idx_coups_sym (coups_symetrique(255)),
                FOREIGN KEY (id_antecedent) REFERENCES games(id) ON DELETE SET NULL,
                FOREIGN KEY (id_suivant) REFERENCES games(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            
            cursor.execute(create_table_query)
            self.connection.commit()
            
            print("[DB_MANAGER DEBUG] ✅ Table 'games' créée ou déjà existante")
            return True
            
        except Error as e:
            print(f"[DB_MANAGER ERROR] Erreur lors de la création de la table : {e}")
            if self.connection:
                self.connection.rollback()
            return False
            
        finally:
            if cursor:
                cursor.close()
    
    def calculate_symmetric_sequence(self, coups: str) -> str:
        """
        Calcule la séquence symétrique (miroir) d'une séquence de coups.
        
        Pour une grille de 9 colonnes (numérotées 1-9), le miroir est : 10 - c
        Exemples :
        - '125' -> '985' (10-1=9, 10-2=8, 10-5=5)
        - '431' -> '679' (10-4=6, 10-3=7, 10-1=9)
        
        Args:
            coups : Séquence de coups (ex: '125431')
            
        Returns:
            Séquence symétrique (ex: '985679')
        """
        if not coups:
            return ''
        
        symmetric = ''
        for char in coups:
            try:
                col = int(char)
                # Formule du miroir pour 9 colonnes (1-9)
                symmetric_col = 10 - col
                symmetric += str(symmetric_col)
            except ValueError:
                # Si le caractère n'est pas un chiffre, on le garde tel quel
                symmetric += char
        
        return symmetric
    
    def check_duplicate(self, coups: str, coups_symetrique: str) -> bool:
        """
        Vérifie si une partie avec la séquence donnée ou sa symétrique existe déjà.
        
        Args:
            coups : Séquence de coups
            coups_symetrique : Séquence symétrique
            
        Returns:
            True si un doublon existe, False sinon
        """
        if not self.connection or not self.connection.is_connected():
            return False
        
        cursor: Optional[MySQLCursor] = None
        
        try:
            cursor = self.connection.cursor()
            
            # Recherche d'une partie avec la même séquence ou sa symétrique
            query = """
            SELECT id FROM games 
            WHERE coups = %s OR coups = %s
            LIMIT 1
            """
            
            cursor.execute(query, (coups, coups_symetrique))
            result = cursor.fetchone()
            
            if result:
                print(f"[DB_MANAGER DEBUG] ⚠️ Doublon détecté : séquence existante (ID: {result[0]})")
                return True
            
            return False
            
        except Error as e:
            print(f"[DB_MANAGER ERROR] Erreur lors de la vérification de doublon : {e}")
            return False
            
        finally:
            if cursor:
                cursor.close()
    
    def find_chain_neighbors(self, coups: str) -> Tuple[Optional[int], Optional[int]]:
        """
        Trouve les voisins dans le chaînage (parties immédiatement avant et après).
        
        Logique :
        - Antécédent (A) : Partie avec 'coups' < nouveau_coups (tri lexicographique)
        - Suivant (B) : Partie avec 'coups' > nouveau_coups
        
        Args:
            coups : Séquence de la nouvelle partie
            
        Returns:
            Tuple (id_antecedent, id_suivant) ou (None, None) en cas d'erreur
        """
        if not self.connection or not self.connection.is_connected():
            return (None, None)
        
        cursor: Optional[MySQLCursor] = None
        
        try:
            cursor = self.connection.cursor()
            
            # Recherche de l'antécédent (partie juste avant)
            query_antecedent = """
            SELECT id FROM games 
            WHERE coups < %s 
            ORDER BY coups DESC 
            LIMIT 1
            """
            cursor.execute(query_antecedent, (coups,))
            result_ante = cursor.fetchone()
            id_antecedent = result_ante[0] if result_ante else None
            
            # Recherche du suivant (partie juste après)
            query_suivant = """
            SELECT id FROM games 
            WHERE coups > %s 
            ORDER BY coups ASC 
            LIMIT 1
            """
            cursor.execute(query_suivant, (coups,))
            result_suiv = cursor.fetchone()
            id_suivant = result_suiv[0] if result_suiv else None
            
            print(f"[DB_MANAGER DEBUG] Voisins trouvés - Antécédent: {id_antecedent}, Suivant: {id_suivant}")
            
            return (id_antecedent, id_suivant)
            
        except Error as e:
            print(f"[DB_MANAGER ERROR] Erreur lors de la recherche des voisins : {e}")
            return (None, None)
            
        finally:
            if cursor:
                cursor.close()
    
    def update_chain_links(self, new_id: int, id_antecedent: Optional[int], 
                          id_suivant: Optional[int]) -> bool:
        """
        Met à jour les liens de chaînage après l'insertion d'une nouvelle partie.
        
        Opérations :
        1. Ping pour vérifier la connexion
        2. Si antécédent existe : Met à jour son id_suivant vers new_id
        3. Si suivant existe : Met à jour son id_antecedent vers new_id
        4. Met à jour les liens de la nouvelle partie
        5. COMMIT explicite des changements
        
        Args:
            new_id : ID de la nouvelle partie insérée
            id_antecedent : ID de la partie précédente
            id_suivant : ID de la partie suivante
            
        Returns:
            True si la mise à jour réussit, False sinon
        """
        cursor: Optional[MySQLCursor] = None
        
        try:
            # Vérification de la connexion
            if not self.connection or not self.connection.is_connected():
                print("[DB_MANAGER ERROR] ❌ Pas de connexion active pour le chaînage")
                return False
            
            # Ping pour éviter les déconnexions
            self.connection.ping(reconnect=True)
            
            cursor = self.connection.cursor()
            
            # Mise à jour de l'antécédent (son suivant devient la nouvelle partie)
            if id_antecedent:
                query_update_ante = """
                UPDATE games 
                SET id_suivant = %s 
                WHERE id = %s
                """
                cursor.execute(query_update_ante, (new_id, id_antecedent))
                print(f"[DB_MANAGER DEBUG] ↗️ Antécédent {id_antecedent} mis à jour")
            
            # Mise à jour du suivant (son antécédent devient la nouvelle partie)
            if id_suivant:
                query_update_suiv = """
                UPDATE games 
                SET id_antecedent = %s 
                WHERE id = %s
                """
                cursor.execute(query_update_suiv, (new_id, id_suivant))
                print(f"[DB_MANAGER DEBUG] ↘️ Suivant {id_suivant} mis à jour")
            
            # Mise à jour des liens de la nouvelle partie
            query_update_new = """
            UPDATE games 
            SET id_antecedent = %s, id_suivant = %s 
            WHERE id = %s
            """
            cursor.execute(query_update_new, (id_antecedent, id_suivant, new_id))
            print(f"[DB_MANAGER DEBUG] 🔗 Nouvelle partie {new_id} chaînée")
            
            # COMMIT des mises à jour
            self.connection.commit()
            print(f"[DB_MANAGER DEBUG] ✅ Chaînage validé (COMMIT OK)")
            return True
            
        except Error as e:
            print(f"[DB_MANAGER ERROR] ❌ Erreur MySQL lors du chaînage : {e}")
            print(f"[DB_MANAGER ERROR] Détails - Code: {e.errno}, Message: {e.msg}")
            if self.connection:
                try:
                    self.connection.rollback()
                    print("[DB_MANAGER DEBUG] 🔙 ROLLBACK du chaînage")
                except:
                    pass
            return False
        
        except Exception as e:
            print(f"[DB_MANAGER ERROR] ❌ Erreur inattendue lors du chaînage : {type(e).__name__} - {e}")
            if self.connection:
                try:
                    self.connection.rollback()
                except:
                    pass
            return False
            
        finally:
            if cursor:
                cursor.close()
    
    def insert_game(self, coups: str, mode_jeu: str = 'PvP', 
                   statut: str = 'TERMINEE', ligne_gagnante: Optional[str] = None) -> Optional[int]:
        """
        Insère une nouvelle partie dans la base de données avec chaînage intelligent.
        
        Processus :
        1. Vérification de la connexion avec ping
        2. Calcul de la séquence symétrique
        3. Vérification de doublons (séquence ou symétrique)
        4. Si pas de doublon : Insertion de la partie
        5. Recherche des voisins dans le chaînage
        6. Mise à jour des liens de chaînage
        7. COMMIT explicite des changements
        
        Args:
            coups : Séquence des colonnes jouées (ex: '431256')
            mode_jeu : Mode de jeu (PvP, PvAI, AIvsAI)
            statut : Statut final (EN_COURS, TERMINEE, ABANDONNEE)
            ligne_gagnante : Coordonnées de l'alignement gagnant (JSON)
            
        Returns:
            ID de la partie insérée, ou None en cas d'échec/doublon
        """
        cursor: Optional[MySQLCursor] = None
        
        try:
            # Vérification de la connexion
            if not self.connection or not self.connection.is_connected():
                print("[DB_MANAGER ERROR] ❌ Pas de connexion active")
                return None
            
            # Ping pour éviter les déconnexions
            self.connection.ping(reconnect=True)
            print("[DB_MANAGER DEBUG] 🔄 Connexion vérifiée (ping OK)")
            
            # Étape 1 : Calcul de la séquence symétrique
            coups_symetrique = self.calculate_symmetric_sequence(coups)
            print(f"[DB_MANAGER DEBUG] Coups: '{coups}' -> Symétrique: '{coups_symetrique}'")
            
            # Étape 2 : Vérification de doublons
            if self.check_duplicate(coups, coups_symetrique):
                print("[DB_MANAGER DEBUG] ⚠️ Insertion annulée : doublon détecté")
                return None
            
            cursor = self.connection.cursor()
            
            # Étape 3 : Insertion de la nouvelle partie
            insert_query = """
            INSERT INTO games (coups, coups_symetrique, mode_jeu, statut, ligne_gagnante)
            VALUES (%s, %s, %s, %s, %s)
            """
            
            print(f"[DB_MANAGER DEBUG] 📝 Insertion dans MySQL...")
            cursor.execute(insert_query, (coups, coups_symetrique, mode_jeu, statut, ligne_gagnante))
            new_id = cursor.lastrowid
            
            # COMMIT de l'insertion
            self.connection.commit()
            print(f"[DB_MANAGER DEBUG] ✅ Partie insérée avec ID: {new_id} (COMMIT OK)")
            
            # Étape 4 : Recherche des voisins
            id_antecedent, id_suivant = self.find_chain_neighbors(coups)
            
            # Étape 5 : Mise à jour du chaînage
            if self.update_chain_links(new_id, id_antecedent, id_suivant):
                print(f"[DB_MANAGER DEBUG] 🎉 SUCCÈS : Données insérées - Partie {new_id} chaînée")
                return new_id
            else:
                print("[DB_MANAGER WARNING] ⚠️ Partie insérée mais chaînage incomplet")
                return new_id
            
        except Error as e:
            print(f"[DB_MANAGER ERROR] ❌ Erreur MySQL lors de l'insertion : {e}")
            print(f"[DB_MANAGER ERROR] Détails - Code: {e.errno}, Message: {e.msg}")
            if self.connection:
                try:
                    self.connection.rollback()
                    print("[DB_MANAGER DEBUG] 🔙 ROLLBACK effectué")
                except:
                    pass
            return None
        
        except Exception as e:
            print(f"[DB_MANAGER ERROR] ❌ Erreur inattendue : {type(e).__name__} - {e}")
            if self.connection:
                try:
                    self.connection.rollback()
                except:
                    pass
            return None
            
        finally:
            if cursor:
                cursor.close()
    
    def get_all_games(self, order_by: str = 'coups') -> List[Dict]:
        """
        Récupère toutes les parties triées par la colonne spécifiée.
        
        Args:
            order_by : Colonne de tri (par défaut 'coups' pour ordre lexicographique)
            
        Returns:
            Liste de dictionnaires représentant les parties
        """
        if not self.connection or not self.connection.is_connected():
            print("[DB_MANAGER ERROR] Pas de connexion active")
            return []
        
        cursor: Optional[MySQLCursor] = None
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            query = f"""
            SELECT id, coups, coups_symetrique, id_antecedent, id_suivant,
                   mode_jeu, statut, ligne_gagnante, numero, created_at
            FROM games
            ORDER BY {order_by}
            """
            
            cursor.execute(query)
            games = cursor.fetchall()
            
            print(f"[DB_MANAGER DEBUG] 📋 {len(games)} parties récupérées")
            return games
            
        except Error as e:
            print(f"[DB_MANAGER ERROR] Erreur lors de la récupération : {e}")
            return []
            
        finally:
            if cursor:
                cursor.close()
    
    def get_game_by_id(self, game_id: int) -> Optional[Dict]:
        """
        Récupère les détails d'une partie spécifique par son ID.
        
        Args:
            game_id : Identifiant de la partie
            
        Returns:
            Dictionnaire avec les détails de la partie, ou None si non trouvée
        """
        if not self.connection or not self.connection.is_connected():
            print("[DB_MANAGER ERROR] Pas de connexion active")
            return None
        
        cursor: Optional[MySQLCursor] = None
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            query = """
            SELECT id, coups, coups_symetrique, id_antecedent, id_suivant,
                   mode_jeu, statut, ligne_gagnante, numero, created_at
            FROM games
            WHERE id = %s
            """
            
            cursor.execute(query, (game_id,))
            game = cursor.fetchone()
            
            if game:
                print(f"[DB_MANAGER DEBUG] 🎮 Partie {game_id} récupérée")
            else:
                print(f"[DB_MANAGER DEBUG] ❌ Partie {game_id} non trouvée")
            
            return game
            
        except Error as e:
            print(f"[DB_MANAGER ERROR] Erreur lors de la récupération : {e}")
            return None
            
        finally:
            if cursor:
                cursor.close()
    
    def get_game_count(self) -> int:
        """
        Compte le nombre total de parties enregistrées.
        
        Returns:
            Nombre de parties
        """
        if not self.connection or not self.connection.is_connected():
            return 0
        
        cursor: Optional[MySQLCursor] = None
        
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM games")
            result = cursor.fetchone()
            
            count = result[0] if result else 0
            print(f"[DB_MANAGER DEBUG] 📊 Nombre de parties : {count}")
            return count
            
        except Error as e:
            print(f"[DB_MANAGER ERROR] Erreur lors du comptage : {e}")
            return 0
            
        finally:
            if cursor:
                cursor.close()
    
    def delete_game(self, game_id: int) -> bool:
        """
        Supprime une partie et met à jour le chaînage.
        
        Args:
            game_id : ID de la partie à supprimer
            
        Returns:
            True si la suppression réussit, False sinon
        """
        if not self.connection or not self.connection.is_connected():
            return False
        
        cursor: Optional[MySQLCursor] = None
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # Récupération des liens de la partie à supprimer
            cursor.execute("SELECT id_antecedent, id_suivant FROM games WHERE id = %s", (game_id,))
            game = cursor.fetchone()
            
            if not game:
                print(f"[DB_MANAGER DEBUG] Partie {game_id} non trouvée")
                return False
            
            id_ante = game['id_antecedent']
            id_suiv = game['id_suivant']
            
            # Reconnexion des voisins entre eux
            if id_ante:
                cursor.execute("UPDATE games SET id_suivant = %s WHERE id = %s", (id_suiv, id_ante))
            
            if id_suiv:
                cursor.execute("UPDATE games SET id_antecedent = %s WHERE id = %s", (id_ante, id_suiv))
            
            # Suppression de la partie
            cursor.execute("DELETE FROM games WHERE id = %s", (game_id,))
            
            self.connection.commit()
            print(f"[DB_MANAGER DEBUG] 🗑️ Partie {game_id} supprimée et chaînage mis à jour")
            return True
            
        except Error as e:
            print(f"[DB_MANAGER ERROR] Erreur lors de la suppression : {e}")
            if self.connection:
                self.connection.rollback()
            return False
            
        finally:
            if cursor:
                cursor.close()


# ========================================
# EXEMPLE D'UTILISATION
# ========================================

def example_usage():
    """
    Exemple d'utilisation du DatabaseManager.
    """
    # Création du gestionnaire
    db = DatabaseManager()
    
    # Connexion
    if not db.connect():
        print("Échec de la connexion")
        return
    
    # Création des tables
    db.create_tables()
    
    # Insertion de parties
    game1_id = db.insert_game('125', mode_jeu='PvP', statut='TERMINEE')
    game2_id = db.insert_game('431', mode_jeu='PvAI', statut='TERMINEE')
    game3_id = db.insert_game('222', mode_jeu='PvP', statut='TERMINEE')
    
    # Tentative d'insertion d'un doublon symétrique
    # '985' est le symétrique de '125'
    game4_id = db.insert_game('985', mode_jeu='PvP', statut='TERMINEE')  # Sera refusé
    
    # Récupération de toutes les parties
    all_games = db.get_all_games()
    print(f"\n📋 Toutes les parties ({len(all_games)}) :")
    for game in all_games:
        print(f"  - ID {game['id']}: {game['coups']} (sym: {game['coups_symetrique']})")
        print(f"    Liens: Antécédent={game['id_antecedent']}, Suivant={game['id_suivant']}")
    
    # Récupération d'une partie spécifique
    if game1_id:
        game_details = db.get_game_by_id(game1_id)
        print(f"\n🎮 Détails de la partie {game1_id} :")
        print(game_details)
    
    # Statistiques
    total = db.get_game_count()
    print(f"\n📊 Total de parties : {total}")
    
    # Déconnexion
    db.disconnect()


if __name__ == "__main__":
    example_usage()
