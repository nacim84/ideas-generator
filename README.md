# Ideas Generator

Ce projet suit une architecture à 3 couches pour la génération d'idées, comme décrit dans [AGENTS.md](AGENTS.md).

## Structure

- **`directives/`** : Procédures Opérationnelles Standard (SOP) en Markdown. (Couche 1)
- **`execution/`** : Scripts Python déterministes. (Couche 3)
- **`.tmp/`** : Fichiers intermédiaires et temporaires.
- **`.env`** : Variables d'environnement.

## Utilisation

L'agent (Couche 2) orchestre le flux en lisant les directives et en exécutant les scripts appropriés.
