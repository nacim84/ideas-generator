# Daily Business Ideas Generation

**Objectif :** Collecter les discussions récentes sur Reddit, identifier des opportunités de business avec Gemini, et envoyer un rapport par email.

**Fréquence :** Quotidienne (ou à la demande).

**Pré-requis :**
- Clé API Gemini configurée dans `.env` (`GEMINI_API_KEY`).
- Identifiants Gmail (`credentials.json`, `token.json`) à la racine.
- Email de destination configuré dans `.env` (`RECIPIENT_EMAIL`).

---

## Procédure

### Étape 1 : Collecte de Données
Exécuter le script de collecte pour récupérer les derniers posts des subreddits configurés.
```bash
python execution/reddit_analyzer/collector.py
```
*Sortie attendue :* "Saved X new posts."

### Étape 2 : Analyse Gemini
Utiliser l'IA pour analyser les posts des dernières 24h et extraire 5 idées clés.
```bash
python execution/reddit_analyzer/analyze_ideas.py
```
*Sortie attendue :* Affichage du rapport dans le terminal et création du fichier `latest_analysis.md`.

### Étape 3 : Envoi du Rapport
Envoyer le rapport généré par email.
```bash
python execution/reddit_analyzer/send_email.py
```
*Sortie attendue :* "Message Id: ... sent successfully."

---

## En cas d'erreur
- **Erreur API Reddit (429) :** Attendre quelques minutes. Le script a déjà un délai (`time.sleep`) entre les requêtes.
- **Erreur Gemini :** Vérifier les quotas et la clé API dans `.env`.
- **Erreur Gmail :** Si le token est expiré, supprimer `token.json` et relancer le script pour régénérer l'authentification.
