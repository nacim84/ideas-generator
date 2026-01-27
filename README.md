# Ideas Generator 🚀

**Générateur automatisé d'opportunités business alimenté par l'IA et la veille communautaire.**

Ce projet surveille en continu des communautés ciblées sur Reddit (SaaS, Entrepreneur, Startups, etc.), analyse les discussions à l'aide de Google Gemini pour détecter des "Pain Points" et des tendances émergentes, et envoie un rapport d'idées concrètes par email quotidiennement. Le système inclut également une production automatisée de podcasts de qualité broadcast.

---

## ✨ Fonctionnalités

- **📡 Veille Multi-Canal :** Scrape automatiquement des dizaines de subreddits configurables via RSS/Reddit API
- **🧠 Analyse IA Avancée :** Utilise Google Gemini (Flash) pour synthétiser des centaines de posts en idées business actionnables
- **📂 Segmentation Intelligente :** Classe les rapports par catégories (ex: *B2B_MARKET*, *PAIN_POINTS*, *DIRECT_DEMAND*) pour une lecture ciblée
- **📧 Rapports Quotidiens :** Envoi automatique d'emails formatés en HTML avec un résumé exécutif et le top 5 des opportunités du jour
- **🎙️ Production de Podcasts :** Génère automatiquement des épisodes audio professionnels (10 min) avec :
  - Multi-speaker diarisation (HOST, EXPERT, GUEST)
  - Voix TTS-1-HD d'OpenAI (onyx, shimmer, nova)
  - Post-production audio avec ducking et mastering
  - Intros/outros musicaux et effets sonores
- **⚡ Architecture CI/CD :** Entièrement automatisé via GitHub Actions avec exécution parallèle des catégories (Matrix Strategy)
- **🇫🇷 Localisation :** Rapports générés et formatés en Français
- **💰 Monitoring Coûts :** Suivi et alertes automatisés des dépenses API

---

## 🏗️ Architecture

Ce projet suit une **architecture à 3 couches** pour maximiser la fiabilité et la maintenance :

1.  **Couche Directive (`directives/`)** : Instructions en langage naturel (SOP) définissant *quoi* faire
2.  **Couche Orchestration** : L'agent (ou le CI/CD) qui lit les directives et appelle les outils
3.  **Couche Exécution (`execution/reddit_analyzer/`)** : Scripts Python déterministes et isolés qui font le travail réel

### Pipeline Complet
```
Reddit RSS → Collecte → Base SQLite → Analyse Gemini → Rapport Email/Markdown → 
Script Podcast → Segmentation NLTK → TTS Multi-Speaker → Post-Production → Épisode MP3
```

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
uv add -r requirements-audio.txt  # Dépendances audio pour podcast
```

### 2. Configuration des Secrets
Copiez le template de configuration :
```bash
cp .env.example .env
```

Éditez le fichier `.env` avec vos valeurs :
```ini
# API Keys
GEMINI_API_KEY=votre_cle_api_gemini
OPENAI_API_KEY=votre_cle_api_openai

# Email Configuration
RECIPIENT_EMAIL=votre_email@destinataire.com

# Podcast Settings (optionnel)
PODCAST_TITLE="Idées Business Quotidiennes"
PODCAST_DESCRIPTION="Analyses quotidiennes des opportunités business..."

# Cost Management
MAX_MONTHLY_COST_USD=100.0
ENABLE_COST_ALERTS=true
```

### 3. Authentification Gmail
Pour l'envoi d'emails, le projet nécessite des identifiants OAuth2 :
1. Allez sur [Google Cloud Console](https://console.cloud.google.com/)
2. Créez un nouveau projet et activez l'API "Gmail API"
3. Allez dans "Credentials" > "Create Credentials" > "OAuth client ID"
4. Sélectionnez "Desktop app" et téléchargez `credentials.json`
5. Placez le fichier dans `execution/reddit_analyzer/credentials.json`
6. Exécutez `uv run send_email.py` en local pour générer `token.json`

### 4. Configuration GitHub Actions (Optionnel)
Pour le déploiement en production, ajoutez ces secrets dans votre repository GitHub :

```bash
# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Email Configuration
RECIPIENT_EMAIL=your_email@destination.com
GMAIL_CREDENTIALS_JSON=$(base64 execution/reddit_analyzer/credentials.json)
GMAIL_TOKEN_JSON=$(base64 execution/reddit_analyzer/token.json)

