import os
import json
import argparse
import asyncio
from pathlib import Path
from openai import OpenAI


def load_config():
    """Load podcast configuration from JSON file."""
    config_path = Path(__file__).parent / "podcast_config_advanced.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_segments(segments_file):
    """Load segments from JSON file."""
    with open(segments_file, "r", encoding="utf-8") as f:
        return json.load(f)


def get_voice_for_speaker(speaker, config):
    """Get the voice ID for a given speaker role."""
    voice_mapping = config["multi_speaker"]
    if speaker in voice_mapping:
        return voice_mapping[speaker]["voice"]
    else:
        # Default to HOST voice if speaker not found
        return voice_mapping["HOST"]["voice"]


async def synthesize_segment(segment, config, client, index):
    """
    Génère l'audio pour un segment donné avec la voix appropriée.
    """
    # Sélection de la voix selon le rôle
    voice_id = get_voice_for_speaker(segment["speaker"], config)

    print(
        f"Generating segment {index}: {segment['speaker']} - {len(segment['content'])} chars"
    )

    try:
        response = client.audio.speech.create(
            model=config["tts_settings"]["model"],
            voice=voice_id,
            input=segment["content"],
        )

        filename = f"temp_segment_{index:03d}_{segment['speaker'].lower()}.mp3"
        response.stream_to_file(filename)
        return filename

    except Exception as e:
        print(f"Error generating segment {index}: {e}")
        return None


async def synthesize_multiple_segments(segments, config, max_concurrent=3):
    """
    Génère l'audio pour plusieurs segments en parallèle avec limite de concurrence.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Create output directory
    output_dir = Path(__file__).parent / "audio" / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Change to output directory
    original_cwd = os.getcwd()
    os.chdir(output_dir)

    try:
        # Process segments in batches
        generated_files = []
        for i in range(0, len(segments), max_concurrent):
            batch_segments = segments[i : i + max_concurrent]
            batch_tasks = []

            for j, segment in enumerate(batch_segments):
                segment_index = i + j
                task = synthesize_segment(segment, config, client, segment_index)
                batch_tasks.append(task)

            # Wait for batch to complete
            batch_results = await asyncio.gather(*batch_tasks)
            generated_files.extend([f for f in batch_results if f is not None])

            print(
                f"Completed batch {i // max_concurrent + 1}/{(len(segments) + max_concurrent - 1) // max_concurrent}"
            )

        return generated_files

    finally:
        os.chdir(original_cwd)


def save_audio_manifest(audio_files, segments_file, output_file):
    """Save manifest of generated audio files."""
    manifest = {
        "segments_file": segments_file,
        "audio_files": audio_files,
        "total_files": len(audio_files),
        "generated_at": str(asyncio.get_event_loop().time()),
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Synthesize podcast audio using OpenAI TTS"
    )
    parser.add_argument("--segments", required=True, help="Path to segments JSON file")
    parser.add_argument(
        "--output",
        help="Output manifest file path (default: audio_manifest_[category]_[date].json)",
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=3,
        help="Maximum concurrent API calls (default: 3)",
    )

    args = parser.parse_args()

    # Check OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        return 1

    # Load configuration
    try:
        config = load_config()
    except FileNotFoundError:
        print("Error: podcast_config_advanced.json not found")
        return 1

    # Load segments
    try:
        segments_data = load_segments(args.segments)
        segments = segments_data["segments"]
    except FileNotFoundError:
        print(f"Error: Segments file not found: {args.segments}")
        return 1
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in segments file: {args.segments}")
        return 1

    print(f"Starting audio synthesis for {len(segments)} segments...")
    print(f"Using TTS model: {config['tts_settings']['model']}")
    print(f"Maximum concurrent calls: {args.max_concurrent}")

    # Generate audio
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        audio_files = loop.run_until_complete(
            synthesize_multiple_segments(segments, config, args.max_concurrent)
        )

        loop.close()

    except Exception as e:
        print(f"Error during audio synthesis: {e}")
        return 1

    # Generate output filename
    if args.output:
        output_file = Path(args.output)
    else:
        # Extract category and date from segments file
        segments_path = Path(args.segments)
        category = "unknown"
        date = "unknown"

        if "segments_" in segments_path.name:
            parts = segments_path.stem.replace("segments_", "").split("_")
            if len(parts) >= 2:
                category = parts[0]
                date = parts[1]

        output_dir = Path(__file__).parent / "audio_manifests"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f"audio_manifest_{category}_{date}.json"

    # Save manifest
    save_audio_manifest(audio_files, args.segments, output_file)

    print(f"Audio synthesis completed successfully!")
    print(f"Generated {len(audio_files)} audio files")
    print(f"Manifest saved: {output_file}")

    # Estimate total duration
    total_chars = sum(len(seg["content"]) for seg in segments)
    estimated_seconds = total_chars / 20  # ~20 chars per second for TTS
    estimated_minutes = estimated_seconds / 60

    print(f"Total characters processed: {total_chars}")
    print(
        f"Estimated duration: {estimated_seconds:.0f} seconds ({estimated_minutes:.1f} minutes)"
    )

    return 0


if __name__ == "__main__":
    exit(main())
