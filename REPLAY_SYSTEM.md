# 🎬 Système de Replay et Navigation - Documentation

## ✅ Fonctionnalités Implémentées

### 1. **Nouvel État : HISTORY_MENU**
Écran d'historique accessible depuis le menu principal.

#### Affichage
- **Liste des parties** : Récupération via `db.get_all_games(order_by='coups')`
- **Tri lexicographique** : Parties ordonnées par séquence de coups
- **Informations affichées** :
  - ID et date de création
  - Séquence de coups (tronquée si > 20 caractères)
  - Mode de jeu (PvP, PvAI, AIvsAI)
- **Limite** : 10 parties visibles simultanément

#### Navigation
- Clic sur une partie → Entre en **REPLAY_MODE**
- Bouton **RETOUR** → Retour au **MENU**
- Touche **ECHAP** → Retour au **MENU**

---

### 2. **Mode REPLAY_MODE : Visualisation Pas-à-Pas**

#### Interface
**Panneau latéral droit (300px)** contenant :
- **Titre** : "MODE REPLAY" ou "MODE MIROIR"
- **Informations** :
  - ID de la partie
  - Mode de jeu
  - Progression : `Coups: X/Y`
- **Instructions clavier** :
  - `[←]` Coup précédent
  - `[→]` Coup suivant
  - `[Espace]` Lecture automatique
  - `[M]` Basculer vers symétrie
  - `[Echap]` Retour historique

#### Contrôles Clavier
```python
← (Flèche Gauche)  : Annule le dernier coup (undo)
→ (Flèche Droite)  : Joue le coup suivant
M                   : Bascule entre coups / coups_symetrique
ESPACE              : Active/désactive la lecture auto (500ms/coup)
ECHAP               : Retour à l'historique
```

---

### 3. **Navigation Chaînée entre Parties**

#### Boutons de Navigation
**Bouton PRÉCÉDENT** (← PRÉCÉDENT)
- Couleur : Vert (actif) / Gris (désactivé)
- Action : Charge la partie `id_antecedent`
- État : Désactivé si `id_antecedent == NULL`

**Bouton SUIVANT** (SUIVANT →)
- Couleur : Vert (actif) / Gris (désactivé)
- Action : Charge la partie `id_suivant`
- État : Désactivé si `id_suivant == NULL`

#### Algorithme de Chargement
```python
def _load_neighbor_game(direction):
    # 1. Récupération de l'ID voisin
    neighbor_id = game_data['id_antecedent'] ou game_data['id_suivant']
    
    # 2. Chargement depuis MySQL
    db.get_game_by_id(neighbor_id)
    
    # 3. Réinitialisation du plateau
    _load_replay(neighbor_game)
    
    # 4. Mise à jour de l'interface
```

---

### 4. **Bouton VOIR SYMÉTRIE**

#### Fonctionnement
- **Icône** : ⇄ VOIR SYMÉTRIE
- **Couleur** : Violet (mode miroir) / Bleu (mode normal)
- **Action** : Bascule entre `coups` et `coups_symetrique`

#### Algorithme
```python
def _toggle_symmetric():
    # 1. Inversion du flag
    show_symmetric = not show_symmetric
    
    # 2. Récupération de la séquence
    coups = game['coups_symetrique'] if show_symmetric else game['coups']
    
    # 3. Réinitialisation du plateau
    replay_board = Board()
    
    # 4. Rejeu des coups jusqu'à la position actuelle
    for i in range(current_move):
        _replay_play_move(moves[i])
```

#### Transformation Visuelle
```
Exemple : Plateau 9 colonnes
Colonne normale : 4 → Colonne symétrique : 6
Formule : 10 - colonne
```

---

### 5. **Visualisation de la Ligne Gagnante**

#### Affichage Final
Quand `current_move == total_moves` :
- **Parsing JSON** : `ligne_gagnante` → Liste de coordonnées
- **Surbrillance** : Contours dorés avec `draw_winning_highlight()`
- **Exemple** : `[[0,4],[1,4],[2,4],[3,4]]` → 4 pions verticaux

