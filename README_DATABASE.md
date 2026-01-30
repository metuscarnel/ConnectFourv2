# Installer les dépendances
pip install mysql-connector-python python-dotenv

# Créer la base de données
mysql -u root -p < database_setup.sql

# Lancer les tests
python test_database.py# Installer les dépendances
pip install mysql-connector-python python-dotenv

# Créer la base de données
mysql -u root -p < database_setup.sql

# Lancer les tests
python test_database.py# Installer les dépendances
pip install mysql-connector-python python-dotenv

# Créer la base de données
mysql -u root -p < database_setup.sql

# Lancer les tests
python test_database.py# Installer les dépendances
pip install mysql-connector-python python-dotenv

# Créer la base de données
mysql -u root -p < database_setup.sql

# Lancer les tests
python test_database.py# 🗄️ Gestionnaire de Base de Données MySQL - Connect Four

## 📋 Vue d'ensemble

Le module `db_manager.py` fournit une gestion complète de la base de données MySQL pour le jeu Puissance 4 (Connect Four). Il implémente un système de chaînage intelligent pour organiser les parties et détecte automatiquement les parties symétriques pour éviter les doublons.

## ✨ Fonctionnalités principales

### 1. **Chaînage Intelligent**
Les parties sont organisées en chaîne doublement liée basée sur l'ordre lexicographique des séquences de coups :
- `id_antecedent` : pointe vers la partie précédente
- `id_suivant` : pointe vers la partie suivante

**Exemple :**
```
Partie A (coups='125') ← Partie B (coups='431') → Partie C (coups='777')
```

### 2. **Détection de Symétrie**
Pour une grille 8×9, la symétrie est calculée avec la formule : `10 - colonne`

**Exemples :**
- `'125'` → Symétrique : `'985'` (10-1=9, 10-2=8, 10-5=5)
- `'431'` → Symétrique : `'679'` (10-4=6, 10-3=7, 10-1=9)

Si une partie avec la séquence symétrique existe déjà, l'insertion est refusée.

### 3. **Gestion des Doublons**
Avant chaque insertion, le système vérifie :
- ✅ La séquence exacte n'existe pas déjà
- ✅ La séquence symétrique n'existe pas déjà

## 🚀 Installation

### 1. Prérequis
```bash
# MySQL Server doit être installé et en cours d'exécution
# Vérifier l'installation :
mysql --version
```

### 2. Installation des dépendances Python
```bash
pip install -r requirements.txt
```

Dépendances nécessaires :
- `mysql-connector-python>=8.0.33`
- `python-dotenv>=1.0.0`

### 3. Configuration de la base de données

#### Créer la base de données MySQL :
```bash
mysql -u root -p < database_setup.sql
```

Ou manuellement :
```sql
CREATE DATABASE connect4 CHARACTER SET utf8mb4;
USE connect4;
-- Exécuter le contenu de database_setup.sql
```

#### Configurer le fichier .env :
```dotenv
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=votre_mot_de_passe
DB_NAME=connect4
```

## 📖 Utilisation

### Initialisation

```python
from src.utils.db_manager import DatabaseManager

# Créer une instance
db = DatabaseManager()

# Se connecter
if db.connect():
    print("Connexion réussie !")
    
    # Créer les tables
    db.create_tables()
else:
    print("Échec de connexion")
```

### Insertion d'une partie

```python
# Insertion simple
game_id = db.insert_game(
    coups='125431',
    mode_jeu='PvP',
    statut='TERMINEE',
    ligne_gagnante='[[0,0],[0,1],[0,2],[0,3]]'
)

if game_id:
    print(f"Partie insérée avec ID: {game_id}")
else:
    print("Insertion refusée (doublon détecté)")
```

### Récupération des parties

```python
# Toutes les parties (triées par coups)
all_games = db.get_all_games()

for game in all_games:
    print(f"ID: {game['id']}, Coups: {game['coups']}")

# Une partie spécifique
game = db.get_game_by_id(5)
if game:
    print(f"Mode: {game['mode_jeu']}, Statut: {game['statut']}")

# Compter les parties
total = db.get_game_count()
print(f"Total de parties: {total}")
```

### Navigation dans le chaînage

```python
# Récupérer une partie
game = db.get_game_by_id(10)

# Partie précédente
if game['id_antecedent']:
    prev_game = db.get_game_by_id(game['id_antecedent'])
    print(f"Partie précédente: {prev_game['coups']}")

# Partie suivante
if game['id_suivant']:
    next_game = db.get_game_by_id(game['id_suivant'])
    print(f"Partie suivante: {next_game['coups']}")
```

### Suppression avec mise à jour du chaînage

```python
# Supprimer une partie (le chaînage est automatiquement mis à jour)
if db.delete_game(15):
    print("Partie supprimée et chaînage mis à jour")
```

### Déconnexion

```python
# Toujours fermer la connexion proprement
db.disconnect()
```

## 🧪 Tests

### Lancer la suite de tests complète

```bash
python test_database.py
```

Tests inclus :
1. ✅ Connexion à la base de données
2. ✅ Création de la table 'games'
3. ✅ Calcul de symétrie
4. ✅ Insertion et chaînage
5. ✅ Détection de doublons
6. ✅ Opérations de lecture
7. ✅ Suppression avec mise à jour du chaînage

