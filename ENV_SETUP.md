# Configuration des Variables d'Environnement

Ce guide explique comment configurer les variables d'environnement pour le système de génération podcast.

## 📋 Variables Requises

### 1. Clés API Essentielles

#### GEMINI_API_KEY
**Source :** [Google AI Studio](https://makersuite.google.com/app/apikey)  
**Usage :** Analyse des idées business à partir des données Reddit  
**Exemple :** `AIzaSyB_C3...`

#### OPENAI_API_KEY  
**Source :** [OpenAI Platform](https://platform.openai.com/api-keys)  
**Usage :** Synthèse vocale (TTS) pour la génération podcast  
**Exemple :** `sk-abc123...`

#### RECIPIENT_EMAIL
**Source :** Votre email personnel  
**Usage :** Réception des rapports email quotidiens  
**Exemple :** `votre-email@exemple.com`

### 2. Configuration Gmail (pour envoi d'emails)

#### Étape 1 : Créer un projet Google Cloud
1. Allez sur [Google Cloud Console](https://console.cloud.google.com/)
2. Créez un nouveau projet
3. Activez l'API "Gmail API"

#### Étape 2 : Créer des identifiants OAuth2
1. Allez dans "Credentials" > "Create Credentials" > "OAuth client ID"
2. Sélectionnez "Desktop app"
3. Téléchargez le fichier `credentials.json`
4. Placez-le dans `execution/reddit_analyzer/credentials.json`

#### Étape 3 : Authentification
1. Exécutez `uv run send_email.py` en local
2. Une fenêtre s'ouvrira pour vous connecter
3. Cela générera automatiquement `token.json`

## 🔧 Configuration Complète

### Fichier .env
Copiez `.env.example` vers `.env` et remplissez les valeurs :

```bash
# Copier le template
cp .env.example .env

# Éditer avec vos valeurs
nano .env
```

### Variables Clés à Configurer

```bash
# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Email
RECIPIENT_EMAIL=your_email@destination.com

# Podcast Settings
PODCAST_TITLE="Idées Business Quotidiennes"
PODCAST_DESCRIPTION="Analyses quotidiennes des opportunités business..."
PODCAST_AUTHOR="AI Business Ideas Generator"

# Cost Management
MAX_MONTHLY_COST_USD=100.0
MAX_EPISODES_PER_DAY=20
```

## 🚀 Configuration GitHub Actions

### Secrets Repository
Ajoutez ces secrets dans votre repository GitHub :

1. Allez dans Settings > Secrets and variables > Actions
2. Cliquez sur "New repository secret"

#### Secrets Requis
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

# Cost Management
MAX_MONTHLY_COST_USD=100.0
```

### Secrets Optionnels
```bash
# Cloud Storage
PODCAST_STORAGE_BUCKET=your-bucket-name
PODCAST_STORAGE_REGION=us-east-1

# Analytics
GA_TRACKING_ID=UA-XXXXXXXXX-X

# Distribution
PODCAST_INDEX_API_KEY=your_key_here
PODCAST_INDEX_API_SECRET=your_secret_here
```

## 🎯 Configuration par Environnement

### Développement
```bash
ENVIRONMENT=development
LOG_LEVEL=DEBUG
ENABLE_DEBUG_LOGGING=true
PODCAST_DRY_RUN=true
MAX_EPISODES_PER_DAY=5
```

### Production
```bash
ENVIRONMENT=production
LOG_LEVEL=INFO
ENABLE_DEBUG_LOGGING=false
PODCAST_DRY_RUN=false
MAX_EPISODES_PER_DAY=20
```

## 🔐 Sécurité

### Bonnes Pratiques
1. **Ne jamais commettre** de clés API dans le dépôt
2. **Utiliser** `.gitignore` pour ignorer `.env`
3. **Rotater** régulièrement les clés API
4. **Limiter** les permissions des clés API
5. **Surveiller** l'utilisation avec des alertes

### Configuration .gitignore
Assurez-vous que `.gitignore` contient :
```
.env
*.log
__pycache__/
*.pyc
.venv/
.env.local
.env.development.local
.env.test.local
.env.production.local
```

## 📊 Monitoring des Coûts

### Estimation des Coûts
```bash
# Coûts mensuels estimés
GEMINI_API: $10-20/mois
OPENAI_TTS: $450-900/mois (selon usage)
TOTAL: $460-920/mois
```

### Alertes de Coûts
Configurez les alertes dans `.env` :
```bash
ENABLE_COST_ALERTS=true
COST_ALERT_THRESHOLD=80.0  # 80% du budget mensuel
MAX_MONTHLY_COST_USD=100.0
```

## 🎵 Configuration Audio

### Paramètres Qualité
```bash
AUDIO_FORMAT=mp3
AUDIO_BITRATE=128k
AUDIO_SAMPLE_RATE=24000
AUDIO_CHANNELS=mono
```

### Voix TTS
```bash
HOST_VOICE=onyx          # Voix masculine, profonde
EXPERT_VOICE=shimmer     # Voix féminine, claire
GUEST_VOICE=nova         # Voix neutre
TTS_MODEL=tts-1-hd       # Qualité HD
```

## 🔧 Tests de Configuration

### Vérification des Dépendances
```bash
cd execution/reddit_analyzer

# Tester les imports Python
python -c "import openai; print('OpenAI OK')"
python -c "import nltk; print('NLTK OK')"
python -c "from pydub import AudioSegment; print('PyDub OK')"
```

### Test de Connexion API
```bash
# Tester Gemini API
uv run analyze_ideas.py --category "B2B_MARKET"

# Tester OpenAI TTS
uv run synthesize_podcast_audio.py --max-concurrent 1

# Tester envoi email
uv run send_email.py --category "B2B_MARKET"
```

## 🚀 Démarrage Rapide

1. **Installer les dépendances**
   ```bash
   cd execution/reddit_analyzer
   uv sync
   uv add -r requirements-audio.txt
   ```

2. **Configurer les clés API**
   ```bash
   cp .env.example .env
   # Éditer .env avec vos valeurs
   ```

3. **Authentification Gmail**
   ```bash
   uv run send_email.py --category "B2B_MARKET"
   ```

4. **Tester le système**
   ```bash
   uv run generate_podcast_script.py --category "B2B_MARKET"
   uv run semantic_segmentation.py --script "scripts/podcast_script_b2b_*.json"
   ```

5. **Déployer en production**
   ```bash
   git push origin main
   # Le workflow GitHub Actions s'exécutera automatiquement
   ```

## 📞 Support

Si vous rencontrez des problèmes :
1. Vérifiez les logs GitHub Actions
2. Confirmez que toutes les variables sont correctement configurées
3. Testez manuellement chaque composant
4. Consultez la documentation dans `directives/`

## 🔄 Mises à Jour

### Mettre à jour les clés API
1. Générer de nouvelles clés sur les plateformes respectives
2. Mettre à jour `.env` localement
3. Mettre à jour les secrets GitHub
4. Redémarrer le workflow si nécessaire

### Mettre à jour la configuration
1. Modifier `podcast_config_advanced.json` pour changer les voix ou paramètres
2. Tester les changements en développement
3. Déployer en production
4. Surveiller les résultats et ajuster si nécessaire