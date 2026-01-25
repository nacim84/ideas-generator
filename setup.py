#!/usr/bin/env python3
"""
Ideas Generator - Automated Setup Script
This script helps automate the configuration and setup of the podcast generation system.
"""

import os
import sys
import json
import shutil
import subprocess
import platform
from pathlib import Path
from datetime import datetime


def print_banner():
    """Print setup banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                 IDEAS GENERATOR - SETUP                     ║
    ║           Automated Configuration for Podcast System          ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print(
            f"❌ Python 3.11+ required. Current version: {version.major}.{version.minor}"
        )
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
    return True


def check_dependencies():
    """Check and install required dependencies"""
    print("\n🔍 Checking dependencies...")

    required_packages = [
        "openai",
        "pydub",
        "nltk",
        "python-dotenv",
        "requests",
        "tqdm",
        "librosa",
        "soundfile",
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package} - OK")
        except ImportError:
            print(f"❌ {package} - Missing")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n📦 Installing {len(missing_packages)} missing packages...")

        # Install requirements-audio.txt first
        try:
            subprocess.run(
                [sys.executable, "-m", "uv", "add", "-r", "requirements-audio.txt"],
                check=True,
                capture_output=True,
            )
            print("✅ Audio dependencies installed successfully")
        except subprocess.CalledProcessError:
            print("❌ Failed to install audio dependencies")
            return False

        # Install any remaining packages
        for package in missing_packages:
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", package],
                    check=True,
                    capture_output=True,
                )
                print(f"✅ {package} installed successfully")
            except subprocess.CalledProcessError:
                print(f"❌ Failed to install {package}")
                return False

    return True


def setup_nltk_data():
    """Download required NLTK data"""
    print("\n📚 Setting up NLTK data...")
    try:
        import nltk

        nltk.download("punkt", quiet=True)
        print("✅ NLTK data downloaded successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to download NLTK data: {e}")
        return False


def setup_directories():
    """Create required directories"""
    print("\n📁 Setting up directories...")

    directories = [
        "execution/reddit_analyzer/scripts",
        "execution/reddit_analyzer/segments",
        "execution/reddit_analyzer/audio/raw",
        "execution/reddit_analyzer/audio_manifests",
        "execution/reddit_analyzer/episodes",
        "execution/reddit_analyzer/assets",
        "execution/reddit_analyzer/assets/music",
        "execution/reddit_analyzer/assets/sound_effects",
        ".tmp",
    ]

    for directory in directories:
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

    return True


def setup_environment():
    """Setup environment configuration"""
    print("\n🔧 Setting up environment configuration...")

    # Copy .env.example to .env if it doesn't exist
    env_example = Path(".env.example")
    env_file = Path(".env")

    if not env_file.exists() and env_example.exists():
        print("📝 Creating .env file from template...")
        shutil.copy2(env_example, env_file)
        print("✅ .env file created. Please edit it with your API keys.")
    elif not env_file.exists():
        print("⚠️  No .env.example found. Creating empty .env file...")
        env_file.touch()
        print("✅ Empty .env file created. Please edit it with your API keys.")
    else:
        print("✅ .env file already exists")

    return True


def setup_gmail_auth():
    """Setup Gmail authentication"""
    print("\n📧 Setting up Gmail authentication...")

    credentials_path = Path("execution/reddit_analyzer/credentials.json")
    token_path = Path("execution/reddit_analyzer/token.json")

    if not credentials_path.exists():
        print("⚠️  Gmail credentials not found.")
        print("📋 To setup Gmail authentication:")
        print("   1. Go to https://console.cloud.google.com/")
        print("   2. Create a new project")
        print("   3. Enable Gmail API")
        print("   4. Create OAuth 2.0 credentials (Desktop app)")
        print(
            "   5. Download credentials.json and place it in execution/reddit_analyzer/"
        )
        print("   6. Run: uv run send_email.py --category 'B2B_MARKET'")
        return False

    if not token_path.exists():
        print("⚠️  Gmail token not found.")
        print("📋 To generate token:")
        print("   1. Run: uv run send_email.py --category 'B2B_MARKET'")
        print("   2. Follow the authentication flow")
        return False

    print("✅ Gmail authentication setup complete")
    return True


def test_api_keys():
    """Test API keys configuration"""
    print("\n🔑 Testing API keys...")

    # Test Gemini API
    try:
        import os

        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            print("✅ GEMINI_API_KEY configured")
        else:
            print("❌ GEMINI_API_KEY not found in environment")
    except Exception as e:
        print(f"❌ Error checking GEMINI_API_KEY: {e}")

    # Test OpenAI API
    try:
        import os

        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            print("✅ OPENAI_API_KEY configured")
        else:
            print("❌ OPENAI_API_KEY not found in environment")
    except Exception as e:
        print(f"❌ Error checking OPENAI_API_KEY: {e}")

    # Test email configuration
    try:
        import os

        email = os.getenv("RECIPIENT_EMAIL")
        if email:
            print(f"✅ RECIPIENT_EMAIL configured: {email}")
        else:
            print("❌ RECIPIENT_EMAIL not found in environment")
    except Exception as e:
        print(f"❌ Error checking RECIPIENT_EMAIL: {e}")

    return True


def run_tests():
    """Run basic tests to verify setup"""
    print("\n🧪 Running basic tests...")

    tests = []

    # Test imports
    try:
        import openai
        import nltk
        from pydub import AudioSegment

        tests.append(("Import dependencies", True))
    except Exception as e:
        tests.append(("Import dependencies", False))
        print(f"❌ Import test failed: {e}")

    # Test configuration files
    config_files = [
        "execution/reddit_analyzer/podcast_config_advanced.json",
        "execution/reddit_analyzer/requirements-audio.txt",
    ]

    for config_file in config_files:
        if Path(config_file).exists():
            tests.append((f"Config file: {config_file}", True))
        else:
            tests.append((f"Config file: {config_file}", False))
            print(f"❌ Missing config file: {config_file}")

    # Test directory structure
    required_dirs = [
        "execution/reddit_analyzer/scripts",
        "execution/reddit_analyzer/segments",
        "execution/reddit_analyzer/audio/raw",
        "execution/reddit_analyzer/episodes",
    ]

    for directory in required_dirs:
        if Path(directory).exists():
            tests.append((f"Directory: {directory}", True))
        else:
            tests.append((f"Directory: {directory}", False))
            print(f"❌ Missing directory: {directory}")

    # Print results
    print("\n📊 Test Results:")
    passed = 0
    total = len(tests)

    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {test_name}")
        if result:
            passed += 1

    print(f"\n🎯 Tests passed: {passed}/{total}")
    return passed == total


def generate_setup_report():
    """Generate a setup report"""
    print("\n📄 Generating setup report...")

    report = {
        "setup_timestamp": datetime.now().isoformat(),
        "platform": platform.system(),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "files": {},
        "directories": {},
        "configuration": {},
    }

    # Check files
    important_files = [
        ".env",
        "execution/reddit_analyzer/podcast_config_advanced.json",
        "execution/reddit_analyzer/requirements-audio.txt",
        "execution/reddit_analyzer/credentials.json",
        "execution/reddit_analyzer/token.json",
    ]

    for file_path in important_files:
        path = Path(file_path)
        report["files"][file_path] = {
            "exists": path.exists(),
            "size": path.stat().st_size if path.exists() else 0,
        }

    # Check directories
    important_dirs = [
        "execution/reddit_analyzer/scripts",
        "execution/reddit_analyzer/segments",
        "execution/reddit_analyzer/audio/raw",
        "execution/reddit_analyzer/audio_manifests",
        "execution/reddit_analyzer/episodes",
    ]

    for dir_path in important_dirs:
        path = Path(dir_path)
        report["directories"][dir_path] = {
            "exists": path.exists(),
            "file_count": len(list(path.glob("*"))) if path.exists() else 0,
        }

    # Check environment variables
    important_env_vars = ["GEMINI_API_KEY", "OPENAI_API_KEY", "RECIPIENT_EMAIL"]

    for env_var in important_env_vars:
        value = os.getenv(env_var)
        report["configuration"][env_var] = {
            "set": bool(value),
            "length": len(value) if value else 0,
        }

    # Save report
    report_file = Path("setup_report.json")
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"✅ Setup report saved to: {report_file}")
    return report


def main():
    """Main setup function"""
    print_banner()

    print("🚀 Starting automated setup...")

    # Setup steps
    steps = [
        ("Checking Python version", check_python_version),
        ("Installing dependencies", check_dependencies),
        ("Setting up NLTK data", setup_nltk_data),
        ("Creating directories", setup_directories),
        ("Setting up environment", setup_environment),
        ("Setting up Gmail authentication", setup_gmail_auth),
        ("Testing API keys", test_api_keys),
        ("Running tests", run_tests),
        ("Generating setup report", generate_setup_report),
    ]

    passed_steps = 0
    total_steps = len(steps)

    for step_name, step_func in steps:
        print(f"\n🔄 {step_name}...")
        try:
            if step_func():
                print(f"✅ {step_name} - SUCCESS")
                passed_steps += 1
            else:
                print(f"❌ {step_name} - FAILED")
        except Exception as e:
            print(f"❌ {step_name} - ERROR: {e}")

    # Final result
    print(f"\n{'=' * 60}")
    print(f"🎉 SETUP COMPLETE: {passed_steps}/{total_steps} steps passed")
    print(f"{'=' * 60}")

    if passed_steps == total_steps:
        print("\n🎊 All setup steps completed successfully!")
        print("\n📋 Next steps:")
        print("   1. Edit .env file with your API keys")
        print(
            "   2. Add Gmail credentials to execution/reddit_analyzer/credentials.json"
        )
        print("   3. Generate Gmail token by running: uv run send_email.py")
        print(
            "   4. Test the system: uv run generate_podcast_script.py --category 'B2B_MARKET'"
        )
        print("   5. Deploy to GitHub: git push origin main")

        print("\n🎯 Ready to generate your first podcast!")
        return True
    else:
        print(
            f"\n⚠️  {total_steps - passed_steps} steps failed. Please fix the issues above."
        )
        print("\n📋 Troubleshooting tips:")
        print("   - Check that all dependencies are installed")
        print("   - Verify your API keys are correctly set")
        print("   - Ensure all required directories exist")
        print("   - Review the setup_report.json for details")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