# Podcast Configuration
PODCAST_CONFIG_ADVANCED_JSON=$(base64 execution/reddit_analyzer/podcast_config_advanced.json)
```

### 5. Dépendances du Système
**Pour l'audio post-production (Linux/macOS) :**
```bash
# Installation des dépendances système
sudo apt-get install ffmpeg libsox-dev sox  # Debian/Ubuntu
# ou
brew install ffmpeg sox  # macOS
```

**Pour l'audio post-production (Windows) :**
Téléchargez et installez [FFmpeg](https://ffmpeg.org/download.html) et ajoutez-le au PATH.

---

## 📊 Coûts Estimés

| Service | Coût Mensuel | Notes |
|---------|-------------|-------|
| **Google Gemini API** | $10-20 | Analyse des idées business |
| **OpenAI TTS-1-HD** | $450-900 | Selon nombre d'épisodes |
| **TOTAL ESTIMÉ** | **$460-920** | Peut être optimisé |

### Optimisation des Coûts
- Utiliser `MAX_MONTHLY_COST_USD` et `ENABLE_COST_ALERTS`
- Traiter les catégories en parallèle via GitHub Actions
- Caching des segments audio récurrents

---

## ⚙️ Personnalisation

### Configuration des Sources de Données
Le cœur du moteur est configuré dans `execution/reddit_analyzer/config.json` :

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

### Configuration Podcast Avancée
La configuration détaillée se trouve dans `execution/reddit_analyzer/podcast_config_advanced.json` :

```json
{
  "tts_settings": {
    "model": "tts-1-hd",
    "max_chars_per_segment": 4000,
    "sample_rate": 24000,
    "audio_format": "mp3"
  },
  "multi_speaker": {
    "HOST": {
      "voice": "onyx",
      "description": "Voix masculine, profonde pour l'animateur"
    },
    "EXPERT": {
      "voice": "shimmer",
      "description": "Voix féminine pour les analyses expertes"
    },
    "GUEST": {
      "voice": "nova",
      "description": "Voix neutre pour les citations"
    }
  },
  "audio_production": {
    "background_music": {
      "intro_volume": -6,
      "body_volume": -15,
      "ducking_level": -15
    }
  }
}
```

*Le système groupera automatiquement les analyses par `category`.*

---

## 🚀 Utilisation

### Mode Manuel (Local)
Placez-vous dans `execution/reddit_analyzer/` :

#### 1. Collecte de Données
```bash
uv run collector.py
```
*Sortie attendue :* "Saved X new posts."

#### 2. Analyse Gemini
```bash
uv run analyze_ideas.py --category "B2B_MARKET"
```
*Sortie attendue :* Création du fichier `latest_analysis_B2B_MARKET.md`

#### 3. Envoi du Rapport
```bash
uv run send_email.py --category "B2B_MARKET"
```
*Sortie attendue :* "Email sent successfully."

### Mode Podcast Complet (Local)
Le système génère des podcasts de qualité broadcast (10 min) :

#### 1. Générer le Script Podcast
```bash
uv run generate_podcast_script.py --category "B2B_MARKET"
```
*Sortie attendue :* `scripts/podcast_script_B2B_MARKET_YYYYMMDD.json`

#### 2. Segmentation Sémantique
Découpe le script en segments cohérents pour TTS :
```bash
uv run semantic_segmentation.py --script "scripts/podcast_script_B2B_MARKET_YYYYMMDD.json"
```

#### 3. Synthèse Audio Multi-Speaker
```bash
uv run synthesize_podcast_audio.py --segments "segments_B2B_MARKET_YYYYMMDD.json"
```

#### 4. Post-Production et Mixage
```bash
uv run audio_postproduction.py --raw-audio "audio/raw/" --output "episodes/"
```

### Mode Automatique (GitHub Actions)
Le workflow `.github/workflows/daily_ideas.yml` s'exécute **tous les jours à 08:00 UTC**.

#### Fonctionnalités
- ✅ **Collecte unique** des données pour optimiser les coûts API
- ✅ **Matrix Strategy** : Traitements parallèles par catégorie
- ✅ **Fail-fast: false** : Une catégorie n'empêche pas les autres
- ✅ **Artifacts** : Conservation des épisodes et scripts générés
- ✅ **Auto-commit** : Mise à jour automatique de la base de données

#### Workflow Complet
```yaml
1. collect-data (global)
   ↓
2. analyze-and-report (par catégorie)
   ├── analyse_ideas.py
   ├── send_email.py  
   ├── generate_podcast_script.py
   ├── semantic_segmentation.py
   ├── synthesize_podcast_audio.py (si OPENAI_API_KEY)
   └── audio_postproduction.py (si OPENAI_API_KEY)
   ↓
