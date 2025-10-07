CREATE TABLE utilisateur (
    id SERIAL PRIMARY KEY,
    nom TEXT,
    prenom TEXT,
    date_naissance DATE,
    email TEXT NOT NULL UNIQUE,
    mot_de_passe TEXT NOT NULL,
    numero_telephone TEXT,
    sexe TEXT,
    avatar TEXT,
    avatar TEXT,
    role TEXT NOT NULL CHECK (role IN ('admin', 'utilisateur'))
);
 
CREATE TABLE ordonnance (
    id SERIAL PRIMARY KEY,
    utilisateur_id INTEGER NOT NULL,
    nom TEXT,
    date_ordonnance DATE NOT NULL,
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateur(id) ON DELETE CASCADE
);
 
CREATE TABLE medicaments (
    id SERIAL PRIMARY KEY,
    ordonnance_id INTEGER NOT NULL,
    nom TEXT,
    description_medicaments TEXT,
    dose TEXT,
    composant TEXT,
    frequence TEXT,
    frequence TEXT,
    FOREIGN KEY (ordonnance_id) REFERENCES ordonnance(id) ON DELETE CASCADE
);
 
CREATE TABLE allergies (
    id SERIAL PRIMARY KEY,
    utilisateur_id INTEGER NOT NULL,
    nom TEXT,
    description_allergie TEXT,
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateur(id) ON DELETE CASCADE
);
 
CREATE TABLE antecedent_medical (
    id SERIAL PRIMARY KEY,
    utilisateur_id INTEGER NOT NULL,
    description TEXT,
    nom TEXT,
    date_diagnostic DATE,
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateur(id) ON DELETE CASCADE
);
 
CREATE TABLE conversation (
    id SERIAL PRIMARY KEY,
    utilisateur_id INTEGER NOT NULL,
    titre TEXT,
    date_conversation DATE NOT NULL,
    date_derniere_activite DATE,
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateur(id) ON DELETE CASCADE
);
 
CREATE TABLE message (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL,
    contenu TEXT,
    role TEXT CHECK (role IN ('utilisateur', 'assistant')),
    timestamp DATE NOT NULL,
    FOREIGN KEY (conversation_id) REFERENCES conversation(id) ON DELETE CASCADE
);
 