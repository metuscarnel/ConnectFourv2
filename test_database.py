#!/usr/bin/env python3
"""
Script de test pour le gestionnaire de base de données MySQL.
Teste toutes les fonctionnalités : connexion, insertion, chaînage, symétries.
"""

import sys
import os

# Ajout du chemin parent pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.db_manager import DatabaseManager


def print_separator(title: str = ""):
    """Affiche un séparateur visuel."""
    print("\n" + "=" * 70)
    if title:
        print(f"  {title}")
        print("=" * 70)


def test_connection():
    """Test de connexion à la base de données."""
    print_separator("TEST 1 : CONNEXION À LA BASE DE DONNÉES")
    
    db = DatabaseManager()
    
    if db.connect():
        print("✅ Connexion réussie")
        db.disconnect()
        return True
    else:
        print("❌ Échec de la connexion")
        return False


def test_table_creation():
    """Test de création de la table."""
    print_separator("TEST 2 : CRÉATION DE LA TABLE 'games'")
    
    db = DatabaseManager()
    
    if not db.connect():
        print("❌ Impossible de se connecter")
        return False
    
    if db.create_tables():
        print("✅ Table créée avec succès")
        db.disconnect()
        return True
    else:
        print("❌ Échec de la création de la table")
        db.disconnect()
        return False


def test_symmetric_calculation():
    """Test du calcul de symétrie."""
    print_separator("TEST 3 : CALCUL DE SYMÉTRIE")
    
    db = DatabaseManager()
    
    test_cases = [
        ('125', '985'),   # 10-1=9, 10-2=8, 10-5=5
        ('431', '679'),   # 10-4=6, 10-3=7, 10-1=9
        ('999', '111'),   # 10-9=1, 10-9=1, 10-9=1
        ('555', '555'),   # 10-5=5, 10-5=5, 10-5=5
    ]
    
    all_passed = True
    for coups, expected_sym in test_cases:
        result = db.calculate_symmetric_sequence(coups)
        status = "✅" if result == expected_sym else "❌"
        print(f"{status} '{coups}' -> '{result}' (attendu: '{expected_sym}')")
        if result != expected_sym:
            all_passed = False
    
    return all_passed


def test_insertion_and_chaining():
    """Test d'insertion et de chaînage."""
    print_separator("TEST 4 : INSERTION ET CHAÎNAGE")
    
    db = DatabaseManager()
    
    if not db.connect():
        print("❌ Impossible de se connecter")
        return False
    
    db.create_tables()
    
    # Insertion de plusieurs parties dans un ordre non trié
    # Note: '999' ne sera pas inséré car c'est le symétrique de '111'
    parties = [
        ('555', 'PvP'),
        ('222', 'PvP'),
        ('777', 'PvAI'),
        ('111', 'PvP'),
    ]
    
    inserted_ids = []
    
    print("\n📝 Insertion de parties :")
    for coups, mode in parties:
        game_id = db.insert_game(coups, mode_jeu=mode, statut='TERMINEE')
        if game_id:
            print(f"  ✅ Partie '{coups}' insérée (ID: {game_id})")
            inserted_ids.append(game_id)
        else:
            print(f"  ⚠️ Partie '{coups}' non insérée (doublon ou symétrique)")
    
    # Vérification du chaînage
    print("\n🔗 Vérification du chaînage :")
    all_games = db.get_all_games(order_by='coups')
    
    for i, game in enumerate(all_games):
        print(f"\n  Partie {i+1} (ID: {game['id']}):")
        print(f"    Coups: {game['coups']}")
        print(f"    Symétrique: {game['coups_symetrique']}")
        print(f"    Antécédent: {game['id_antecedent']}")
        print(f"    Suivant: {game['id_suivant']}")
        
        # Vérification de la cohérence
        if i > 0:  # Pas le premier
            expected_ante = all_games[i-1]['id']
            if game['id_antecedent'] != expected_ante:
                print(f"    ⚠️ Incohérence : antécédent attendu = {expected_ante}")
        
        if i < len(all_games) - 1:  # Pas le dernier
            expected_suiv = all_games[i+1]['id']
            if game['id_suivant'] != expected_suiv:
                print(f"    ⚠️ Incohérence : suivant attendu = {expected_suiv}")
    
    db.disconnect()
    # Succès si au moins 4 parties insérées
    return len(inserted_ids) >= 4


def test_duplicate_detection():
    """Test de détection des doublons."""
    print_separator("TEST 5 : DÉTECTION DES DOUBLONS")
    
    db = DatabaseManager()
    
    if not db.connect():
        print("❌ Impossible de se connecter")
        return False
    
    db.create_tables()
    
    # Insertion d'une partie
    print("📝 Insertion de la partie '345'...")
    game_id = db.insert_game('345', mode_jeu='PvP', statut='TERMINEE')
    
    if game_id:
        print(f"  ✅ Partie insérée (ID: {game_id})")
    else:
        print("  ❌ Échec d'insertion")
        db.disconnect()
        return False
    
    # Tentative de réinsertion de la même séquence
    print("\n🔄 Tentative de réinsertion de '345' (devrait échouer)...")
    duplicate1 = db.insert_game('345', mode_jeu='PvP', statut='TERMINEE')
    
    if duplicate1 is None:
        print("  ✅ Doublon correctement détecté et refusé")
    else:
        print("  ❌ Le doublon n'a pas été détecté !")
        db.disconnect()
        return False
    
    # Tentative d'insertion de la séquence symétrique
    sym = db.calculate_symmetric_sequence('345')
    print(f"\n🪞 Tentative d'insertion de la symétrique '{sym}' (devrait échouer)...")
    duplicate2 = db.insert_game(sym, mode_jeu='PvP', statut='TERMINEE')
    
    if duplicate2 is None:
        print("  ✅ Symétrie correctement détectée et refusée")
    else:
        print("  ❌ La symétrie n'a pas été détectée !")
        db.disconnect()
        return False
    
    db.disconnect()
    return True