---

## 🎯 Flux d'Utilisation

### Scénario Complet
```
1. MENU PRINCIPAL
   ↓ Clic sur "Historique"
   
2. HISTORY_MENU
   ↓ Sélection de "Partie #9"
   
3. REPLAY_MODE (Partie #9)
   - Coup 0/10
   ↓ Flèche DROITE (5 fois)
   - Coup 5/10
   ↓ Clic "SUIVANT"
   
4. REPLAY_MODE (Partie #11)
   - Coup 0/56
   ↓ Touche M
   
5. MODE MIROIR (coups_symetrique)
   - Plateau inversé horizontalement
   ↓ ESPACE
   
6. LECTURE AUTO
   - Animation automatique jusqu'à la fin
   - Affichage ligne gagnante
```

---

## 📊 Structure des Données

### Données de Replay
```python
replay_game_data = {
    'id': 9,
    'coups': '4544565545',
    'coups_symetrique': '6566545565',
    'id_antecedent': 10,
    'id_suivant': 11,
    'mode_jeu': 'PvP',
    'statut': 'TERMINEE',
    'ligne_gagnante': '[[0,4],[1,4],[2,4],[3,4]]',
    'created_at': '2026-01-30 14:02:14'
}
```

### Variables d'État
```python
self.replay_board         # Plateau actuel du replay
self.replay_current_move  # Position actuelle (0-indexed)
self.replay_show_symmetric # True = affichage symétrique
self.replay_auto_play     # True = lecture automatique
```

---

## 🔧 Méthodes Clés

### Controller (game_controller.py)
```python
run_history_menu()        # Affiche la liste des parties
run_replay_mode()         # Mode visualisation avec navigation
_load_replay(game_data)   # Charge une partie pour replay
_replay_play_move(col)    # Joue un coup dans le replay
_replay_undo_move()       # Annule le dernier coup
_toggle_symmetric()       # Bascule normal/symétrique
_load_neighbor_game(dir)  # Charge partie précédente/suivante
```

### View (pygame_view.py)
```python
draw_history_menu(games)              # Liste des parties
draw_replay_interface(...)            # Interface de replay
draw_winning_highlight(line, board)   # Surbrillance victoire
```

---

## 🎨 Design Visuel

### Couleurs
- **Fond historique** : Noir
- **Titre** : Or (255, 215, 0)
- **Parties sélectionnables** : Fond gris (40, 40, 40) + Bordure bleue
- **Panneau replay** : Fond gris foncé (30, 30, 30) + Bordure or
- **Bouton PRÉCÉDENT/SUIVANT** : Vert (actif) / Gris (inactif)
- **Bouton SYMÉTRIE** : Violet (miroir) / Bleu (normal)
- **Bouton RETOUR** : Rouge foncé

### Dimensions
- **Panneau latéral** : 300px de largeur
- **Boutons navigation** : 130x50px
- **Bouton symétrie** : 270x50px (pleine largeur)
- **Parties affichées** : 10 maximum

---

## 🐛 Gestion d'Erreurs

### Cas Limites Gérés
```python
# Pas de partie antécédente/suivante
if id_antecedent is None:
    button_disabled = True

# Ligne gagnante invalide
try:
    winning_line = json.loads(ligne_gagnante)
except:
    pass  # Pas de surbrillance

# Base de données vide
if len(games) == 0:
    # Message "Aucune partie enregistrée"

# Déconnexion MySQL
connection.ping(reconnect=True)
```

---

## 📝 Notes Techniques

### Performance
- **Lecture DB** : Requête unique avec ORDER BY indexé
- **Rejeu coups** : O(n) où n = nombre de coups
- **Symétrie** : Recalcul complet du plateau (acceptable < 100 coups)

### Compatibilité
- **Plateaux variables** : Gère 6x7, 8x9, etc.
- **Formule symétrie** : `(cols + 1) - colonne` (adaptatif)

### Améliorations Futures
- Pagination (au-delà de 10 parties)
- Recherche/filtrage par mode ou date
- Export vidéo du replay
- Statistiques de parties
