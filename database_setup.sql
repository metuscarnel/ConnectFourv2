-- Script SQL de création de la base de données Connect Four
-- À exécuter dans MySQL pour initialiser la structure

-- Création de la base de données
CREATE DATABASE IF NOT EXISTS connect4 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- Utilisation de la base de données
USE connect4;

-- Création de la table games
CREATE TABLE IF NOT EXISTS games (
    -- Identifiant unique de la partie
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Séquence des coups joués (ex: '431256')
    coups VARCHAR(500) NOT NULL,
    
    -- Séquence symétrique calculée (ex: '679854' pour coups='431256')
    coups_symetrique VARCHAR(500) NOT NULL,
    
    -- Chaînage : ID de la partie précédente (tri par coups)
    id_antecedent INT DEFAULT NULL,
    
    -- Chaînage : ID de la partie suivante (tri par coups)
    id_suivant INT DEFAULT NULL,
    
    -- Mode de jeu : 'PvP', 'PvAI', 'AIvsAI'
    mode_jeu VARCHAR(50) DEFAULT 'PvP',
    
    -- Statut : 'EN_COURS', 'TERMINEE', 'ABANDONNEE'
    statut VARCHAR(50) DEFAULT 'EN_COURS',
    
    -- Coordonnées de l'alignement gagnant (format JSON)
    ligne_gagnante TEXT DEFAULT NULL,
    
    -- Numéro optionnel de la partie
    numero INT DEFAULT NULL,
    
    -- Date de création
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Index pour optimiser les recherches et le tri
    INDEX idx_coups (coups(255)),
    INDEX idx_coups_sym (coups_symetrique(255)),
    INDEX idx_created (created_at)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Note : Les clés étrangères sur id_antecedent et id_suivant ne sont pas ajoutées
-- car elles peuvent causer des problèmes lors de l'insertion de la première partie.
-- Le chaînage est géré par l'application.

-- Affichage de la structure
SHOW CREATE TABLE games;

-- Statistiques initiales
SELECT COUNT(*) AS total_parties FROM games;

SHOW TABLES;
