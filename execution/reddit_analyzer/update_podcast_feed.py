import os
import json
import argparse
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from xml.dom import minidom


def load_podcast_metadata(episode_file):
    """Load podcast metadata from episode JSON file."""
    metadata_file = Path(episode_file).with_suffix(".json")
    if not metadata_file.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_file}")

    with open(metadata_file, "r", encoding="utf-8") as f:
        return json.load(f)


def create_rss_feed(episodes_dir, output_file):
    """Create RSS feed for all podcast episodes."""

    # Find all episode files
    episode_files = list(Path(episodes_dir).glob("*.mp3"))
    if not episode_files:
        print("No episode files found")
        return

    # Sort by date (newest first)
    episode_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    # Create RSS root
    rss = ET.Element("rss")
    rss.set("xmlns:itunes", "http://www.itunes.com/dtds/podcast-1.0.dtd")
    rss.set("version", "2.0")

    # Create channel
    channel = ET.SubElement(rss, "channel")

    # Channel metadata
    title = ET.SubElement(channel, "title")
    title.text = "Idées Business Quotidiennes"

    description = ET.SubElement(channel, "description")
    description.text = "Analyses quotidiennes automatisées des opportunités business découvertes sur Reddit"

    language = ET.SubElement(channel, "language")
    language.text = "fr"

    author = ET.SubElement(channel, "itunes:author")
    author.text = "AI Business Ideas Generator"

    summary = ET.SubElement(channel, "itunes:summary")
    summary.text = "Podcast automatisé des meilleures idées business du jour, basé sur l'analyse de communautés professionnelles"

    # Category
    category = ET.SubElement(channel, "itunes:category")
    category.set("text", "Business")

    # Link
    link = ET.SubElement(channel, "link")
    link.text = "https://github.com/your-repo/ideas-generator"

    # Generate episodes
    for episode_file in episode_files[:10]:  # Limit to last 10 episodes
        try:
            metadata = load_podcast_metadata(episode_file)

            # Create item
            item = ET.SubElement(channel, "item")

            # Title
            ep_title = ET.SubElement(item, "title")
            ep_title.text = metadata["title"]

            # Description
            description = ET.SubElement(item, "description")
            description.text = f"Épisode du {metadata['date']} - Analyse de la catégorie {metadata['category']}"

            # Pub date
            pub_date = ET.SubElement(item, "pubDate")
            pub_date.text = datetime.fromtimestamp(metadata["created_at"]).strftime(
                "%a, %d %b %Y %H:%M:%S GMT"
            )

            # GUID
            guid = ET.SubElement(item, "guid")
            guid.set("isPermaLink", "false")
            guid.text = f"episode-{metadata['date']}-{metadata['category']}"

            # Enclosure (audio file)
            enclosure = ET.SubElement(item, "enclosure")
            enclosure.set(
                "url", f"https://your-domain.com/podcasts/{episode_file.name}"
            )
            enclosure.set("length", str(metadata["duration_ms"]))
            enclosure.set("type", "audio/mpeg")

            # iTunes specific
            itunes_title = ET.SubElement(item, "itunes:title")
            itunes_title.text = metadata["title"]

            itunes_duration = ET.SubElement(item, "itunes:duration")
            duration_minutes = int(metadata["duration_ms"] / 60000)
            duration_seconds = int((metadata["duration_ms"] % 60000) / 1000)
            itunes_duration.text = f"{duration_minutes:02d}:{duration_seconds:02d}"

            itunes_summary = ET.SubElement(item, "itunes:summary")
            itunes_summary.text = f"Épisode du {metadata['date']} - Analyse de la catégorie {metadata['category']}"

            itunes_episode = ET.SubElement(item, "itunes:episode")
            itunes_episode.text = metadata["date"]

            itunes_season = ET.SubElement(item, "itunes:season")
            itunes_season.text = "1"

        except Exception as e:
            print(f"Error processing {episode_file}: {e}")
            continue

    # Pretty print XML
    rough_string = ET.tostring(rss, "utf-8")
    parsed = minidom.parseString(rough_string)
    pretty_xml = parsed.toprettyxml(indent="  ")

    # Save RSS feed
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(pretty_xml)

    print(f"RSS feed created successfully: {output_file}")
    print(f"Total episodes: {len([item for item in channel.findall('item')])}")


def update_rss_with_new_episode(episode_file, rss_file):
    """Update existing RSS feed with new episode."""

    if not Path(rss_file).exists():
        print(f"RSS feed not found: {rss_file}")
        return

    # Load existing RSS
    tree = ET.parse(rss_file)
    root = tree.getroot()
    channel = root.find("channel")

    # Get new episode metadata
    try:
        metadata = load_podcast_metadata(episode_file)
    except Exception as e:
        print(f"Error loading episode metadata: {e}")
        return

    # Create new item
    item = ET.SubElement(channel, "item")

    # Title
    ep_title = ET.SubElement(item, "title")
    ep_title.text = metadata["title"]

    # Description
    description = ET.SubElement(item, "description")
    description.text = f"Épisode du {metadata['date']} - Analyse de la catégorie {metadata['category']}"

    # Pub date
    pub_date = ET.SubElement(item, "pubDate")
    pub_date.text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")

    # GUID
    guid = ET.SubElement(item, "guid")
    guid.set("isPermaLink", "false")
    guid.text = f"episode-{metadata['date']}-{metadata['category']}"

    # Enclosure (audio file)
    enclosure = ET.SubElement(item, "enclosure")
    enclosure.set("url", f"https://your-domain.com/podcasts/{episode_file.name}")
    enclosure.set("length", str(metadata["duration_ms"]))
    enclosure.set("type", "audio/mpeg")

    # iTunes specific
    itunes_title = ET.SubElement(item, "itunes:title")
    itunes_title.text = metadata["title"]

    itunes_duration = ET.SubElement(item, "itunes:duration")
    duration_minutes = int(metadata["duration_ms"] / 60000)
    duration_seconds = int((metadata["duration_ms"] % 60000) / 1000)
    itunes_duration.text = f"{duration_minutes:02d}:{duration_seconds:02d}"

    itunes_summary = ET.SubElement(item, "itunes:summary")
    itunes_summary.text = f"Épisode du {metadata['date']} - Analyse de la catégorie {metadata['category']}"

    itunes_episode = ET.SubElement(item, "itunes:episode")
    itunes_episode.text = metadata["date"]

    itunes_season = ET.SubElement(item, "itunes:season")
    itunes_season.text = "1"

    # Save updated RSS
    tree.write(rss_file, encoding="utf-8", xml_declaration=True)

    print(f"RSS feed updated successfully: {rss_file}")
    print(f"Added episode: {metadata['title']}")


def main():
    parser = argparse.ArgumentParser(description="Update podcast RSS feed")
    parser.add_argument("--new-episode", help="Path to new episode MP3 file")
    parser.add_argument("--episodes-dir", help="Directory containing all episodes")
    parser.add_argument("--output", help="Output RSS file path (default: podcast.xml)")
    parser.add_argument("--update-existing", help="Update existing RSS feed")

    args = parser.parse_args()

    if args.new_episode:
        # Update existing RSS with new episode
        rss_file = args.update_existing or "podcast.xml"
        update_rss_with_new_episode(args.new_episode, rss_file)

    elif args.episodes_dir:
        # Create new RSS feed from all episodes
        output_file = args.output or "podcast.xml"
        create_rss_feed(args.episodes_dir, output_file)

    else:
        print("Error: Must specify either --new-episode or --episodes-dir")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
