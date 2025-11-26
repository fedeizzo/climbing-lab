"""
Command-line interface for Tindeq Exporter
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from .analytics import TindeqAnalytics
from .processor import TindeqBatchExport, TindeqSession
from .storage import TindeqStorage


def cmd_import(args):
    """Import Tindeq batch export or individual session"""
    import os

    storage = TindeqStorage(args.storage_dir)
    input_path = Path(args.path)

    try:
        if args.batch:
            # Import batch export using context manager
            print(f"Loading batch export: {args.path}")
            with TindeqBatchExport(args.path) as batch:
                print(f"Found {len(batch.session_zips)} sessions\n")

                for i, session_zip in enumerate(batch.session_zips):
                    print(f"[{i + 1}/{len(batch.session_zips)}] {session_zip.stem}")
                    session = batch.load_session(i)
                    storage.import_session(session)

                print(f"\n✓ Imported {len(batch.session_zips)} sessions")

        else:
            # Import single session using context manager
            print(f"Loading session: {args.path}")
            with TindeqSession(args.path) as session:
                storage.import_session(session)
                print("✓ Session imported")

        # Delete input zip if requested
        if args.delete_after:
            if input_path.exists():
                os.remove(input_path)
                print(f"✓ Deleted input file: {args.path}")
            else:
                print(f"⚠ Warning: Could not delete {args.path} (file not found)")

    except Exception as e:
        print(f"Error during import: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_list(args):
    """List all sessions"""
    storage = TindeqStorage(args.storage_dir)
    sessions = storage.list_sessions(tag=args.tag, start_date=args.from_date, end_date=args.to_date)

    if sessions.empty:
        print("No sessions found")
        return

    print(f"\nFound {len(sessions)} sessions:\n")
    for _, session in sessions.iterrows():
        print(f"  {session['date'][:19]}  {session['tag']:15}  {session['session_id']}")


def cmd_exercises(args):
    """List all exercises"""
    storage = TindeqStorage(args.storage_dir)
    exercises = storage.get_all_exercises()

    if not exercises:
        print("No exercises found")
        return

    print(f"\nFound {len(exercises)} unique exercises:\n")
    for ex in exercises:
        print(f"  - {ex}")


def cmd_progress(args):
    """Show progress for an exercise"""
    storage = TindeqStorage(args.storage_dir)

    try:
        progress = storage.get_exercise_progress(args.exercise, start_date=args.from_date, end_date=args.to_date)

        if progress.empty:
            print(f"No data found for exercise: {args.exercise}")
            return

        print(f"\nProgress for '{args.exercise}':\n")

        if args.format == "table":
            # Group by date and side for cleaner display
            summary = (
                progress.groupby(["date", "side"])
                .agg(
                    {
                        "avg_weight": "mean",
                        "peak_weight": "max",
                        "rfd2080": "mean",
                    }
                )
                .round(2)
            )
            print(summary)

        elif args.format == "csv":
            print(progress.to_csv(index=False))

        elif args.format == "json":
            print(progress.to_json(orient="records", indent=2))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_export(args):
    """Export data to CSV"""
    storage = TindeqStorage(args.storage_dir)

    if args.type == "sessions":
        df = storage.list_sessions(tag=args.tag, start_date=args.from_date, end_date=args.to_date)
        output_file = args.output or "sessions.csv"

    elif args.type == "progress":
        if not args.exercise:
            print(
                "Error: --exercise is required for progress export",
                file=sys.stderr,
            )
            sys.exit(1)

        df = storage.get_exercise_progress(args.exercise, start_date=args.from_date, end_date=args.to_date)
        output_file = args.output or f"{args.exercise}_progress.csv"

    else:
        print(f"Unknown export type: {args.type}", file=sys.stderr)
        sys.exit(1)

    df.to_csv(output_file, index=False)
    print(f"✓ Exported to {output_file}")


def cmd_stats(args):
    """Show session statistics"""
    storage = TindeqStorage(args.storage_dir)

    try:
        summary = storage.get_session_summary(args.session_id)
        print(f"\nSession: {summary['date']}")
        print(f"Tag: {summary['tag']}")
        print(f"Session ID: {args.session_id}\n")

        print("Exercises:")
        for ex in summary["exercises"]:
            print(f"  - {ex['name']}")

            if args.detailed:
                rep_stats, set_stats = storage.get_exercise_stats(args.session_id, ex["name"])

                if not set_stats.empty:
                    print("\n    Set stats:")
                    print(set_stats.to_string(index=False))
                    print()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_analyze(args):
    """Analyze training data"""
    storage = TindeqStorage(args.storage_dir)
    analytics = TindeqAnalytics(storage)

    if args.type == "consistency":
        result = analytics.analyze_consistency(days=args.days)

        print(f"\n📊 Training Consistency ({args.days} days)\n")
        print(f"Total sessions: {result['frequency']['total_sessions']}")
        print(f"Sessions per week: {result['frequency']['sessions_per_week']:.1f}")
        print(f"Days trained: {result['frequency']['days_trained']}")
        print(f"Training rate: {result['frequency']['training_rate']:.1f}%")
        print("\n🔥 Streak:")
        print(f"Current: {result['streak']['current_streak']} days")
        print(f"Longest: {result['streak']['longest_streak']} days")
        print(f"Last training: {result['streak']['last_training_date']}")
        print("\n🌅 Morning vs Evening:")
        print(
            f"Morning: {result['morning_evening_split']['morning_count']} "
            f"({result['morning_evening_split']['morning_pct']:.1f}%)"
        )
        print(
            f"Evening: {result['morning_evening_split']['evening_count']} "
            f"({result['morning_evening_split']['evening_pct']:.1f}%)"
        )

    elif args.type == "performance":
        if not args.exercise:
            print(
                "Error: --exercise is required for performance analysis",
                file=sys.stderr,
            )
            sys.exit(1)

        result = analytics.analyze_performance(args.exercise, args.metric, args.days)

        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

        print(f"\n📈 Performance Analysis: {result['exercise']}")
        print(f"Metric: {result['metric']}\n")
        print(f"Trend: {result['trend']['trend_direction']}")
        print(f"Change: {result['trend']['change_pct']:+.2f}%")
        print(f"Recent avg: {result['trend']['recent_avg']:.2f} kg")
        print(f"Early avg: {result['trend']['early_avg']:.2f} kg")
        print("\n⚖️  Left/Right Balance:")
        print(f"Left: {result['left_right_balance']['left_avg']:.2f} kg")
        print(f"Right: {result['left_right_balance']['right_avg']:.2f} kg")
        print(f"Asymmetry: {result['left_right_balance']['asymmetry_pct']:.2f}%")
        print(f"Stronger side: {result['left_right_balance']['stronger_side']}")

        if args.json:
            print("\n" + json.dumps(result, indent=2))

    elif args.type == "fatigue":
        if not args.session_id or not args.exercise:
            print(
                "Error: --session-id and --exercise are required for fatigue analysis",
                file=sys.stderr,
            )
            sys.exit(1)

        result = analytics.analyze_session_fatigue(args.session_id, args.exercise)

        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

        print(f"\n😓 Fatigue Analysis: {result['exercise']}")
        print(f"Session: {result['session_id']}\n")
        print("Peak Weight:")
        print(f"  First set: {result['fatigue_peak_weight']['first_set_avg']:.2f} kg")
        print(f"  Last set: {result['fatigue_peak_weight']['last_set_avg']:.2f} kg")
        print(f"  Change: {result['fatigue_peak_weight']['fatigue_pct']:+.2f}%")
        print(f"  Status: {result['fatigue_peak_weight']['fatigue_direction']}")
        print("\nRep Consistency:")
        print(f"  CV: {result['rep_consistency']['cv']:.2f}%")
        print(f"  Rating: {result['rep_consistency']['consistency_rating']}")

    elif args.type == "recovery":
        if not args.exercise:
            print(
                "Error: --exercise is required for recovery analysis",
                file=sys.stderr,
            )
            sys.exit(1)

        result = analytics.analyze_recovery(args.exercise, args.days)

        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

        print(f"\n💤 Recovery Analysis: {result['exercise']}")
        print(f"Period: {result['period_days']} days\n")
        print(f"Recovery Quality: {result['recovery_quality']['recovery_rating']}")
        print(f"Morning avg: {result['recovery_quality']['morning_avg']:.2f} kg")
        print(f"Evening avg: {result['recovery_quality']['evening_avg']:.2f} kg")
        print(f"Recovery: {result['recovery_quality']['avg_recovery_pct']:+.2f}%")
        print(f"\nPreferred time: {result['preferred_time']}")

    elif args.type == "compare":
        result = analytics.compare_exercises(days=args.days)

        print(f"\n🏆 Exercise Comparison ({args.days} days)\n")
        for ex in result["exercises"]:
            print(
                f"{ex['exercise']:30} {ex['avg_peak_weight']:6.2f} kg  "
                f"{ex['trend']:10}  {ex['change_pct']:+6.2f}%  "
                f"asymmetry: {ex['asymmetry_pct']:5.2f}%"
            )

        print(f"\nStrongest: {result['strongest_exercise']}")
        print(f"Most improved: {result['most_improved']}")

    elif args.type == "weakpoints":
        result = analytics.identify_weak_points(days=args.days)

        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

        print(f"\n🎯 Weak Points Analysis ({result['period_days']} days)\n")

        if result["declining_exercises"]:
            print("⚠️  Declining exercises:")
            for ex in result["declining_exercises"]:
                print(f"  - {ex['exercise']} ({ex['change_pct']:+.2f}%)")
            print()

        if result["high_asymmetry_exercises"]:
            print("⚠️  High asymmetry:")
            for ex in result["high_asymmetry_exercises"]:
                print(f"  - {ex['exercise']} ({ex['asymmetry_pct']:.2f}%)")
            print()

        if result["weakest_exercise"]:
            print(
                f"⚠️  Weakest: {result['weakest_exercise']['exercise']} "
                f"({result['weakest_exercise']['avg_peak_weight']:.2f} kg)"
            )
            print()

        if result["recommendations"]:
            print("💡 Recommendations:")
            for rec in result["recommendations"]:
                print(f"  • {rec}")


def cmd_report(args):
    """Generate training reports"""
    storage = TindeqStorage(args.storage_dir)
    analytics = TindeqAnalytics(storage)

    if args.type == "weekly":
        result = analytics.generate_weekly_report(weeks=args.weeks)

        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

        print(f"\n📅 Weekly Report ({result['period']})")
        print(f"Period: {result['start_date']} to {result['end_date']}\n")
        print(f"Total sessions: {result['total_sessions']}")
        print(f"Avg sessions/week: {result['avg_sessions_per_week']:.1f}\n")

        print("Weekly breakdown:")
        for week in result["weekly_sessions"]:
            print(
                f"  Week {week['week']}: {week['session_count']} sessions "
                f"({week['week_start'].strftime('%Y-%m-%d')} - {week['week_end'].strftime('%Y-%m-%d')})"
            )

        if args.json:
            print("\n" + json.dumps(result, indent=2, default=str))

    elif args.type == "monthly":
        result = analytics.generate_monthly_report(months=args.months)

        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

        print(f"\n📅 Monthly Report ({result['period']})")
        print(f"Period: {result['start_date']} to {result['end_date']}\n")
        print(f"Total sessions: {result['total_sessions']}\n")

        print("Monthly breakdown:")
        for month in result["monthly_sessions"]:
            print(f"  {month['month']}: {month['session_count']} sessions")

        print("\n📊 Consistency:")
        print(f"Current streak: {result['consistency']['streak']['current_streak']} days")
        print(f"Training rate: {result['consistency']['frequency']['training_rate']:.1f}%")

        print("\n📈 Exercise Trends:")
        for exercise, trend in result["exercise_trends"].items():
            print(f"  {exercise:30} {trend['trend_direction']:10} {trend['change_pct']:+6.2f}%")

        if args.json:
            print("\n" + json.dumps(result, indent=2, default=str))


def cmd_peakload_import(args):
    """Import peakload data from CSV"""
    storage = TindeqStorage(args.storage_dir)

    try:
        imported = storage.import_peakload_csv(args.csv_path)
        print(f"✓ Imported {imported} peakload entries from {args.csv_path}")
    except Exception as e:
        print(f"✗ Failed to import peakload data: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_peakload_list(args):
    """List peakload entries"""
    storage = TindeqStorage(args.storage_dir)

    peakloads = storage.list_peakloads(start_date=args.from_date, end_date=args.to_date)

    if not peakloads:
        print("No peakload data found")
        return

    if args.format == "json":
        print(json.dumps(peakloads, indent=2, default=str))
    elif args.format == "csv":
        df = pd.DataFrame(peakloads)
        print(df.to_csv(index=False))
    else:  # table
        print(f"\nPeakload Entries ({len(peakloads)} total):\n")
        print(f"{'Date':<20} {'Tag':<20} {'Left (kg)':<12} {'Right (kg)':<12} {'Comment'}")
        print("-" * 100)
        for entry in peakloads:
            date_str = entry["date"][:16] if entry["date"] else "N/A"
            tag = entry["tag"][:19] if entry["tag"] else "N/A"
            left = f"{entry['left_max_weight']:.2f}" if entry["left_max_weight"] else "N/A"
            right = f"{entry['right_max_weight']:.2f}" if entry["right_max_weight"] else "N/A"
            comment = entry["comment"][:40] if entry["comment"] else ""
            print(f"{date_str:<20} {tag:<20} {left:<12} {right:<12} {comment}")


def cmd_peakload_trend(args):
    """Show peakload trends"""
    storage = TindeqStorage(args.storage_dir)

    df = storage.get_peakload_timeseries(start_date=args.from_date, end_date=args.to_date)

    if df.empty:
        print("No peakload data found")
        return

    # Calculate statistics
    print("\nPeakload Trend Analysis\n")
    print(f"Period: {df['date'].min()} to {df['date'].max()}")
    print(f"Total entries: {len(df)}\n")

    # Left hand stats
    if df["left_max_weight"].notna().any():
        left_mean = df["left_max_weight"].mean()
        left_max = df["left_max_weight"].max()
        left_min = df["left_max_weight"].min()
        left_last = df["left_max_weight"].iloc[-1]
        left_first = df["left_max_weight"].iloc[0]
        left_change = ((left_last - left_first) / left_first * 100) if left_first > 0 else 0

        print("Left Hand:")
        print(f"  Current: {left_last:.2f} kg")
        print(f"  Average: {left_mean:.2f} kg")
        print(f"  Max: {left_max:.2f} kg")
        print(f"  Min: {left_min:.2f} kg")
        print(f"  Change: {left_change:+.1f}%\n")

    # Right hand stats
    if df["right_max_weight"].notna().any():
        right_mean = df["right_max_weight"].mean()
        right_max = df["right_max_weight"].max()
        right_min = df["right_max_weight"].min()
        right_last = df["right_max_weight"].iloc[-1]
        right_first = df["right_max_weight"].iloc[0]
        right_change = ((right_last - right_first) / right_first * 100) if right_first > 0 else 0

        print("Right Hand:")
        print(f"  Current: {right_last:.2f} kg")
        print(f"  Average: {right_mean:.2f} kg")
        print(f"  Max: {right_max:.2f} kg")
        print(f"  Min: {right_min:.2f} kg")
        print(f"  Change: {right_change:+.1f}%\n")

    # Balance
    if df["left_max_weight"].notna().any() and df["right_max_weight"].notna().any():
        balance = (df["left_max_weight"] / df["right_max_weight"] * 100).mean()
        print(f"Average Balance: {balance:.1f}% (Left/Right ratio)")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog="tindeq-exporter",
        description="Import and analyze Tindeq finger training data",
    )

    parser.add_argument(
        "--storage-dir",
        default="tindeq_data",
        help="Storage directory (default: tindeq_data)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Import command
    import_parser = subparsers.add_parser("import", help="Import Tindeq data")
    import_parser.add_argument("path", help="Path to batch zip or session zip")
    import_parser.add_argument(
        "--batch",
        action="store_true",
        help="Import as batch export (multiple sessions)",
    )
    import_parser.add_argument(
        "--delete-after",
        action="store_true",
        help="Delete the input zip file after successful import",
    )
    import_parser.set_defaults(func=cmd_import)

    # List command
    list_parser = subparsers.add_parser("list", help="List sessions")
    list_parser.add_argument("--tag", help="Filter by tag")
    list_parser.add_argument("--from-date", help="Start date (YYYY-MM-DD)")
    list_parser.add_argument("--to-date", help="End date (YYYY-MM-DD)")
    list_parser.set_defaults(func=cmd_list)

    # Exercises command
    exercises_parser = subparsers.add_parser("exercises", help="List all exercises")
    exercises_parser.set_defaults(func=cmd_exercises)

    # Progress command
    progress_parser = subparsers.add_parser("progress", help="Show exercise progress")
    progress_parser.add_argument("exercise", help="Exercise name")
    progress_parser.add_argument("--from-date", help="Start date (YYYY-MM-DD)")
    progress_parser.add_argument("--to-date", help="End date (YYYY-MM-DD)")
    progress_parser.add_argument(
        "--format",
        choices=["table", "csv", "json"],
        default="table",
        help="Output format",
    )
    progress_parser.set_defaults(func=cmd_progress)

    # Export command
    export_parser = subparsers.add_parser("export", help="Export data to CSV")
    export_parser.add_argument("type", choices=["sessions", "progress"], help="What to export")
    export_parser.add_argument("--exercise", help="Exercise name (for progress export)")
    export_parser.add_argument("--tag", help="Filter by tag")
    export_parser.add_argument("--from-date", help="Start date (YYYY-MM-DD)")
    export_parser.add_argument("--to-date", help="End date (YYYY-MM-DD)")
    export_parser.add_argument("-o", "--output", help="Output file")
    export_parser.set_defaults(func=cmd_export)

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show session statistics")
    stats_parser.add_argument("session_id", help="Session ID")
    stats_parser.add_argument(
        "-d",
        "--detailed",
        action="store_true",
        help="Show detailed stats per exercise",
    )
    stats_parser.set_defaults(func=cmd_stats)

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze training data")
    analyze_parser.add_argument(
        "type",
        choices=[
            "consistency",
            "performance",
            "fatigue",
            "recovery",
            "compare",
            "weakpoints",
        ],
        help="Type of analysis",
    )
    analyze_parser.add_argument(
        "--exercise",
        help="Exercise name (required for performance/fatigue/recovery)",
    )
    analyze_parser.add_argument("--session-id", help="Session ID (required for fatigue)")
    analyze_parser.add_argument(
        "--metric",
        choices=["peak_weight", "avg_weight", "rfd2080"],
        default="peak_weight",
        help="Metric to analyze (default: peak_weight)",
    )
    analyze_parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to look back (default: 30)",
    )
    analyze_parser.add_argument("--json", action="store_true", help="Output as JSON")
    analyze_parser.set_defaults(func=cmd_analyze)

    # Report command
    report_parser = subparsers.add_parser("report", help="Generate training reports")
    report_parser.add_argument("type", choices=["weekly", "monthly"], help="Type of report")
    report_parser.add_argument(
        "--weeks",
        type=int,
        default=4,
        help="Number of weeks for weekly report (default: 4)",
    )
    report_parser.add_argument(
        "--months",
        type=int,
        default=3,
        help="Number of months for monthly report (default: 3)",
    )
    report_parser.add_argument("--json", action="store_true", help="Output as JSON")
    report_parser.set_defaults(func=cmd_report)

    # Peakload commands
    peakload_parser = subparsers.add_parser("peakload", help="Manage peakload data")
    peakload_subparsers = peakload_parser.add_subparsers(dest="peakload_cmd", required=True)

    # Peakload import
    peakload_import_parser = peakload_subparsers.add_parser("import", help="Import peakload CSV")
    peakload_import_parser.add_argument("csv_path", help="Path to CSV file with peakload data")
    peakload_import_parser.set_defaults(func=cmd_peakload_import)

    # Peakload list
    peakload_list_parser = peakload_subparsers.add_parser("list", help="List peakload entries")
    peakload_list_parser.add_argument("--from-date", help="Start date (YYYY-MM-DD)")
    peakload_list_parser.add_argument("--to-date", help="End date (YYYY-MM-DD)")
    peakload_list_parser.add_argument(
        "--format",
        choices=["table", "csv", "json"],
        default="table",
        help="Output format",
    )
    peakload_list_parser.set_defaults(func=cmd_peakload_list)

    # Peakload trend
    peakload_trend_parser = peakload_subparsers.add_parser("trend", help="Show peakload trends")
    peakload_trend_parser.add_argument("--from-date", help="Start date (YYYY-MM-DD)")
    peakload_trend_parser.add_argument("--to-date", help="End date (YYYY-MM-DD)")
    peakload_trend_parser.set_defaults(func=cmd_peakload_trend)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
