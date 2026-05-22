"""
NightShift Work Agent: CLI entry point for browsing the marketplace and executing digital tasks.
"""

import argparse
import sys

from nightshift_client import NightShiftClient
from report_generator import ReportGenerator
from config import AGENT_NAME, VERSION


def cmd_browse_jobs(args, client, reporter):
    """
    Fetch and display all open jobs from the NightShift marketplace.
    Returns 0 on success, 1 on error.
    """
    print("Fetching jobs from the NightShift marketplace...")
    try:
        data = client.get_jobs()
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    jobs = _normalize_list(data, ("jobs", "data", "results"))
    if not jobs:
        print("No jobs found.")
        return 0

    headers = ["ID", "Title", "Status", "Type", "Created"]
    rows = []
    for job in jobs:
        rows.append([
            str(job.get("id", ""))[:14],
            str(job.get("title", job.get("name", "N/A")))[:48],
            str(job.get("status", "N/A")),
            str(job.get("type", job.get("category", "N/A"))),
            str(job.get("created_at", job.get("createdAt", "N/A")))[:19],
        ])

    reporter.print_table(
        headers,
        rows,
        title=f"Jobs on NightShift Marketplace  ({len(jobs)} found)",
    )
    return 0


def cmd_browse_services(args, client, reporter):
    """
    Fetch and display all available services from the NightShift marketplace.
    Returns 0 on success, 1 on error.
    """
    print("Fetching services from the NightShift marketplace...")
    try:
        data = client.get_services()
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    services = _normalize_list(data, ("services", "data", "results"))
    if not services:
        print("No services found.")
        return 0

    headers = ["ID", "Name", "Category", "Price", "Status"]
    rows = []
    for svc in services:
        rows.append([
            str(svc.get("id", ""))[:14],
            str(svc.get("name", svc.get("title", "N/A")))[:48],
            str(svc.get("category", svc.get("type", "N/A"))),
            str(svc.get("price", svc.get("cost", "N/A"))),
            str(svc.get("status", "N/A")),
        ])

    reporter.print_table(
        headers,
        rows,
        title=f"Services on NightShift Marketplace  ({len(services)} found)",
    )
    return 0


def cmd_browse_profiles(args, client, reporter):
    """
    Fetch and display all registered profiles from the NightShift marketplace.
    Returns 0 on success, 1 on error.
    """
    print("Fetching profiles from the NightShift marketplace...")
    try:
        data = client.get_profiles()
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    profiles = _normalize_list(data, ("profiles", "agents", "data", "results"))
    if not profiles:
        print("No profiles found.")
        return 0

    headers = ["ID", "Name", "Type", "Rating", "Location"]
    rows = []
    for profile in profiles:
        rows.append([
            str(profile.get("id", ""))[:14],
            str(profile.get("name", profile.get("username", "N/A")))[:40],
            str(profile.get("type", profile.get("role", "N/A"))),
            str(profile.get("rating", profile.get("score", "N/A"))),
            str(profile.get("location", profile.get("country", "N/A"))),
        ])

    reporter.print_table(
        headers,
        rows,
        title=f"Profiles on NightShift Marketplace  ({len(profiles)} found)",
    )
    return 0