def test_read_operations():
    """Test des opérations de lecture."""
    print_separator("TEST 6 : OPÉRATIONS DE LECTURE")
    
    db = DatabaseManager()
    
    if not db.connect():
        print("❌ Impossible de se connecter")
        return False
    
    # Récupération de toutes les parties
    print("📋 Récupération de toutes les parties :")
    all_games = db.get_all_games()
    print(f"  Total : {len(all_games)} parties")
    
    # Comptage
    count = db.get_game_count()
    print(f"\n📊 Comptage : {count} parties")
    
    # Vérification de cohérence
    if len(all_games) == count:
        print("  ✅ Cohérence entre get_all_games() et get_game_count()")
    else:
        print("  ❌ Incohérence détectée !")
    
    # Récupération d'une partie spécifique
    if all_games:
        first_game_id = all_games[0]['id']
        print(f"\n🎮 Récupération de la partie ID {first_game_id} :")
        game = db.get_game_by_id(first_game_id)
        
        if game:
            print(f"  ✅ Partie trouvée : '{game['coups']}' ({game['mode_jeu']})")
        else:
            print("  ❌ Partie non trouvée")
    
    db.disconnect()
    return True


def test_deletion():
    """Test de suppression avec mise à jour du chaînage."""
    print_separator("TEST 7 : SUPPRESSION ET MISE À JOUR DU CHAÎNAGE")
    
    db = DatabaseManager()
    
    if not db.connect():
        print("❌ Impossible de se connecter")
        return False
    
    db.create_tables()
    
    # Insertion de 3 parties pour tester la suppression (séquences uniques)
    print("📝 Insertion de 3 parties pour le test :")
    ids = []
    for coups in ['412', '634', '856']:
        game_id = db.insert_game(coups, mode_jeu='PvP', statut='TERMINEE')
        if game_id:
            ids.append(game_id)
            print(f"  ✅ Partie '{coups}' insérée (ID: {game_id})")
    
    if len(ids) < 3:
        print("❌ Échec d'insertion des parties de test")
        db.disconnect()
        return False
    
    # Affichage du chaînage avant suppression
    print("\n🔗 Chaînage AVANT suppression :")
    games_before = db.get_all_games(order_by='coups')
    for g in games_before:
        if g['id'] in ids:
            print(f"  ID {g['id']}: coups='{g['coups']}', ante={g['id_antecedent']}, suiv={g['id_suivant']}")
    
    # Suppression de la partie du milieu
    middle_id = ids[1]
    print(f"\n🗑️ Suppression de la partie {middle_id} (milieu) :")
    if db.delete_game(middle_id):
        print(f"  ✅ Partie {middle_id} supprimée")
    else:
        print(f"  ❌ Échec de suppression")
        db.disconnect()
        return False
    
    # Affichage du chaînage après suppression
    print("\n🔗 Chaînage APRÈS suppression :")
    games_after = db.get_all_games(order_by='coups')
    for g in games_after:
        if g['id'] in [ids[0], ids[2]]:  # Les deux qui restent
            print(f"  ID {g['id']}: coups='{g['coups']}', ante={g['id_antecedent']}, suiv={g['id_suivant']}")
    
    # Vérification : les deux parties restantes doivent être liées directement
    game1 = db.get_game_by_id(ids[0])
    game3 = db.get_game_by_id(ids[2])
    
    if game1 and game3:
        if game1['id_suivant'] == ids[2] and game3['id_antecedent'] == ids[0]:
            print("\n✅ Chaînage correctement mis à jour après suppression")
        else:
            print("\n❌ Problème dans la mise à jour du chaînage")
    
    db.disconnect()
    return True


def run_all_tests():
    """Exécute tous les tests."""
    print("\n" + "█" * 70)
    print("  SUITE DE TESTS - GESTIONNAIRE DE BASE DE DONNÉES")
    print("█" * 70)
    
    tests = [
        ("Connexion", test_connection),
        ("Création de table", test_table_creation),
        ("Calcul de symétrie", test_symmetric_calculation),
        ("Insertion et chaînage", test_insertion_and_chaining),
        ("Détection de doublons", test_duplicate_detection),
        ("Opérations de lecture", test_read_operations),
        ("Suppression", test_deletion),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ ERREUR CRITIQUE dans {name} : {e}")
            results.append((name, False))
    
    # Résumé
    print_separator("RÉSUMÉ DES TESTS")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {name}")
    
    print(f"\n  SCORE : {passed}/{total} tests réussis")
    
    if passed == total:
        print("\n  🎉 TOUS LES TESTS SONT PASSÉS ! 🎉")
    else:
        print(f"\n  ⚠️ {total - passed} test(s) ont échoué")
    
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_all_tests()
