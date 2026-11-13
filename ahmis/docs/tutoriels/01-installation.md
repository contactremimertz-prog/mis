# 1. Installation et démarrage

## Prérequis

- **Python 3.10 ou plus récent** : [python.org/downloads](https://www.python.org/downloads/). Sous Windows, cochez « Add python.exe to PATH » pendant l'installation.
- Une connexion internet au premier lancement (téléchargement de Django).
- Aucun serveur de base de données : la démo utilise **SQLite**, un simple fichier (`db/ahmis.sqlite3`).

## Démarrer

**Windows** : double-cliquez sur `demarrer.bat`.

**macOS / Linux** : dans un terminal, depuis le dossier AHMIS :

```
./demarrer.sh
```

Au premier lancement, le script :

1. crée un environnement Python isolé (dossier `.venv`) ;
2. installe les dépendances (`requirements.txt`) ;
3. crée la base de données ;
4. charge les données de démonstration ;
5. ouvre le navigateur sur **http://127.0.0.1:8000**.

Les lancements suivants réutilisent la base existante : vos essais sont conservés.

**Arrêter** : fermez la fenêtre (Windows) ou faites `Ctrl+C` dans le terminal.

## Remettre la démo à zéro

- Windows : `reinitialiser_demo.bat`
- macOS / Linux : `./reinitialiser_demo.sh`

La base est vidée puis rechargée avec la situation de départ décrite au tutoriel 0.

> Les dates de la démo sont calculées à partir du jour du chargement. Si vous rouvrez la démo plusieurs semaines plus tard, les échéances auront « vieilli » : réinitialisez pour retrouver les situations décrites dans les tutoriels.

## Se connecter

La page de connexion affiche la liste des comptes de démonstration. Commencez avec `admin` / `Ahmis2026!` pour tout voir.

## Lancer les tests automatiques

Les règles métier (calcul des butées, signatures, contrôles de pose…) sont couvertes par des tests :

```
python manage.py test apps
```

(à lancer après avoir activé l'environnement : `.venv\Scripts\activate` sous Windows, `. .venv/bin/activate` sous macOS/Linux).

## En cas de problème

| Symptôme | Solution |
|---|---|
| « Python 3.10+ est requis » | Installer Python puis relancer le script |
| Le port 8000 est occupé | Lancer `python manage.py runserver 127.0.0.1:8001` et ouvrir http://127.0.0.1:8001 |
| Page « Erreur de serveur » | Relancer ; si cela persiste, réinitialiser la démo |