def cmd_review(args, executor, reporter):
    """
    Clone and review a public GitHub repository using Claude.
    Saves a scored markdown report to the output directory.
    Returns 0 on success, 1 on error.
    """
    github_url = args.github_url
    print(f"\n{AGENT_NAME}: Code Review")
    print(f"Target: {github_url}\n")

    try:
        review_output = executor.review_code(github_url)
    except (RuntimeError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    repo_slug = github_url.rstrip("/").split("/")[-1]
    filename = reporter.make_filename("review", repo_slug)
    header = reporter.get_header(f"Code Review: {repo_slug}")
    full_report = header + review_output

    saved_path = reporter.save_report(filename, full_report)
    print("\n" + full_report)
    print(f"Report saved to: {saved_path}")
    return 0


def cmd_research(args, executor, reporter):
    """
    Generate a structured research brief on a topic using Claude.
    Saves the brief as a markdown file to the output directory.
    Returns 0 on success, 1 on error.
    """
    topic = args.topic
    print(f"\n{AGENT_NAME}: Research Brief")
    print(f"Topic: {topic}\n")

    try:
        research_output = executor.research(topic)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    filename = reporter.make_filename("research", topic)
    header = reporter.get_header(f"Research Brief: {topic}")
    full_report = header + research_output

    saved_path = reporter.save_report(filename, full_report)
    print("\n" + full_report)
    print(f"Report saved to: {saved_path}")
    return 0


def cmd_summarize(args, executor, reporter):
    """
    Read a local file and produce a structured summary using Claude.
    Saves the summary as a markdown file to the output directory.
    Returns 0 on success, 1 on error.
    """
    file_path = args.file
    print(f"\n{AGENT_NAME}: Document Summary")
    print(f"File: {file_path}\n")

    try:
        summary_output = executor.summarize(file_path)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    import os
    slug = os.path.basename(file_path)
    filename = reporter.make_filename("summary", slug)
    header = reporter.get_header(f"Summary: {slug}")
    full_report = header + summary_output

    saved_path = reporter.save_report(filename, full_report)
    print("\n" + full_report)
    print(f"Report saved to: {saved_path}")
    return 0


def _normalize_list(data, candidate_keys):
    """
    Extract a list from an API response that may be a bare list or a dict with a data key.
    Tries each key in candidate_keys before falling back to the raw value.
    """
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in candidate_keys:
            if key in data and isinstance(data[key], list):
                return data[key]
    return []


def build_parser():
    """Construct and return the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="agent",
        description=(
            f"{AGENT_NAME} v{VERSION}  |  "
            "Browse the NightShift marketplace and execute digital tasks powered by Claude."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python agent.py browse-jobs\n"
            "  python agent.py browse-services\n"
            "  python agent.py browse-profiles\n"
            "  python agent.py review https://github.com/user/repo\n"
            "  python agent.py research \"federated learning\"\n"
            "  python agent.py summarize report.pdf\n"
        ),
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {VERSION}"
    )

    subparsers = parser.add_subparsers(dest="command", metavar="<command>")

    subparsers.add_parser(
        "browse-jobs",
        help="List open jobs from the NightShift marketplace",
    )
    subparsers.add_parser(
        "browse-services",
        help="List available services from the marketplace",
    )
    subparsers.add_parser(
        "browse-profiles",
        help="List registered agent and human profiles",
    )

    review_parser = subparsers.add_parser(
        "review",
        help="Run a structured code review on a public GitHub repository",
    )
    review_parser.add_argument(
        "github_url",
        metavar="<github_url>",
        help="URL of the public GitHub repository to review",
    )

    research_parser = subparsers.add_parser(
        "research",
        help="Generate a structured research brief on any topic",
    )
    research_parser.add_argument(
        "topic",
        metavar="<topic>",
        help="The topic to research",
    )

    summarize_parser = subparsers.add_parser(
        "summarize",
        help="Produce a structured summary of a local file",
    )
    summarize_parser.add_argument(
        "file",
        metavar="<file>",
        help="Path to the local file to summarize",
    )

    return parser


def main():
    """
    Parse arguments and dispatch to the appropriate command handler.
    Returns an exit code suitable for passing to sys.exit.
    """
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    client = NightShiftClient()
    reporter = ReportGenerator()

    claude_commands = {"review", "research", "summarize"}
    executor = None
    if args.command in claude_commands:
        try:
            from task_executor import TaskExecutor
            executor = TaskExecutor()
        except ImportError as exc:
            print(
                f"Error: Could not import task executor. "
                f"Run 'pip install -r requirements.txt' first.\n{exc}",
                file=sys.stderr,
            )
            return 1
        except EnvironmentError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    if args.command == "browse-jobs":
        return cmd_browse_jobs(args, client, reporter)
    elif args.command == "browse-services":
        return cmd_browse_services(args, client, reporter)
    elif args.command == "browse-profiles":
        return cmd_browse_profiles(args, client, reporter)
    elif args.command == "review":
        return cmd_review(args, executor, reporter)
    elif args.command == "research":
        return cmd_research(args, executor, reporter)
    elif args.command == "summarize":
        return cmd_summarize(args, executor, reporter)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
