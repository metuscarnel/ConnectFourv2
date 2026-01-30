"""
Module de gestion de la base de données MySQL pour Connect Four.
Gère l'enregistrement des parties avec chaînage intelligent.
"""

import os
from typing import Optional, Dict, List
import mysql.connector
from mysql.connector import Error, MySQLConnection
from dotenv import load_dotenv


class DatabaseManager:
    """
    Gestionnaire de base de données MySQL pour Connect Four.
    
    Fonctionnalités :
    - Connexion à MySQL via variables d'environnement
    - Création automatique de la table 'games'
    - Insertion avec détection de symétries et chaînage intelligent
    - Import depuis fichiers .txt
    """
    
    def __init__(self) -> None:
        """Initialise le gestionnaire de base de données."""
        load_dotenv()
        
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', 3306))
        self.user = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASSWORD', '')
        self.database = os.getenv('DB_NAME', 'connect4')
        
        self.connection: Optional[MySQLConnection] = None
        
        print(f"[DB_MANAGER DEBUG] Configuration chargée - Host: {self.host}, DB: {self.database}")
    
    def connect(self) -> bool:
        """Établit la connexion à la base de données MySQL."""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            
            if self.connection.is_connected():
                db_info = self.connection.get_server_info()
                print(f"[DB_MANAGER DEBUG] ✅ Connecté à MySQL Server version {db_info}")
                return True
                
        except Error as e:
            print(f"[DB_MANAGER ERROR] Erreur de connexion : {e}")
            return False
    
    def disconnect(self) -> None:
        """Ferme la connexion à la base de données."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("[DB_MANAGER DEBUG] 🔌 Connexion MySQL fermée")
    
    def create_tables(self) -> None:
        """Crée la table 'games' si elle n'existe pas."""
        if not self.connection or not self.connection.is_connected():
            print("[DB_MANAGER ERROR] Pas de connexion active")
            return
        
        try:
            cursor = self.connection.cursor()
            
            create_table_query = """
            CREATE TABLE IF NOT EXISTS games (
                id INT AUTO_INCREMENT PRIMARY KEY,
                coups VARCHAR(255) NOT NULL UNIQUE,
                coups_symetrique VARCHAR(255),
                mode_jeu VARCHAR(50),
                statut VARCHAR(50),
                ligne_gagnante TEXT,
                id_antecedent INT,
                id_suivant INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            cursor.execute(create_table_query)
            self.connection.commit()
            cursor.close()
            
            print("[DB_MANAGER DEBUG] ✅ Table 'games' créée ou déjà existante")
            
        except Error as e:
            print(f"[DB_MANAGER ERROR] Erreur création table : {e}")
    
    def import_from_txt_file(self, file_path: str) -> dict:
        """
        Importe une partie depuis un fichier .txt unique.
        
        Le nom du fichier doit contenir la séquence de coups (ex: "4554433.txt").
        
        Args:
            file_path: Chemin complet du fichier .txt
            
        Returns:
            Dictionnaire avec résultat : {
                'success': bool,
                'game_id': int (si success),
                'error': str (si échec)
            }
        """
        import os
        
        result = {
            'success': False,
            'game_id': None,
            'error': ''
        }
        
        try:
            # Vérification que le fichier existe
            if not os.path.exists(file_path):
                result['error'] = f"Fichier introuvable : {file_path}"
                return result
            
            # Extraction du nom de fichier
            filename = os.path.basename(file_path)
            
            # Extraction de la séquence depuis le nom du fichier
            coups = filename.replace('.txt', '')
            
            # Validation : que des chiffres entre 1 et 9
            if not coups or not all(c.isdigit() and '1' <= c <= '9' for c in coups):
                result['error'] = f"Nom de fichier invalide : {filename}. Doit contenir uniquement des chiffres 1-9."
                return result
            
            # Calcul du symétrique (miroir : 10 - colonne)
            coups_symetrique = ''.join(str(10 - int(c)) for c in coups)
            
            # Vérification si la partie ou son symétrique existe déjà
            cursor = self.connection.cursor(dictionary=True)
            check_query = """
                SELECT id FROM games 
                WHERE coups = %s OR coups = %s
                LIMIT 1
            """
            cursor.execute(check_query, (coups, coups_symetrique))
            existing = cursor.fetchone()
            cursor.close()
            
            if existing:
                result['error'] = f"Doublon : cette partie existe déjà (ID {existing['id']})"
                return result
            
            # Insertion de la nouvelle partie
            cursor = self.connection.cursor()
            insert_query = """
                INSERT INTO games (coups, coups_symetrique, mode_jeu, statut)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_query, (coups, coups_symetrique, 'Import', 'TERMINEE'))
            self.connection.commit()
            game_id = cursor.lastrowid
            cursor.close()
            
            # Reconstruction des chaînages
            print(f"[DB_IMPORT] ✅ Importé: {filename} -> ID {game_id}")
            print(f"[DB_IMPORT] 🔗 Reconstruction des chaînages...")
            self._rebuild_chains()
            
            result['success'] = True
            result['game_id'] = game_id
            
        except Exception as e:
            result['error'] = f"Erreur : {str(e)}"
            print(f"[DB_IMPORT] ❌ Erreur : {e}")
        
        return result
    
    def import_from_txt_files(self, folder_path: str) -> dict:
        """
        Importe des parties depuis des fichiers .txt dans un dossier.
        
        Chaque fichier doit être nommé avec la séquence de coups (ex: "4554433.txt").
        Le contenu du fichier peut contenir des métadonnées optionnelles.
        
        Args:
            folder_path: Chemin du dossier contenant les fichiers .txt
            
        Returns:
            Dictionnaire avec statistiques : {
                'total_files': int,
                'imported': int,
                'duplicates': int,
                'errors': int,
                'error_details': list
            }
        """
        stats = {
            'total_files': 0,
            'imported': 0,
            'duplicates': 0,
            'errors': 0,
            'error_details': []
        }
        
        # Vérification que le dossier existe
        if not os.path.exists(folder_path):
            print(f"[DB_IMPORT] ⚠️  Dossier introuvable: {folder_path}")
            stats['error_details'].append(f"Dossier introuvable: {folder_path}")
            stats['errors'] = 1
            return stats
        
        # Listage des fichiers .txt
        try:
            txt_files = [f for f in os.listdir(folder_path) if f.endswith('.txt')]
            stats['total_files'] = len(txt_files)
            
            print(f"[DB_IMPORT] 📂 Trouvé {len(txt_files)} fichier(s) .txt dans {folder_path}")
            
            for filename in txt_files:
                try:
                    # Extraction de la séquence depuis le nom du fichier
                    coups = filename.replace('.txt', '')
                    
                    # Validation basique : que des chiffres entre 1 et 9
                    if not coups or not all(c.isdigit() and '1' <= c <= '9' for c in coups):
                        print(f"[DB_IMPORT] ⚠️  Nom de fichier invalide: {filename}")
                        stats['errors'] += 1
                        stats['error_details'].append(f"{filename}: format invalide")
                        continue
                    
                    # Calcul du symétrique (miroir : 10 - colonne)
                    coups_symetrique = ''.join(str(10 - int(c)) for c in coups)
                    
                    # Vérification si la partie ou son symétrique existe déjà
                    cursor = self.connection.cursor(dictionary=True)
                    check_query = """
                        SELECT id FROM games 
                        WHERE coups = %s OR coups = %s
                        LIMIT 1
                    """
                    cursor.execute(check_query, (coups, coups_symetrique))
                    existing = cursor.fetchone()
                    cursor.close()
                    
                    if existing:
                        stats['duplicates'] += 1
                        print(f"[DB_IMPORT] ⏭️  Doublon ignoré: {filename}")
                        continue
                    
                    # Insertion de la nouvelle partie
                    cursor = self.connection.cursor()
                    insert_query = """
                        INSERT INTO games (coups, coups_symetrique, mode_jeu, statut)
                        VALUES (%s, %s, %s, %s)
                    """
                    cursor.execute(insert_query, (coups, coups_symetrique, 'Import', 'TERMINEE'))
                    self.connection.commit()
                    game_id = cursor.lastrowid
                    cursor.close()
                    
                    stats['imported'] += 1
                    print(f"[DB_IMPORT] ✅ Importé: {filename} -> ID {game_id}")
                
                except Exception as e:
                    stats['errors'] += 1
                    error_msg = f"{filename}: {str(e)}"
                    stats['error_details'].append(error_msg)
                    print(f"[DB_IMPORT] ❌ Erreur avec {filename}: {e}")
            
            # Reconstruction des chaînages après import
            if stats['imported'] > 0:
                print(f"\n[DB_IMPORT] 🔗 Reconstruction des chaînages...")
                self._rebuild_chains()
            
            print(f"\n[DB_IMPORT] 📊 RÉSUMÉ:")
            print(f"  - Fichiers traités: {stats['total_files']}")
            print(f"  - Importés: {stats['imported']}")
            print(f"  - Doublons: {stats['duplicates']}")
            print(f"  - Erreurs: {stats['errors']}")
            
        except Exception as e:
            print(f"[DB_IMPORT] ❌ Erreur globale : {e}")
            stats['errors'] += 1
            stats['error_details'].append(f"Erreur globale: {str(e)}")
        
        return stats
    
    def _rebuild_chains(self) -> None:
        """Reconstruit les chaînages (id_antecedent et id_suivant) pour toute la table."""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # Récupération de TOUTES les parties triées par 'coups'
            cursor.execute("SELECT id, coups FROM games ORDER BY coups ASC")
            all_games = cursor.fetchall()
            
            print(f"[DB_REBUILD] 🔄 Reconstruction des chaînages pour {len(all_games)} parties...")
            
            # Mise à jour des liens
            for i, game in enumerate(all_games):
                id_antecedent = all_games[i - 1]['id'] if i > 0 else None
                id_suivant = all_games[i + 1]['id'] if i < len(all_games) - 1 else None
                
                update_query = """
                    UPDATE games
                    SET id_antecedent = %s, id_suivant = %s
                    WHERE id = %s
                """
                cursor.execute(update_query, (id_antecedent, id_suivant, game['id']))
            
            self.connection.commit()
            cursor.close()
            
            print(f"[DB_REBUILD] ✅ Chaînages reconstruits avec succès")
            
        except Exception as e:
            print(f"[DB_REBUILD] ❌ Erreur : {e}")
            if self.connection:
                self.connection.rollback()
    
    def get_all_games(self) -> list:
        """
        Récupère toutes les parties de la base de données triées par coups.
        
        Returns:
            Liste de dictionnaires contenant les informations des parties
        """
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
                SELECT id, coups, coups_symetrique, mode_jeu, statut, 
                       ligne_gagnante, id_antecedent, id_suivant, created_at
                FROM games
                ORDER BY coups ASC
            """
            cursor.execute(query)
            games = cursor.fetchall()
            cursor.close()
            
            print(f"[DB_MANAGER DEBUG] 📋 {len(games)} parties récupérées")
            return games
            
        except Exception as e:
            print(f"[DB_MANAGER ERROR] Erreur lors de la récupération : {e}")
            return []
    
    def get_game_by_id(self, game_id: int) -> Optional[dict]:
        """
        Récupère une partie spécifique par son ID.
        
        Args:
            game_id: ID de la partie à récupérer
        
        Returns:
            Dictionnaire contenant les informations de la partie, ou None si non trouvée
        """
        if not self.connection or not self.connection.is_connected():
            print("[DB_MANAGER ERROR] Pas de connexion active")
            return None
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
                SELECT id, coups, coups_symetrique, mode_jeu, statut, 
                       ligne_gagnante, id_antecedent, id_suivant, created_at
                FROM games
                WHERE id = %s
            """
            cursor.execute(query, (game_id,))
            game = cursor.fetchone()
            cursor.close()
            
            if game:
                print(f"[DB_MANAGER DEBUG] 📥 Partie {game_id} récupérée")
            else:
                print(f"[DB_MANAGER DEBUG] ⚠️ Partie {game_id} non trouvée")
            
            return game
            
        except Exception as e:
            print(f"[DB_MANAGER ERROR] Erreur lors de la récupération de la partie {game_id} : {e}")
            return None
    
    def truncate_games(self) -> bool:
        """
        Vide complètement la table games et réinitialise les auto-increment.
        
        ⚠️ ATTENTION : Cette opération est irréversible !
        
        Returns:
            True si la réinitialisation a réussi, False sinon
        """
        if not self.connection or not self.connection.is_connected():
            print("[DB_MANAGER ERROR] Pas de connexion active")
            return False
        
        try:
            cursor = self.connection.cursor()
            
            # Vider la table
            cursor.execute("TRUNCATE TABLE games")
            self.connection.commit()
            cursor.close()
            
            print("[DB_MANAGER DEBUG] 🗑️ Table 'games' vidée et IDs réinitialisés")
            return True
            
        except Error as e:
            print(f"[DB_MANAGER ERROR] Erreur lors de la réinitialisation : {e}")
            if self.connection:
                self.connection.rollback()
            return False
