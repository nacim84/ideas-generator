import subprocess
import os
import time
from pathlib import Path

def run_command(command):
    """Runs a command and prints its output."""
    print(f"--- Running command: {' '.join(command)} ---")
    result = subprocess.run(command, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {result.returncode}")
    return result

def check_file_exists(path, max_wait_seconds=60):
    """Checks if a file exists, waiting up to a max duration."""
    start_time = time.time()
    while not os.path.exists(path):
        if time.time() - start_time > max_wait_seconds:
            return False
        time.sleep(1)
    return True

def main():
    """
    Main function to run the E2E tests.
    """
    try:
        # 1. Start services
        run_command(["docker-compose", "up", "-d", "--build"])

        # 2. Execute the application logic inside the container
        run_command(["docker-compose", "exec", "app", "python", "run_graph.py"])

        # 3. Verify the outputs
        print("--- Verifying outputs ---")
        
        # Load config to know which categories to check
        config_path = Path("execution/reddit_analyzer/config.json")
        with open(config_path, "r") as f:
            config = json.load(f)
        
        categories = list(set(sub['category'] for sub in config.get('subreddits', [])))
        
        all_checks_passed = True
        for category in categories:
            print(f"Checking outputs for category: {category}")
            
            # Check for analysis report
            report_path = Path(f"execution/reddit_analyzer/latest_analysis_{category}.md")
            if not check_file_exists(report_path):
                print(f"  [FAIL] Analysis report not found: {report_path}")
                all_checks_passed = False
            else:
                print(f"  [PASS] Analysis report found: {report_path}")

            # Check for podcast episode (we just check for one, assuming the date is today)
            episode_dir = Path("execution/reddit_analyzer/episodes")
            episodes = list(episode_dir.glob(f"episode_{category}_*.mp3"))
            if not episodes:
                print(f"  [FAIL] Podcast episode not found in: {episode_dir}")
                all_checks_passed = False
            else:
                print(f"  [PASS] Podcast episode found: {episodes[0]}")

        if all_checks_passed:
            print("\n--- E2E TESTS PASSED SUCCESSFULLY ---")
        else:
            print("\n--- E2E TESTS FAILED ---")

    except Exception as e:
        print(f"\n--- An error occurred during E2E tests: {e} ---")
    finally:
        # 4. Stop services
        print("\n--- Tearing down services ---")
        run_command(["docker-compose", "down"])

if __name__ == "__main__":
    import json
    main()