### Exemple de sortie

```
======================================================================
  TEST 4 : INSERTION ET CHAÎNAGE
======================================================================

📝 Insertion de parties :
  ✅ Partie '555' insérée (ID: 1)
  ✅ Partie '222' insérée (ID: 2)
  ✅ Partie '777' insérée (ID: 3)

🔗 Vérification du chaînage :
  Partie 1 (ID: 2):
    Coups: 222
    Antécédent: None
    Suivant: 1

  Partie 2 (ID: 1):
    Coups: 555
    Antécédent: 2
    Suivant: 3

  Partie 3 (ID: 3):
    Coups: 777
    Antécédent: 1
    Suivant: None
```

## 📊 Structure de la Table

```sql
CREATE TABLE games (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    coups               VARCHAR(500) NOT NULL,
    coups_symetrique    VARCHAR(500) NOT NULL,
    id_antecedent       INT DEFAULT NULL,
    id_suivant          INT DEFAULT NULL,
    mode_jeu            VARCHAR(50) DEFAULT 'PvP',
    statut              VARCHAR(50) DEFAULT 'EN_COURS',
    ligne_gagnante      TEXT DEFAULT NULL,
    numero              INT DEFAULT NULL,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_coups (coups(255)),
    INDEX idx_coups_sym (coups_symetrique(255))
);
```

### Champs

| Champ | Type | Description |
|-------|------|-------------|
| `id` | INT | Identifiant unique auto-incrémenté |
| `coups` | VARCHAR(500) | Séquence des colonnes jouées |
| `coups_symetrique` | VARCHAR(500) | Séquence miroir (formule: 10-c) |
| `id_antecedent` | INT | ID de la partie précédente (chaînage) |
| `id_suivant` | INT | ID de la partie suivante (chaînage) |
| `mode_jeu` | VARCHAR(50) | 'PvP', 'PvAI', ou 'AIvsAI' |
| `statut` | VARCHAR(50) | 'EN_COURS', 'TERMINEE', 'ABANDONNEE' |
| `ligne_gagnante` | TEXT | Coordonnées de l'alignement gagnant (JSON) |
| `numero` | INT | Numéro optionnel de la partie |
| `created_at` | TIMESTAMP | Date/heure de création |

## 🔧 Gestion des Erreurs

Le module gère automatiquement :
- ✅ Erreurs de connexion MySQL
- ✅ Doublons (séquence ou symétrique)
- ✅ Transactions avec rollback automatique en cas d'erreur
- ✅ Fermeture propre des curseurs et connexions
- ✅ Logs détaillés pour le débogage

Toutes les méthodes incluent des blocs `try/except` avec gestion appropriée des erreurs.

## 📝 Exemple Complet

```python
from src.utils.db_manager import DatabaseManager

def example():
    # Initialisation
    db = DatabaseManager()
    
    if not db.connect():
        return
    
    db.create_tables()
    
    # Insertion de parties
    parties = [
        ('125', 'PvP', 'TERMINEE'),
        ('431', 'PvAI', 'TERMINEE'),
        ('777', 'AIvsAI', 'TERMINEE'),
    ]
    
    for coups, mode, statut in parties:
        game_id = db.insert_game(coups, mode_jeu=mode, statut=statut)
        print(f"Partie '{coups}' insérée (ID: {game_id})")
    
    # Tentative d'insertion d'un doublon symétrique
    # '985' est le symétrique de '125'
    db.insert_game('985', mode_jeu='PvP', statut='TERMINEE')  # Sera refusé
    
    # Récupération et affichage
    all_games = db.get_all_games()
    print(f"\nTotal: {len(all_games)} parties")
    
    for game in all_games:
        print(f"ID {game['id']}: {game['coups']} (sym: {game['coups_symetrique']})")
    
    # Fermeture
    db.disconnect()

if __name__ == "__main__":
    example()
```

## 🎯 Cas d'Usage

### Mode Replay
Utiliser le chaînage pour naviguer chronologiquement :
```python
current_game = db.get_game_by_id(5)

# Partie précédente
if current_game['id_antecedent']:
    prev = db.get_game_by_id(current_game['id_antecedent'])
    replay_game(prev['coups'])

# Partie suivante
if current_game['id_suivant']:
    next = db.get_game_by_id(current_game['id_suivant'])
    replay_game(next['coups'])
```

### Statistiques
```python
all_games = db.get_all_games()

# Par mode de jeu
pvp_count = sum(1 for g in all_games if g['mode_jeu'] == 'PvP')
pvai_count = sum(1 for g in all_games if g['mode_jeu'] == 'PvAI')

print(f"PvP: {pvp_count}, PvAI: {pvai_count}")
```

## 📞 Support

Pour toute question ou problème :
1. Vérifier que MySQL est bien démarré
2. Vérifier les identifiants dans `.env`
3. Consulter les logs de débogage `[DB_MANAGER DEBUG]`
4. Exécuter `test_database.py` pour diagnostiquer

## 📄 Licence

Projet éducatif - Connect Four / Puissance 4
