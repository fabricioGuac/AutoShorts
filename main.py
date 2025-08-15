import argparse
from dotenv import load_dotenv

def main():
    # Env set up
    load_dotenv()

    # Parses the arguments
    parser = argparse.ArgumentParser(description="AI Video Generator Entry Point")
    parser.add_argument(
        "--cron",
        action="store_true",
        help="Run scheduled cron jobs (check if any post is scheduled at this hour)"
    )
    args = parser.parse_args()

    # Checks the argument to see if it should run the cli or just the scheduled check
    if args.cron:
        from src.scheduler.cron_tasks import post_scheduled_content
        post_scheduled_content()
    else:
        from src.cli import cli_main
        cli_main()

# Runs main() only when this script is executed directly (e.g, via terminal or cron),
# and prevents it from running on import
if __name__ == "__main__":
    main()