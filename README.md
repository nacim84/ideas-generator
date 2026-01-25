# Ideas Generator 🚀

**Générateur automatisé d'opportunités business alimenté par l'IA et la veille communautaire.**

Ce projet surveille en continu des communautés ciblées sur Reddit (SaaS, Entrepreneur, Startups, etc.), analyse les discussions à l'aide de Google Gemini pour détecter des "Pain Points" et des tendances émergentes, et envoie un rapport d'idées concrètes par email quotidiennement.

---

## ✨ Fonctionnalités

- **📡 Veille Multi-Canal :** Scrape automatiquement des dizaines de subreddits configurables.
- **🧠 Analyse IA Avancée :** Utilise Google Gemini (Flash) pour synthétiser des centaines de posts en idées business actionnables.
- **📂 Segmentation Intelligente :** Classe les rapports par catégories (ex: *Tech Startups*, *B2B Market*, *Direct Demand*) pour une lecture ciblée.
- **📧 Rapports Quotidiens :** Envoi automatique d'emails formatés en HTML avec un résumé exécutif et le top 5 des opportunités du jour.
- **🎙️ Production de Podcasts :** Génère automatiquement des épisodes de podcast audio (qualité studio) à partir des analyses, avec plusieurs voix, musique et post-production.
- **⚡ Architecture CI/CD :** Entièrement automatisé via GitHub Actions avec exécution parallèle des catégories (Matrix Strategy).
- **🇫🇷 Localisation :** Rapports générés et formatés en Français.

---

## 🏗️ Architecture

Ce projet suit une **architecture à 3 couches** pour maximiser la fiabilité et la maintenance :

1.  **Couche Directive (`directives/`)** : Instructions en langage naturel (SOP) définissant *quoi* faire.
2.  **Couche Orchestration** : L'agent (ou le CI/CD) qui lit les directives et appelle les outils.
3.  **Couche Exécution (`execution/`)** : Scripts Python déterministes et isolés qui font le travail réel (collecte, analyse, envoi).

---

## 🛠️ Installation et Configuration

### Pré-requis
- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** (Gestionnaire de paquets Python ultra-rapide)
- Un compte **Google Cloud** (pour l'API Gemini et Gmail)
- Un compte **OpenAI** (pour l'API TTS)

### 1. Clonage et Dépendances
```bash
git clone https://github.com/votre-user/ideas-generator.git
cd ideas-generator/execution/reddit_analyzer
uv sync
```

### 2. Configuration des Secrets
Créez un fichier `.env` à la racine du projet :
```ini
GEMINI_API_KEY=votre_cle_api_gemini
OPENAI_API_KEY=votre_cle_api_openai
RECIPIENT_EMAIL=votre_email@destinataire.com
```

### 3. Authentification Gmail
Pour l'envoi d'emails, le projet nécessite des identifiants OAuth2 :
1.  Placez votre fichier `credentials.json` (téléchargé depuis Google Cloud Console) dans `execution/reddit_analyzer/`.
2.  Lors de la première exécution locale (`uv run send_email.py`), une fenêtre s'ouvrira pour vous connecter. Cela générera un fichier `token.json`.

---

## ⚙️ Personnalisation

Le cœur du moteur est configuré dans `execution/reddit_analyzer/config.json`. Vous pouvez ajouter ou modifier des sources :

```json
{
  "subreddits": [
    {
      "name": "SaaS",
      "category": "B2B_MARKET",
      "weight": 9,
      "description": "Discussions fondateurs SaaS"
    },
    {
      "name": "SomebodyMakeThis",
      "category": "DIRECT_DEMAND",
      "weight": 10,
      "description": "Demandes explicites de produits"
    }
  ],
  "db_name": "reddit_ideas.db"
}
```
*Le système groupera automatiquement les analyses par `category`.*

---

## 🚀 Utilisation

### Mode Manuel (Local)
Placez-vous dans `execution/reddit_analyzer/` :

1.  **Collecter les données :**
    ```bash
    uv run collector.py
    ```
2.  **Analyser une catégorie spécifique :**
    ```bash
    uv run analyze_ideas.py --category "B2B_MARKET"
    ```
3.  **Envoyer le rapport :**
    ```bash
    uv run send_email.py --category "B2B_MARKET"
    ```

### Mode Podcast (Local)
Le système peut générer un podcast audio à partir des idées analysées. La configuration avancée se trouve dans `podcast_config_advanced.json`.

1.  **Générer le script du podcast :**
    ```bash
    uv run generate_podcast_script.py --category "B2B_MARKET"
    ```
2.  **Segmenter le script pour le TTS :**
    ```bash
    uv run semantic_segmentation.py --script "scripts/podcast_script_B2B_MARKET_YYYYMMDD.json"
    ```
3.  **Synthétiser les segments audio :**
    ```bash
    uv run synthesize_podcast_audio.py --segments "segments_B2B_MARKET_YYYYMMDD.json"
    ```
4.  **Post-production et mixage final :**
    ```bash
    uv run audio_postproduction.py --raw-audio "audio/raw/" --output "episodes/"
    ```

### Mode Automatique (GitHub Actions)
Le workflow `.github/workflows/daily_ideas.yml` s'exécute **tous les jours à 08:00 UTC**.
Il détecte automatiquement les catégories présentes dans `config.json` et lance des jobs parallèles pour analyser, envoyer les rapports et générer les podcasts.

---

## 📂 Structure des Dossiers

```
.
├── .github/workflows/   # Workflows CI/CD (Automatisation)
├── directives/          # Procédures (Documentation pour l'Agent)
├── execution/
│   └── reddit_analyzer/ # Le code source Python
│       ├── config.json  # Configuration des sources
│       ├── podcast_config_advanced.json # Configuration avancée du podcast
│       ├── main.py      # Point d'entrée
│       ├── collector.py # Scraper RSS Reddit
│       ├── analyze_ideas.py # Moteur IA (Gemini)
│       ├── generate_podcast_script.py # Générateur de scénario podcast
│       ├── synthesize_podcast_audio.py # Moteur TTS
│       ├── audio_postproduction.py # Mixage et mastering audio
│       └── send_email.py # Gestionnaire d'envoi SMTP/Gmail
└── README.md
```