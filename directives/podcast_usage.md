# Podcast Generation - Utilisation

**Objectif :** Guide pratique pour utiliser le système de génération podcast avancé, depuis la configuration initiale jusqu'à la production d'épisodes.

**Technologies :** OpenAI TTS-1-HD, NLTK, PyDub, GitHub Actions.

---

## 🚀 Installation et Configuration

### 1. Installation des Dépendances

```bash
cd execution/reddit_analyzer

# Installer les dépendences audio
uv add -r requirements-audio.txt

# Télécharger les données NLTK requises
python -c "import nltk; nltk.download('punkt')"
```

### 2. Configuration des Secrets GitHub

Ajouter dans les secrets du repository GitHub :

```bash
OPENAI_API_KEY=your_openai_api_key_here
PODCAST_CONFIG_ADVANCED_JSON=$(cat podcast_config_advanced.json | base64 -w 0)
```

### 3. Configuration Environnement Local

```bash
# Ajouter au fichier .env à la racine
OPENAI_API_KEY=your_openai_api_key_here
```

---

## 🎙️ Workflow de Production

### Exécution Manuelle (Développement)

```bash
cd execution/reddit_analyzer

# 1. Générer le script podcast
uv run generate_podcast_script.py --category "B2B_MARKET"

# 2. Segmenter sémantiquement
uv run semantic_segmentation.py --script "scripts/podcast_script_b2b_20250125.json"

# 3. Synthétiser l'audio TTS
uv run synthesize_podcast_audio.py --segments "segments_b2b_20250125.json"

# 4. Post-production audio
uv run audio_postproduction.py --raw-audio "audio/raw/" --output "episodes/"

# 5. Mettre à jour le RSS
uv run update_podcast_feed.py --new-episode "episodes/episode_b2b_20250125.mp3"
```

### Exécution Automatisée (Production)

Le système s'exécute automatiquement via GitHub Actions :

1. **Déclenchement quotidien** à 08:00 UTC
2. **Pour chaque catégorie** configurée
3. **Pipeline complet** : script → segmentation → TTS → post-production → RSS

---

## 🔧 Configuration Personnalisée

### Modification des Voix

Éditez `podcast_config_advanced.json` :

```json
{
  "multi_speaker": {
    "HOST": {
      "voice": "onyx",           // Voix masculine, profonde
      "emotion": "professional_calm"
    },
    "EXPERT": {
      "voice": "shimmer",        // Voix féminine, claire  
      "emotion": "enthusiastic"
    },
    "GUEST": {
      "voice": "nova",           // Voix neutre
      "emotion": "conversational"
    }
  }
}
```

**Voix disponibles OpenAI TTS :**
- `onyx` - Masculine, profonde, autoritaire
- `shimmer` - Féminine, claire, dynamique
- `nova` - Neutre, bienveillante
- `alloy` - Neutre, équilibrée
- `echo` - Masculine, énergique
- `fable` - Masculine, storytelling
- `onyx` - Masculine, professionnelle

### Ajustement de la Qualité Audio

```json
{
  "tts_settings": {
    "model": "tts-1-hd",        // Qualité HD
    "max_chars_per_segment": 4000, // Limite OpenAI
    "sample_rate": 24000,       // Qualité podcast
    "audio_format": "mp3"
  },
  "audio_production": {
    "background_music": {
      "ducking_level": -15,     // Musique baissée pendant parole
      "intro_volume": -6,       // Volume intro
      "body_volume": -15        // Volume principal
    }
  }
}
```

### Normalisation Texte Personnalisée

Ajoutez vos propres règles dans `content_strategy.text_normalization` :

```json
{
  "text_normalization": {
    "ACME": "A-C-M-E",
    "ROI": "R-O-I",
    "KPI": "K-P-I",
    "SAAS": "sass",
    "VotreStartup": "votre startup"
  }
}
```

---

## 📊 Monitoring et Débogage

### Logs GitHub Actions

1. **Accéder aux logs :** GitHub → Actions → Daily_Business_Ideas_Workflow
2. **Identifier les erreurs :**
   - ❌ `OPENAI_API_KEY not found` → Secret manquant
   - ❌ `Invalid API key` → Clé OpenAI invalide
   - ❌ `NLTK data missing` → Données NLTK non téléchargées
   - ❌ `Audio file not found` → Problème de génération TTS

### Débogage Local

```bash
# Tester chaque étape individuellement

# 1. Tester la génération de script
uv run generate_podcast_script.py --category "B2B_MARKET"

# 2. Tester la segmentation
uv run semantic_segmentation.py --script "scripts/podcast_script_b2b_20250125.json"

# 3. Tester la synthèse TTS (avec une limite)
uv run synthesize_podcast_audio.py --segments "segments_b2b_20250125.json" --max-concurrent 1

# 4. Tester la post-production
uv run audio_postproduction.py --raw-audio "audio/raw/" --output "episodes/debug/"
```

### Validation Audio

Vérifiez la qualité des fichiers générés :

```bash
# Vérifier la structure des fichiers
find audio/raw -name "*.mp3" | head -5
ls -la episodes/

# Vérifier les métadonnées
cat episode_b2b_20250125.json | jq '.duration_ms, .total_segments'

# Jouer un fichier audio (optionnel)
# Utilisez votre lecteur audio préféré
```

