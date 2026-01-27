import argparse
import json
import os
from datetime import datetime
from pathlib import Path

from pydub import AudioSegment
from pydub.effects import normalize


def load_config():
    """Load podcast configuration from JSON file."""
    config_path = Path(__file__).parent / "podcast_config_advanced.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_audio_files(raw_dir):
    """Find, sort, and load all audio files from a directory."""
    segments = []

    # Find all mp3 files and sort them numerically
    audio_files = sorted(raw_dir.glob("segment_*.mp3"))

    for file_path in audio_files:
        audio_file = file_path.name
        if file_path.exists():
            try:
                audio = AudioSegment.from_file(file_path)
                segments.append(
                    {"file": audio_file, "audio": audio, "duration": len(audio)}
                )
            except Exception as e:
                print(f"Warning: Could not load {audio_file}: {e}")
        else:
            print(f"Warning: Audio file not found: {file_path}")

    return segments


def apply_ducking(voice_track, background_music, ducking_level=-15):
    """
    Mixe la voix et la musique en baissagnt la musique pendant la parole.
    """
    # Boucler la musique si elle est plus courte que la voix
    while len(background_music) < len(voice_track) + 5000:
        background_music += background_music

    # Ajustement initial du volume de la musique (tapis sonore)
    background_music = background_music - 10  # -10dB par défaut

    # Structure en 3 parties
    intro_duration = 5000
    music_intro = background_music[:intro_duration]
    music_body = (
        background_music[intro_duration : len(voice_track) + intro_duration]
        + ducking_level
    )
    music_outro = background_music[len(voice_track) + intro_duration :]

    # Assemblage de la piste musique modifiée
    final_music = music_intro.append(music_body, crossfade=2000).append(
        music_outro, crossfade=2000
    )

    # Superposition (Overlay)
    final_mix = final_music.overlay(voice_track, position=intro_duration)

    return final_mix


def create_background_music(config):
    """Create background music with proper structure."""
    # For now, create silent background as placeholder
    # In real implementation, this would load actual music files
    duration = 600000  # 10 minutes in milliseconds
    background = AudioSegment.silent(duration=duration)

    # Apply volume settings from config
    volume_settings = config["audio_production"]["background_music"]

    # Create different sections
    intro_duration = config["audio_production"]["effects"]["intro_duration"]
    outro_duration = config["audio_production"]["effects"]["outro_duration"]

    # Intro section (louder)
    intro = background[:intro_duration] + volume_settings["intro_volume"]

    # Main section (quieter)
    main_section = (
        background[intro_duration : duration - outro_duration]
        + volume_settings["body_volume"]
    )

    # Outro section (louder again)
    outro = background[duration - outro_duration :] + volume_settings["outro_volume"]

    # Combine with crossfades
    full_background = intro.append(main_section, crossfade=2000)
    full_background = full_background.append(outro, crossfade=2000)

    return full_background


def create_episode_audio(segments, config, output_file):
    """Create final episode audio by combining all segments."""
    print("Creating episode audio...")

    # Create combined voice track
    voice_track = AudioSegment.empty()
    total_duration = 0

    for i, segment in enumerate(segments):
        voice_track += segment["audio"]
        total_duration += segment["duration"]
        print(f"Added segment {i + 1}/{len(segments)}: {segment['duration']}ms")

    print(
        f"Total voice duration: {total_duration}ms ({total_duration / 1000 / 60:.1f} minutes)"
    )

    # Create background music
    background_music = create_background_music(config)

    # Apply ducking
    print("Applying ducking effect...")
    final_audio = apply_ducking(
        voice_track,
        background_music,
        config["audio_production"]["background_music"]["ducking_level"],
    )

    # Apply mastering
    print("Applying mastering...")

    # Normalize to target loudness
    target_loudness = config["audio_production"]["mastering"]["target_loudness"]
    final_audio = normalize(final_audio, headroom=target_loudness)

    # Apply EQ (simple high-pass filter)
    eq_low_cut = config["audio_production"]["mastering"]["eq_low_cut"]
    final_audio = final_audio.high_pass_filter(eq_low_cut)

    eq_high_cut = config["audio_production"]["mastering"]["eq_high_cut"]
    final_audio = final_audio.low_pass_filter(eq_high_cut)

    # Export final audio
    print(f"Exporting final episode to: {output_file}")

    # Set format and quality
    format_settings = config["tts_settings"]
    if format_settings["audio_format"] == "mp3":
        final_audio.export(output_file, format="mp3", bitrate="128k")
    else:
        final_audio.export(output_file, format=format_settings["audio_format"])

    print(f"Episode created successfully: {output_file}")
    print(
        f"Final duration: {len(final_audio)}ms ({len(final_audio) / 1000 / 60:.1f} minutes)"
    )

    return len(final_audio)


def create_metadata_file(
    segments, config, output_file, episode_duration, category, date
):
    """Create metadata file for the episode."""
    metadata = {
        "title": f"Idées Business du {date} - {category}",
        "category": category,
        "date": date,
        "duration_ms": episode_duration,
        "duration_minutes": episode_duration / 1000 / 60,
        "total_segments": len(segments),
        "audio_format": config["tts_settings"]["audio_format"],
        "sample_rate": config["tts_settings"]["sample_rate"],
        "created_at": str(os.path.getmtime(output_file)),
        "segments": [
            {
                "file": segment["file"],
                "duration_ms": segment["duration"],
                "speaker": "unknown",
            }
            for segment in segments
        ],
    }

    metadata_file = output_file.with_suffix(".json")
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"Metadata saved: {metadata_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Create final podcast episode from audio segments"
    )
    parser.add_argument(
        "--raw-audio",
        required=True,
        help="Directory containing raw audio files (e.g., audio/raw/B2B_MARKET)",
    )
    parser.add_argument(
        "--output-dir", help="Output directory for episodes (default: episodes/)"
    )
    parser.add_argument(
        "--output-file",
        help="Output episode file path (auto-generated if not specified)",
    )

    args = parser.parse_args()

    # Load configuration
    try:
        config = load_config()
    except FileNotFoundError:
        print("Error: podcast_config_advanced.json not found")
        return 1

    # Load audio files
    raw_dir = Path(args.raw_audio)
    segments = find_audio_files(raw_dir)

    if not segments:
        print("Error: No valid audio segments found in the specified directory.")
        return 1

    print(f"Loaded {len(segments)} audio segments from {raw_dir}")

    # Generate output filename
    if args.output_file:
        output_file = Path(args.output_file)
    else:
        output_dir = (
            Path(args.output_dir)
            if args.output_dir
            else Path(__file__).parent / "episodes"
        )
        output_dir.mkdir(parents=True, exist_ok=True)

        category = raw_dir.name
        date = datetime.now().strftime("%Y%m%d")

        output_file = output_dir / f"episode_{category}_{date}.mp3"

    # Create episode audio
    episode_duration = create_episode_audio(segments, config, output_file)

    # Create metadata
    category = raw_dir.name
    date = datetime.now().strftime("%Y%m%d")
    create_metadata_file(
        segments, config, output_file, episode_duration, category, date
    )

    print(f"Post-production completed successfully!")
    print(f"Final episode: {output_file}")
    print(f"Duration: {episode_duration / 1000 / 60:.1f} minutes")

    return 0


if __name__ == "__main__":
    exit(main())
