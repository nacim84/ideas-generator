import nltk
import json
import argparse
from pathlib import Path


def ensure_nltk_data():
    """Ensure required NLTK data is downloaded."""
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        print("Downloading NLTK punkt data...")
        nltk.download("punkt", quiet=True)


def semantic_chunking(text, max_chars=4000):
    """
    Découpe le texte en segments < max_chars sans couper les phrases.
    """
    ensure_nltk_data()
    sentences = nltk.sent_tokenize(text, language="french")
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        # Vérification prédictive de la longueur
        if len(current_chunk) + len(sentence) + 1 <= max_chars:
            current_chunk += sentence + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " "

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def load_podcast_script(script_file):
    """Load podcast script from JSON file."""
    with open(script_file, "r", encoding="utf-8") as f:
        return json.load(f)


def create_segments(podcast_script, max_chars=4000):
    """Create segments from podcast script with smart chunking."""
    all_content = []

    # Add intro
    if podcast_script.get("intro"):
        all_content.append(
            {"content": podcast_script["intro"], "speaker": "HOST", "type": "intro"}
        )

    # Process main segments
    for i, segment in enumerate(podcast_script["segments"]):
        segment_content = {
            "content": segment["content"],
            "speaker": segment["speaker"],
            "type": "main",
            "original_index": i,
            "emphasis": segment.get("emphasis", []),
        }
        all_content.append(segment_content)

    # Add outro
    if podcast_script.get("outro"):
        all_content.append(
            {"content": podcast_script["outro"], "speaker": "HOST", "type": "outro"}
        )

    # Apply semantic chunking to main content only
    final_segments = []

    # Handle intro and outro separately (should fit in one segment each)
    for content in all_content:
        if content["type"] in ["intro", "outro"]:
            final_segments.append(content)
        else:  # Main content - apply semantic chunking
            chunks = semantic_chunking(content["content"], max_chars)
            for j, chunk in enumerate(chunks):
                final_segments.append(
                    {
                        "content": chunk.strip(),
                        "speaker": content["speaker"],
                        "type": "main",
                        "original_index": content["original_index"],
                        "chunk_index": j,
                        "emphasis": content.get("emphasis", []),
                    }
                )

    return final_segments


def save_segments(segments, output_file):
    """Save segments to JSON file."""
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "metadata": {
                    "total_segments": len(segments),
                    "total_chars": sum(len(seg["content"]) for seg in segments),
                    "estimated_duration": len(segments)
                    * 30,  # 30 seconds per segment estimate
                },
                "segments": segments,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )


def main():
    parser = argparse.ArgumentParser(
        description="Apply semantic segmentation to podcast script"
    )
    parser.add_argument(
        "--script", required=True, help="Path to podcast script JSON file"
    )
    parser.add_argument(
        "--output", help="Output file path (default: segments_[category]_[date].json)"
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=4000,
        help="Maximum characters per segment (default: 4000)",
    )

    args = parser.parse_args()

    # Load podcast script
    try:
        podcast_script = load_podcast_script(args.script)
    except FileNotFoundError:
        print(f"Error: Podcast script file not found: {args.script}")
        return 1
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in podcast script file: {args.script}")
        return 1

    # Create segments
    segments = create_segments(podcast_script, args.max_chars)

    # Generate output filename
    if args.output:
        output_file = Path(args.output)
    else:
        category = podcast_script.get("category", "unknown")
        date = podcast_script.get("date", datetime.now().strftime("%Y%m%d"))
        output_dir = Path(__file__).parent / "segments"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f"segments_{category}_{date}.json"

    # Save segments
    save_segments(segments, output_file)

    print(f"Segments generated successfully: {output_file}")
    print(f"Total segments: {len(segments)}")
    print(f"Total characters: {sum(len(seg['content']) for seg in segments)}")
    print(
        f"Estimated duration: ~{len(segments) * 30} seconds ({len(segments) * 30 / 60:.1f} minutes)"
    )

    # Show segment breakdown
    segment_types = {}
    for seg in segments:
        seg_type = seg["type"]
        segment_types[seg_type] = segment_types.get(seg_type, 0) + 1

    print(f"Segment breakdown: {segment_types}")

    return 0


if __name__ == "__main__":
    from datetime import datetime

    exit(main())
