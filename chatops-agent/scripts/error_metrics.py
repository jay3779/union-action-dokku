"""
Error metrics query script for WhatsApp ChatOps Agent.

Queries the health endpoints to retrieve and display error metrics,
useful for monitoring and debugging.
"""

import requests
import json
import sys
import os
from datetime import datetime
from typing import Optional

# Configure agent URL from environment or default
AGENT_URL = os.getenv("AGENT_URL", "http://localhost:8080")


def get_health_metrics() -> Optional[dict]:
    """
    Query the /health endpoint for basic error metrics.
    
    Returns:
        Dictionary with health metrics or None on error
    """
    try:
        response = requests.get(f"{AGENT_URL}/health", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"❌ Error querying health endpoint: {e}", file=sys.stderr)
        return None


def get_detailed_errors() -> Optional[dict]:
    """
    Query the /health/errors endpoint for detailed error information.
    
    Returns:
        Dictionary with detailed error information or None on error
    """
    try:
        response = requests.get(f"{AGENT_URL}/health/errors", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"❌ Error querying detailed errors endpoint: {e}", file=sys.stderr)
        return None


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} hours"


def display_health_metrics(metrics: dict):
    """Display basic health metrics in a readable format."""
    print("\n" + "=" * 60)
    print("📊 Agent Health Metrics")
    print("=" * 60)
    
    print(f"\n✅ Status: {metrics.get('status', 'unknown')}")
    print(f"🕐 Timestamp: {metrics.get('timestamp', 'N/A')}")
    
    error_metrics = metrics.get('error_metrics', {})
    print(f"\n📈 Error Statistics:")
    print(f"  Total Errors: {error_metrics.get('total_errors', 0)}")
    print(f"  Recent Errors: {error_metrics.get('recent_errors_count', 0)}")
    
    time_since_reset = error_metrics.get('time_since_reset_seconds', 0)
    print(f"  Tracking Duration: {format_duration(time_since_reset)}")
    
    errors_by_category = error_metrics.get('errors_by_category', {})
    print(f"\n📂 Errors by Category:")
    for category, count in sorted(errors_by_category.items()):
        bar = "█" * min(count, 50)
        print(f"  {category.capitalize():15} {count:4d} {bar}")


def display_detailed_errors(data: dict, limit: int = 10):
    """Display detailed error information."""
    print("\n" + "=" * 60)
    print(f"🔍 Recent Errors (last {limit})")
    print("=" * 60)
    
    recent_errors = data.get('recent_errors', [])
    
    if not recent_errors:
        print("\n✅ No errors recorded!")
        return
    
    # Display last N errors
    errors_to_show = recent_errors[-limit:]
    
    for i, error in enumerate(errors_to_show, 1):
        category = error.get('category', 'unknown')
        timestamp = error.get('timestamp', 'N/A')
        details = error.get('details', {})
        
        print(f"\n{i}. [{category.upper()}] @ {timestamp}")
        
        if details:
            print(f"   Details:")
            for key, value in details.items():
                # Truncate long values
                value_str = str(value)
                if len(value_str) > 100:
                    value_str = value_str[:97] + "..."
                print(f"     {key}: {value_str}")


def display_error_summary(data: dict):
    """Display a summary of error patterns."""
    recent_errors = data.get('recent_errors', [])
    
    if not recent_errors:
        return
    
    print("\n" + "=" * 60)
    print("📋 Error Pattern Analysis")
    print("=" * 60)
    
    # Count by category
    category_counts = {}
    for error in recent_errors:
        category = error.get('category', 'unknown')
        category_counts[category] = category_counts.get(category, 0) + 1
    
    print(f"\nCategory Distribution:")
    for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(recent_errors)) * 100
        print(f"  {category.capitalize():15} {count:4d} ({percentage:5.1f}%)")
    
    # Most common error reasons
    print(f"\nCommon Error Reasons:")
    reasons = {}
    for error in recent_errors:
        details = error.get('details', {})
        reason = details.get('reason', 'unspecified')
        reasons[reason] = reasons.get(reason, 0) + 1
    
    for reason, count in sorted(reasons.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {reason}: {count}")


def main():
    """Main entry point for error metrics script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Query and display error metrics from WhatsApp ChatOps Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "-d", "--detailed",
        action="store_true",
        help="Show detailed error information"
    )
    parser.add_argument(
        "-l", "--limit",
        type=int,
        default=10,
        help="Number of recent errors to display (default: 10)"
    )
    parser.add_argument(
        "-a", "--analyze",
        action="store_true",
        help="Show error pattern analysis"
    )
    parser.add_argument(
        "--url",
        default=AGENT_URL,
        help=f"Agent URL (default: {AGENT_URL})"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON instead of formatted display"
    )
    
    args = parser.parse_args()
    
    # Update agent URL if provided
    global AGENT_URL
    AGENT_URL = args.url
    
    print(f"🔍 Querying agent at: {AGENT_URL}")
    
    # Get basic health metrics
    health_data = get_health_metrics()
    
    if not health_data:
        print("❌ Failed to retrieve health metrics", file=sys.stderr)
        sys.exit(1)
    
    if args.json:
        # Just output JSON
        if args.detailed:
            detailed_data = get_detailed_errors()
            if detailed_data:
                print(json.dumps(detailed_data, indent=2))
        else:
            print(json.dumps(health_data, indent=2))
        return
    
    # Display formatted metrics
    display_health_metrics(health_data)
    
    # Get and display detailed errors if requested
    if args.detailed or args.analyze:
        detailed_data = get_detailed_errors()
        
        if not detailed_data:
            print("\n❌ Failed to retrieve detailed error information", file=sys.stderr)
            sys.exit(1)
        
        if args.detailed:
            display_detailed_errors(detailed_data, limit=args.limit)
        
        if args.analyze:
            display_error_summary(detailed_data)
    
    print("\n" + "=" * 60)
    print(f"✅ Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

