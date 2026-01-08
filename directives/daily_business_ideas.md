# Daily Business Ideas Generation

**Objectif :** Collecter les discussions récentes sur Reddit, identifier des opportunités de business avec Gemini, et envoyer un rapport par email.

**Fréquence :** Quotidienne via GitHub Actions (08:00 UTC) ou à la demande.

**Pré-requis :**
- [uv](https://docs.astral.sh/uv/) installé localement.
- Clé API Gemini configurée dans `.env` (`GEMINI_API_KEY`).
- Identifiants Gmail (`credentials.json`, `token.json`) dans `execution/reddit_analyzer/`.
- Email de destination configuré dans `.env` (`RECIPIENT_EMAIL`).

---

## Procédure

Se placer dans le répertoire de l'outil avant d'exécuter les commandes :
```bash
cd execution/reddit_analyzer
```

### Étape 1 : Collecte de Données
Exécuter le script de collecte pour récupérer les derniers posts des subreddits configurés.
```bash
uv run collector.py
```
*Sortie attendue :* "Saved X new posts."

### Étape 2 : Analyse Gemini
Utiliser l'IA pour analyser les posts des dernières 24h et extraire des idées clés.
```bash
uv run analyze_ideas.py
```
*Sortie attendue :* Création du fichier `latest_analysis.md`.

### Étape 3 : Envoi du Rapport
Envoyer le rapport généré par email.
```bash
uv run send_email.py
```
*Sortie attendue :* "Email sent successfully."

---

## Maintenance et CI/CD

### GitHub Actions
Le projet utilise un workflow automatisé (`.github/workflows/daily_ideas.yml`). 
En cas d'erreur "Binary not found" ou "uv not found" dans le CI, vérifier que l'action `astral-sh/setup-uv` est utilisée.

## En cas d'erreur
- **Erreur API Reddit (429) :** Attendre quelques minutes. Le script gère déjà certains délais.
- **Erreur Gemini :** Vérifier les quotas et la validité de la clé API dans le fichier `.env`.
- **Erreur Gmail :** Si le `token.json` est expiré ou invalide localement, le supprimer et relancer `send_email.py` pour provoquer une nouvelle authentification. Pour le CI, s'assurer que le secret `GMAIL_TOKEN_JSON` est à jour.