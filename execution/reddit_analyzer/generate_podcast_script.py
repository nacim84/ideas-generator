import os
import re
import json
import argparse
from datetime import datetime
from pathlib import Path


def load_config():
    """Load podcast configuration from JSON file."""
    config_path = Path(__file__).parent / "podcast_config_advanced.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_text(text, normalization_rules):
    """Apply text normalization rules for better TTS pronunciation."""
    for original, normalized in normalization_rules.items():
        text = re.compile(r"\b" + re.escape(original) + r"\b", re.IGNORECASE).sub(
            normalized, text
        )
    return text


def read_analysis_file(category):
    """Read the analysis markdown file for the given category."""
    analysis_file = Path(__file__).parent / "latest_analysis.md"
    if not analysis_file.exists():
        raise FileNotFoundError(f"Analysis file not found: {analysis_file}")

    with open(analysis_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract category-specific content if needed
    if category:
        # Simple parsing - in real implementation, this would be more sophisticated
        lines = content.split("\n")
        category_section = []
        in_category_section = False

        for line in lines:
            if f"## {category}" in line:
                in_category_section = True
                category_section.append(line)
            elif (
                in_category_section
                and line.startswith("## ")
                and f"## {category}" not in line
            ):
                break
            elif in_category_section:
                category_section.append(line)

        content = "\n".join(category_section) if category_section else content

    return content


def create_podcast_structure(content, category, config):
    """Create podcast script structure with multi-speaker format."""
    segments = []

    # Parse content and create segments
    lines = content.split("\n")
    current_segment = ""
    segment_type = "HOST"

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Determine speaker based on content type
        if line.startswith("#"):
            segment_type = "HOST"
        elif line.startswith("##"):
            segment_type = "EXPERT"
        elif line.startswith("-") or line.startswith("*"):
            segment_type = "EXPERT"
        else:
            segment_type = "HOST"

        # Apply text normalization
        normalized_line = normalize_text(
            line, config["content_strategy"]["text_normalization"]
        )

        if len(current_segment) + len(normalized_line) + 1 < 4000:  # Respect TTS limits
            current_segment += normalized_line + " "
        else:
            if current_segment:
                segments.append(
                    {
                        "speaker": segment_type,
                        "content": current_segment.strip(),
                        "emphasis": extract_emphasis_words(current_segment),
                    }
                )
            current_segment = normalized_line + " "

    # Add final segment
    if current_segment:
        segments.append(
            {
                "speaker": "HOST",
                "content": current_segment.strip(),
                "emphasis": extract_emphasis_words(current_segment),
            }
        )

    return {
        "title": f"Idées Business du {datetime.now().strftime('%d %B %Y')} - {category}",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "category": category,
        "duration_target": config["content_strategy"]["max_episode_duration"],
        "segments": segments,
    }


def extract_emphasis_words(text):
    """Extract words that should be emphasized (capitalized or important terms)."""
    words = re.findall(r"\b[A-Z]{2,}\b|\$\d+[MK]|\b\w*[A-Z]\w*\b", text)
    return list(set(words))[:5]  # Limit to top 5 emphasis words


def generate_intro_text(category, config):
    """Generate podcast introduction text."""
    intros = [
        f"Bienvenue dans cette analyse quotidienne des opportunités business du {datetime.now().strftime('%d %B %Y')}. Aujourd'hui, nous explorons les tendances les plus prometteuses découvertes dans notre communauté {category}.",
        f"Bonjour et bienvenue dans les idées business du jour. {datetime.now().strftime('%d %B %Y')}. Focus aujourd'hui sur les opportunités identifiées dans la catégorie {category}.",
        f"Welcome to today's business insights. {datetime.now().strftime('%B %d, %Y')}. We're diving into the most interesting opportunities from our {category} community analysis.",
    ]
    return intros[0]  # Use first intro for now


def generate_outro_text():
    """Generate podcast conclusion text."""
    outros = [
        "Merci d'avoir écouté cette analyse. Retrouvez les détails complets de ces idées sur notre site web. À demain pour de nouvelles opportunités business !",
        "Merci pour votre écoute. Pour en savoir plus sur ces opportunités business, consultez notre rapport complet. À très bientôt !",
        "Thank you for listening. Find detailed information about these business opportunities on our website. See you tomorrow for more insights!",
    ]
    return outros[0]  # Use first outro for now


def main():
    parser = argparse.ArgumentParser(
        description="Generate podcast script from business analysis"
    )
    parser.add_argument(
        "--category", required=True, help="Category to generate podcast for"
    )
    parser.add_argument(
        "--output",
        help="Output file path (default: scripts/podcast_script_[category]_[date].json)",
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config()

    # Read analysis file
    try:
        content = read_analysis_file(args.category)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1

    # Create podcast structure
    podcast_data = create_podcast_structure(content, args.category, config)

    # Add intro and outro
    podcast_data["intro"] = generate_intro_text(args.category, config)
    podcast_data["outro"] = generate_outro_text()

    # Generate output filename
    if args.output:
        output_file = Path(args.output)
    else:
        output_dir = Path(__file__).parent / "scripts"
        output_dir.mkdir(exist_ok=True)
        output_file = (
            output_dir
            / f"podcast_script_{args.category}_{datetime.now().strftime('%Y%m%d')}.json"
        )

    # Save podcast script
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(podcast_data, f, ensure_ascii=False, indent=2)

    print(f"Podcast script generated successfully: {output_file}")
    print(f"Total segments: {len(podcast_data['segments'])}")
    print(f"Duration estimate: ~{len(podcast_data['segments']) * 30} seconds")

    return 0


if __name__ == "__main__":
    exit(main())