3. commit-db (mise à jour DB)
```

---

## 🔧 Dépannage

### Erreurs Courantes

#### **Erreur API Reddit (429)**
- **Cause** : Limite de taux dépassée
- **Solution** : Attendre quelques minutes, le script gère déjà certains délais

#### **Erreur Gemini API**
- **Cause** : Quota atteint ou clé invalide
- **Solution** : Vérifier `.env` et les quotas sur Google AI Studio

#### **Erreur Gmail OAuth**
- **Cause** : `token.json` expiré ou invalide
- **Solution** : Supprimer `token.json` et relancer `uv run send_email.py`

#### **Coûts API Excessifs**
- **Cause** : OpenAI TTS peut être coûteux ($450-900/mois)
- **Solution** : Ajuster `MAX_MONTHLY_COST_USD` et `MAX_EPISODES_PER_DAY`

### Tests de Configuration
```bash
cd execution/reddit_analyzer

# Tester les dépendances
python -c "import openai; print('OpenAI OK')"
python -c "import nltk; print('NLTK OK')"
python -c "from pydub import AudioSegment; print('PyDub OK')"

# Tester les APIs
uv run analyze_ideas.py --category "B2B_MARKET"
uv run send_email.py --category "B2B_MARKET"
```

---

## 📂 Structure des Dossiers

```
ideas-generator/
├── .github/workflows/          # Workflows CI/CD
├── .tmp/                      # Fichiers temporaires (gitignored)
├── directives/                # Procédures (Markdown)
│   ├── daily_business_ideas.md
│   ├── podcast_generation_plan.md
│   └── GEMINI.md
├── execution/reddit_analyzer/ # Code source Python
│   ├── config.json            # Configuration des sources
│   ├── podcast_config_advanced.json # Configuration podcast
│   ├── requirements-audio.txt # Dépendances audio
│   ├── reddit_ideas.db        # Base de données SQLite
│   ├── main.py               # Point d'entrée
│   ├── collector.py          # Scraper RSS Reddit
│   ├── analyze_ideas.py      # Moteur IA (Gemini)
│   ├── send_email.py         # Gestionnaire SMTP/Gmail
│   ├── generate_podcast_script.py     # Scénario podcast
│   ├── semantic_segmentation.py       # Segmentation NLTK
│   ├── synthesize_podcast_audio.py     # Synthèse TTS
│   ├── audio_postproduction.py        # Post-production
│   ├── update_podcast_feed.py         # RSS feed
│   └── assemble_master_podcast.py     # Assemblage final
├── .env                      # Variables d'environnement
├── .env.example             # Template .env
├── README.md
├── ENV_SETUP.md             # Guide configuration détaillé
├── AGENTS.md                # Architecture 3 couches
├── setup.py                 # Script de setup automatisé
└── run_e2e_tests.py        # Tests end-to-end
```

---

## 📊 Surveillance et Monitoring

### Métriques Clés
- **Qualité Analyse** : Nombre d'idées générées, précision Gemini
- **Performance** : Temps d'exécution par étape
- **Coûts** : Suivi des dépenses API avec alertes
- **Emails** : Taux de succès d'envoi
- **Podcasts** : Qualité audio, temps de génération

### Logs GitHub Actions
- URL : `https://github.com/votre-user/ideas-generator/actions`
- Fréquence : Quotidienne à 08:00 UTC
- Retention : 30 jours pour les artifacts

---

## 🤝 Contribuer

1. Fork le repository
2. Créez une branche pour votre feature (`git checkout -b feature/amélioration`)
3. Committez vos changements (`git commit -am 'Ajout de X'`)
4. Poussez la branche (`git push origin feature/amélioration`)
5. Ouvrez un Pull Request

### Bonnes Pratiques
- ✅ Respectez l'architecture 3 couches
- ✅ Testez localement avant de pousser
- ✅ Mettez à jour la documentation si nécessaire
- ✅ Ne commettez jamais de clés API ou secrets

---

## 📄 Licence

Ce projet est open source. Consultez le fichier LICENSE pour plus d'informations.

---

## 🚀 Démo

Le système génère automatiquement des rapports comme celui-ci :

```markdown
# Rapport d'Idées Business : B2B_MARKET

## 📊 Résumé Exécutif
Le marché actuel montre une transition marquée de la simple création de produit vers une obsession pour la distribution et la validation réelle...

## 🚀 Top 5 Opportunités

### 1. Agence de "LLM Optimization" (LLMO)
**🧐 Le Problème :** Un post souligne que d'ici 2026, si un Micro-SaaS n'apparaît pas dans les réponses des LLM, il perdra une part vitale du marché...

**💡 Solution :** Une agence de conseil ou un outil SaaS spécialisé dans l'optimisation pour les moteurs de réponse...
```

---

**Dernière mise à jour :** Janvier 2025