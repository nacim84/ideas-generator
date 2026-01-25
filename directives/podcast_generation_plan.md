# Podcast Generation - Stratégie Avancée 2025

**Objectif :** Production automatisée de podcasts business "broadcast quality" (10 min) à partir des données Reddit déjà collectées, en utilisant l'architecture technique de pointe 2025.

**Technologies Clés :** OpenAI TTS-1-HD, NLTK segmentation, PyDub audio processing, SSML avancé, multi-speaker diarisation.

**Fréquence :** Quotidienne via GitHub Actions (après analyse) ou à la demande.

**Pré-requis :**
- [uv](https://docs.astral.sh/uv/) installé localement.
- Clé API OpenAI configurée dans `.env` (`OPENAI_API_KEY`).
- Fichier `podcast_config_advanced.json` configuré.
- Accès aux fichiers d'analyse `latest_analysis.md`.

---

## Architecture Technique Détaillée

### Pipeline Complète
```
Données Reddit → Analyse Gemini → Script Scénariste → Segmentation NLTK → 
Diariisation Multi-Speaker → TTS-1-HD → Post-Audio (PyDub) → 
Mixage Ducking → Épisode Final → RSS Feed
```

---

## Procédure Exécution

Se placer dans le répertoire de l'outil :
```bash
cd execution/reddit_analyzer
```

### Étape 1 : Génération du Scénario Audio
Transformer l'analyse brute en script podcast structuré.
```bash
uv run generate_podcast_script.py --category "B2B_MARKET"
```
*Sortie attendue :* `scripts/podcast_script_[category]_[date].json` avec structure multi-speaker.

### Étape 2 : Segmentation Sémantique Avancée
Découper le script en segments cohérents pour TTS.
```bash
uv run semantic_segmentation.py --script "scripts/podcast_script_b2b_20250125.json"
```
*Sortie attendue :* Segments de <4000 caractères respectant les limites OpenAI.

### Étape 3 : Synthèse Multi-Speaker TTS-1-HD
Générer les pistes audio avec voix différenciées.
```bash
uv run synthesize_podcast_audio.py --segments "segments_b2b_20250125.json"
```
*Sortie attendue :* Fichiers audio segmentés dans `audio/raw/`.

### Étape 4 : Post-Production Audio
Appliquer effets, ducking et mastering.
```bash
uv run audio_postproduction.py --raw-audio "audio/raw/" --output "episodes/"
```
*Sortie attendue :* Épisode final MP3 masterisé.

### Étape 5 : Génération RSS Feed
Mettre à jour le podcast feed avec nouvel épisode.
```bash
uv run update_podcast_feed.py --new-episode "episodes/b2b_20250125.mp3"
```

---

## Configuration Avancée

### podcast_config_advanced.json
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
      "description": "Voix masculine, profonde, autoritaire pour l'animateur principal",
      "emotion": "professional_calm"
    },
    "EXPERT": {
      "voice": "shimmer", 
      "description": "Voix féminine, claire, dynamique pour les analyses expertes",
      "emotion": "enthusiastic"
    },
    "GUEST": {
      "voice": "nova",
      "description": "Voix neutre pour les citations et témoignages",
      "emotion": "conversational"
    }
  },
  "audio_production": {
    "background_music": {
      "intro_volume": -6,
      "body_volume": -15,
      "outro_volume": -6,
      "ducking_level": -15
    },
    "effects": {
      "intro_duration": 5000,
      "outro_duration": 5000,
      "crossfade_duration": 2000,
      "compressor_threshold": -18
    },
    "mastering": {
      "target_loudness": -16,
      "eq_low_cut": 80,
      "eq_high_cut": 16000
    }
  },
  "content_strategy": {
    "max_episode_duration": 600,
    "segments": {
      "intro": 0.08,
      "main_content": 0.80,
      "conclusion": 0.12
    },
    "text_normalization": {
      "SaaS": "sass",
      "Q3": "Q three",
      "EBITDA": "E-BIT-DA",
      "YoY": "year over year"
    }
  }
}
```

---

## Scripts Python à Développer

### 1. generate_podcast_script.py
**Objectif :** Transformer l'analyse brute en script podcast structuré.

**Fonctionnalités :**
- Parsing du markdown d'analyse
- Structuration multi-speaker (HOST + EXPERT)
- Application des règles de normalisation textuelle
- Ajout d'éléments radiophoniques (pauses, emphases)

**Exemple de structure JSON :**
```json
{
  "title": "Idées Business du 25 Janvier 2025 - Marché B2B",
  "duration_target": 600,
  "host": "Bienvenue dans cette analyse quotidienne des opportunités business...",
  "segments": [
    {
      "speaker": "HOST",
      "content": "Commençons par les demandes directes les plus intéressantes...",
      "emphasis": ["SaaS", "automatisation"]
    },
    {
      "speaker": "EXPERT", 
      "content": "Notre analyse montre une tendance claire vers les solutions...",
      "technical_terms": ["EBITDA", "YoY"]
    }
  ],
  "outro": "Merci d'avoir écouté cette analyse..."
}
```

### 2. semantic_segmentation.py
**Objectif :** Découpe intelligente du texte en segments TTS.

**Technologie :** NLTK pour la tokenisation avancée

**Logique :**
```python
def semantic_chunking(text, max_chars=4000):
    """
    Découpe le texte en segments < max_chars sans couper les phrases.
    """
    sentences = nltk.sent_tokenize(text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= max_chars:
            current_chunk += sentence + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " "

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks
```

### 3. synthesize_podcast_audio.py
**Objectif :** Génération des pistes audio avec diarisation.

**Fonctionnalités :**
- Sélection vocale par rôle
- Appels API parallèles
- Gestion des erreurs et retry
- Nommage cohérent des fichiers

**Exemple d'appel TTS :**
```python
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def synthesize_segment(text, speaker_role, index):
    # Sélection de la voix selon le rôle
    voice_mapping = {
        "HOST": "onyx",
        "EXPERT": "shimmer", 
        "GUEST": "nova"
    }
    
    response = client.audio.speech.create(
        model="tts-1-hd",
        voice=voice_mapping[speaker_role],
        input=text
    )
    
    filename = f"temp_segment_{index:03d}.mp3"
    response.stream_to_file(filename)
    return filename
```

### 4. audio_postproduction.py
**Objectif :** Post-production professionnelle avec PyDub.

**Fonctionnalités :**
- Ducking automatique (musique baisse pendant la parole)
- Crossfades doux
- Normalisation audio
- Mastering basique

**Logique de Ducking :**
```python
def apply_ducking(voice_track, background_music, ducking_level=-15):
    # Boucler la musique si nécessaire
    while len(background_music) < len(voice_track) + 5000:
        background_music += background_music
    
    # Structure en 3 parties
    intro_duration = 5000
    music_intro = background_music[:intro_duration]
    music_body = background_music[intro_duration:len(voice_track)+intro_duration] + ducking_level
    music_outro = background_music[len(voice_track)+intro_duration:]
    
    # Assemblage avec crossfades
    final_music = music_intro.append(music_body, crossfade=2000).append(music_outro, crossfade=2000)
    final_mix = final_music.overlay(voice_track, position=intro_duration)
    
    return final_mix
```

---

## Intégration CI/CD Avancée

### Workflow GitHub Actions Mis à Jour

```yaml
  generate-podcast-advanced:
    needs: [analyze-and-report]
    runs-on: ubuntu-latest
    strategy:
      matrix:
        category: ${{ fromJson(needs.setup-matrix.outputs.categories) }}
      fail-fast: false
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install uv
        uses: astral-sh/setup-uv@v5

      - name: Install dependencies
        run: |
          cd execution/reddit_analyzer
          uv sync --frozen || uv sync

      - name: Create configuration from Secrets
        run: |
          echo "OPENAI_API_KEY=${{ secrets.OPENAI_API_KEY }}" >> .env
          echo '${{ secrets.PODCAST_CONFIG_ADVANCED_JSON }}' > podcast_config_advanced.json

      - name: Generate Podcast Script for ${{ matrix.category }}
        run: |
          cd execution/reddit_analyzer
          uv run generate_podcast_script.py --category "${{ matrix.category }}"

      - name: Semantic Segmentation
        run: |
          cd execution/reddit_analyzer
          uv run semantic_segmentation.py --script "scripts/podcast_script_${{ matrix.category }}_$(date +%Y%m%d).json"

      - name: Synthesize TTS Audio
        run: |
          cd execution/reddit_analyzer
          uv run synthesize_podcast_audio.py --segments "segments_${{ matrix.category }}_$(date +%Y%m%d).json"

      - name: Audio Post-Production
        run: |
          cd execution/reddit_analyzer
          uv run audio_postproduction.py --raw-audio "audio/raw/" --output "episodes/"

      - name: Upload Podcast Artifacts
        uses: actions/upload-artifact@v4
        with:
          name: podcast-advanced-${{ matrix.category }}
          path: |
            execution/reddit_analyzer/episodes/${{ matrix.category }}_*.mp3
            execution/reddit_analyzer/scripts/*.json
          retention-days: 30
```

---

## Gestion des Musiques et Effets Sonores

### Bibliothèques Royalty-Free Recommandées
1. **Pixabay Music** - Qualité professionnelle, CC-BY attribution
2. **YouTube Audio Library** - Pistes testées et approuvées par YouTube
3. **Free Music Archive** - Collection variée sous licence Creative Commons

### Structure des Assets Audio
```
assets/
├── music/
│   ├── intro/
│   │   ├── business_upbeat.mp3
│   │   └── professional_calm.mp3
│   ├── background/
│   │   ├── subtle_pad.mp3
│   │   └── corporate_ambient.mp3
│   └── outro/
│       ├── closing_theme.mp3
│       └── signature_tune.mp3
├── sound_effects/
│   ├── transition.mp3
│   └── emphasis.mp3
└── jingles/
    ├── daily_opening.mp3
    └── daily_closing.mp3
```

### Gestion des Droits d'Auteur
- **Attribution Obligatoire :** CC-BY nécessite mention de l'artiste
- **Évolutivité :** Système de rotation des musiques pour éviter la saturation
- **Qualité Constante :** Normalisation des niveaux audio entre pistes

---

## Optimisation des Coûts

### Stratégies de Réduction
1. **Batch Processing :** Traiter les segments par lots de 5-10 pour optimiser les appels API
2. **Voice Caching :** Mettre en cache les segments récurrents (intros, transitions)
3. **Quality Scaling :** Ajuster la qualité TTS selon l'importance du segment
4. **Parallel Processing :** Utiliser GitHub Actions matrix pour catégories parallèles

### Estimation des Coûts OpenAI TTS-1-HD
- **Caractères par épisode :** ~15,000 (10 minutes × 1500 mots/min × 10 caractères/mot)
- **Coût par million de caractères :** $15 (TTS-1-HD)
- **Coût mensuel estimé :** $15 × 30 jours × nombre de catégories = **$450-900/mois**

### Alternatives Économiques
1. **ElevenLabs Creator Plan :** $22/mois pour 100,000 caractères
2. **Azure Cognitive Services :** $4/heure voix personnalisée
3. **Local TTS Models :** Coche-11B, Bark (qualité variable)

---

## Qualité Audio et Standards

### Paramètres Techniques
- **Format :** MP3 CBR 128kbps (compromis qualité/taille)
- **Sample Rate :** 24kHz (standard podcast)
- **Canaux :** Mono (compatibilité maximale)
- **Loudness Target :** -16 LUFS (standard podcast)

### Validation Audio
1. **Vérification des coupures :** Aucune phrase coupée en milieu de segment
2. **Test de diarisation :** Voix correctement attribuées aux rôles
3. **Contrôle du ducking :** Musique bien baissée pendant la parole
4. **Normalisation :** Volume cohérent entre épisodes

---

## Stratégie de Contenu et Humanisation

### Techniques d'Humanisation
1. **Pauses Stratégiques :** Utilisation de tirets cadratins (—) et ellipses (...) pour simuler la réflexion
2. **Variation Prosodique :** Majuscules pour l'emphase sur les concepts clés
3. **Interaction Simulée :** Créer des "dialogues" internes entre HOST et EXPERT
4. **Anecdotes Contextuelles :** Ajouter des références culturelles pertinentes

### Gestion des Termes Techniques
```python
# Normalisation pré-TTS
text_normalization_rules = {
    # Business Terms
    "SaaS": "sass",
    "B2B": "B to B", 
    "B2C": "B to C",
    "EBITDA": "E-BIT-DA",
    "YoY": "year over year",
    "Q1": "Q one",
    "Q2": "Q two",
    "Q3": "Q three", 
    "Q4": "Q four",
    
    # Tech Terms
    "AI": "artificial intelligence",
    "API": "A P I",
    "CRM": "C R M",
    "SQL": "S Q L",
    
    # Financial Terms  
    "$10M": "ten million dollars",
    "$1B": "one billion dollars"
}
```

---

## Monitoring et Analytics

### Métriques Clés
1. **Qualité Audio :** Taux de succès TTS, temps moyen de génération
2. **Performance :** Coût par épisode, temps de post-production
3. **Engagement :** Temps d'écoute, nombre de téléchargements
4. **Techniques :** Taille fichiers, bitrate utilisé

### Outils de Surveillance
- **GitHub Actions :** Logs détaillés et monitoring des échecs
- **OpenAI Dashboard :** Suivi des coûts et quotas d'utilisation
- **Audio Validators :** Scripts de validation automatique de la qualité
- **Podcast Analytics :** écoute via podcast hosting platform

---

## Maintenance et Évolution

### Mises à Jour Prioritaires
1. **Monitoring des Coûts :** Alerte si dépassement de budget mensuel
2. **Rotation des Voix :** Tester nouvelles voix disponibles
3. **Optimisation Contenu :** A/B testing des structures de script
4. **Sécurité :** Rotation des clés API et secrets

### Scalabilité Future
- **Support Langues :** Extension vers l'anglais, espagnol, allemand
- **Personnalisation :** Profils utilisateur avec préférences audio
- **Interactivité :** Version "live" avec questions/réponses
- **Monétisation :** Intégration publicités ciblées business

---

Ce plan représente l'état de l'art 2025 pour la production automatisée de podcasts professionnels, en combinant LLM avancés, TTS de haute qualité et techniques de post-production broadcast.