"""
Script de test pour vérifier le format des coordonnées gagnantes en BDD.
"""

import json
from src.utils.db_manager import DatabaseManager

def test_winning_line_format():
    """Test le format des lignes gagnantes dans la base de données."""
    
    print("=" * 60)
    print("TEST FORMAT LIGNE GAGNANTE")
    print("=" * 60)
    
    # Connexion à la base
    db = DatabaseManager()
    db.connect()
    
    # Récupération de toutes les parties avec ligne gagnante
    parties = db.get_all_games()
    parties_avec_ligne = [p for p in parties if p['ligne_gagnante']]
    
    print(f"\n📊 Total parties: {len(parties)}")
    print(f"🎯 Parties avec ligne gagnante: {len(parties_avec_ligne)}")
    
    if not parties_avec_ligne:
        print("\n⚠️  Aucune partie avec ligne gagnante trouvée")
        db.disconnect()
        return
    
    # Analyse des 3 dernières parties
    print(f"\n{'='*60}")
    print("ANALYSE DES DERNIÈRES PARTIES")
    print(f"{'='*60}")
    
    for partie in parties_avec_ligne[-3:]:
        print(f"\n🎮 Partie ID: {partie['id']}")
        print(f"   Coups: {partie['coups']}")
        print(f"   Mode: {partie['mode_jeu']}")
        
        # Récupération de la chaîne brute
        ligne_brute = partie['ligne_gagnante']
        print(f"\n   📝 Ligne brute (type {type(ligne_brute).__name__}):")
        print(f"      {ligne_brute}")
        
        # Tentative de parsing JSON
        try:
            coords = json.loads(ligne_brute)
            print(f"\n   ✅ Parsing JSON réussi")
            print(f"      Type: {type(coords).__name__}")
            print(f"      Longueur: {len(coords)}")
            print(f"      Contenu: {coords}")
            
            # Analyse de chaque coordonnée
            print(f"\n   🔍 Analyse détaillée:")
            for i, coord in enumerate(coords):
                print(f"      [{i}] {coord} - Type: {type(coord).__name__}")
                if isinstance(coord, (list, tuple)) and len(coord) == 2:
                    row, col = coord[0], coord[1]
                    print(f"          row={row} (type {type(row).__name__}), col={col} (type {type(col).__name__})")
                    
                    # Vérification des limites (grille 8x9, Base 0)
                    if 0 <= row < 8 and 0 <= col < 9:
                        print(f"          ✅ Coordonnée valide pour grille 8x9")
                    else:
                        print(f"          ⚠️  HORS LIMITES pour grille 8x9!")
                else:
                    print(f"          ⚠️  Format invalide!")
        
        except json.JSONDecodeError as e:
            print(f"\n   ❌ Erreur parsing JSON: {e}")
            
            # Tentative avec ast.literal_eval
            import ast
            try:
                coords = ast.literal_eval(ligne_brute)
                print(f"   ✅ Parsing ast.literal_eval réussi: {coords}")
            except Exception as e2:
                print(f"   ❌ Erreur ast.literal_eval aussi: {e2}")
    
    db.disconnect()
    
    print(f"\n{'='*60}")
    print("FIN DU TEST")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    test_winning_line_format()
