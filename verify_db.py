#!/usr/bin/env python3
"""
Script de vérification de la base de données.
Affiche toutes les parties enregistrées avec leurs détails.
"""

import sys
import os
# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.db_manager import DatabaseManager
import json

def main():
    print("\n" + "="*70)
    print("  VÉRIFICATION DE LA BASE DE DONNÉES MYSQL")
    print("="*70)
    
    # Connexion
    db = DatabaseManager()
    db.connect()
    
    # Récupération des parties
    parties = db.get_all_games(order_by='id')
    
    print(f"\n📊 Nombre total de parties : {len(parties)}")
    
    if len(parties) == 0:
        print("\n⚠️  Aucune partie enregistrée dans la base de données.")
    else:
        print("\n" + "-"*70)
        print("  LISTE DES PARTIES")
        print("-"*70)
        
        for p in parties:
            print(f"\n🎮 Partie #{p['id']} ({p['created_at']})")
            print(f"   Coups        : {p['coups']}")
            print(f"   Symétrique   : {p['coups_symetrique']}")
            print(f"   Mode         : {p['mode_jeu']}")
            print(f"   Statut       : {p['statut']}")
            print(f"   Antécédent   : {p['id_antecedent']}")
            print(f"   Suivant      : {p['id_suivant']}")
            
            if p['ligne_gagnante']:
                try:
                    ligne = json.loads(p['ligne_gagnante'])
                    print(f"   Ligne gagnante: {ligne}")
                except:
                    print(f"   Ligne gagnante: {p['ligne_gagnante']}")
    
    # Vérification du chaînage
    print("\n" + "-"*70)
    print("  VÉRIFICATION DU CHAÎNAGE")
    print("-"*70)
    
    chaine = []
    current_id = None
    
    # Trouver le début de la chaîne (partie sans antécédent)
    for p in parties:
        if p['id_antecedent'] is None:
            current_id = p['id']
            break
    
    if current_id:
        visited = set()
        while current_id and current_id not in visited:
            visited.add(current_id)
            partie = next((p for p in parties if p['id'] == current_id), None)
            if partie:
                chaine.append(f"{partie['id']}({partie['coups']})")
                current_id = partie['id_suivant']
            else:
                break
        
        print(f"\n🔗 Chaîne complète ({len(chaine)} parties) :")
        print("   " + " → ".join(chaine))
    
    db.disconnect()
    
    print("\n" + "="*70)
    print("  FIN DE LA VÉRIFICATION")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