---

## 💰 Optimisation des Coûts

### Surveillance des Coûts OpenAI

1. **Dashboard OpenAI :** https://platform.openai.com/usage
2. **Estimation mensuelle :**
   - 15k caractères/épisode × 30 jours × 5 catégories = 2.25M caractères/mois
   - Coût : ~$33.75/mois (à $15/million de caractères)

### Stratégies d'Optimisation

```json
{
  "optimization_strategies": {
    "batch_processing": true,      // Traiter par lots
    "voice_caching": true,         // Mettre en cache les segments récurrents
    "quality_scaling": false,       // Ne pas réduire qualité
    "parallel_processing": true    // Utiliser le matrix GitHub Actions
  }
}
```

### Alternatives Économiques

Si les coûts deviennent trop élevés :

1. **ElevenLabs Creator Plan :** $22/mois (100k caractères)
2. **Réduction catégories :** Passer de 5 à 3 catégories
3. **Fréquence réduite :** Passer à 3 épisodes/semaine
4. **Qualité réduite :** Utiliser `tts-1` au lieu de `tts-1-hd`

---

## 🎵 Gestion des Musiques et Assets

### Structure des Assets

```
assets/
├── music/
│   ├── intro/         # Musiques d'introduction
│   ├── background/    # Musiques de fond
│   └── outro/         # Musiques de conclusion
├── sound_effects/     # Effets sonores
└── jingles/          # Jingles quotidiens
```

### Sources Royalty-Free

1. **Pixabay Music** : https://pixabay.com/music/
   - Qualité professionnelle, CC-BY attribution requise
2. **YouTube Audio Library** : https://studio.youtube.com/
   - Pistes testées par YouTube
3. **Free Music Archive** : https://freemusicarchive.org/
   - Collection variée sous Creative Commons

### Exemple de Configuration Musicale

```json
{
  "audio_production": {
    "background_music": {
      "intro_volume": -6,
      "body_volume": -15,
      "outro_volume": -6,
      "ducking_level": -15
    },
    "music_tracks": {
      "intro": "assets/music/intro/business_upbeat.mp3",
      "background": "assets/music/background/corporate_ambient.mp3", 
      "outro": "assets/music/outro/closing_theme.mp3"
    }
  }
}
```

---

## 🚨 Dépannage des Erreurs Courantes

### Erreurs API OpenAI

**Problème :** `Rate limit exceeded`
```bash
# Solution : Réduire la concurrence
uv run synthesize_podcast_audio.py --max-concurrent 1
```

**Problème :** `Invalid API key`
```bash
# Solution : Vérifier la clé dans .env
echo $OPENAI_API_KEY
```

### Erreurs Audio

**Problème :** `pydub could not find ffmpeg`
```bash
# Solution (Ubuntu) :
sudo apt-get install ffmpeg

# Solution (macOS) :
brew install ffmpeg

# Solution (Windows) :
# Télécharger ffmpeg et ajouter au PATH
```

**Problème :** `NLTK data missing`
```bash
# Solution :
python -c "import nltk; nltk.download('punkt')"
```

### Erreurs Fichiers

**Problème :** `File not found: latest_analysis.md`
```bash
# Solution : Exécuter d'abord l'analyse
uv run analyze_ideas.py --category "B2B_MARKET"
```

**Problème :** `Permission denied`
```bash
# Solution : Vérifier les permissions des répertoires
chmod 755 audio/ audio/raw/ episodes/ scripts/
```

---

## 📈 Performance et Scalabilité

### Métriques à Suivre

1. **Qualité Audio :**
   - Taux de succès TTS
   - Temps moyen de génération par épisode
   - Taille moyenne des fichiers

2. **Performance :**
   - Coût par épisode
   - Temps de post-production
   - Utilisation CPU/mémoire

3. **Engagement :**
   - Nombre de téléchargements
   - Temps d'écoute moyen
   - Erreurs de lecture

### Optimisation du Workflow

```yaml
# Configuration GitHub Actions optimisée
strategy:
  matrix:
    category: ${{ fromJson(needs.setup-matrix.outputs.categories) }}
  max-parallel: 3  # Limiter la concurrence pour économiser les coûts
  fail-fast: false
```

---

## 🔐 Sécurité et Maintenance

### Rotation des Clés API

1. **Clé OpenAI :** Mettre à jour tous les 3 mois
2. **Gestion des secrets :** Utiliser GitHub Secrets avec rotation automatique
3. **Audit d'accès :** Vérifier qui a accès aux secrets

### Sauvegardes

```bash
# Sauvegarde des épisodes générés
tar -czf podcast_episodes_backup_$(date +%Y%m%d).tar.gz episodes/

# Sauvegarde des configurations
cp podcast_config_advanced.json podcast_config_backup_$(date +%Y%m%d).json
```

### Mises à Jour

1. **Mises à jour dépendances :** `uv sync --upgrade`
2. **Mises à jour configuration :** Adapter `podcast_config_advanced.json`
3. **Monitoring :** Vérifier les nouvelles versions des bibliothèques

---

Ce guide vous permettra de maîtriser la production podcast automatisée et d'optimiser la qualité/coût de vos épisodes.