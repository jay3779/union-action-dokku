#!/usr/bin/env python3
"""
Log inspection and filtering script.

This script helps parse and filter structlog output for debugging.

Usage:
    # View all logs
    docker-compose logs agent | python scripts/inspect_logs.py
    
    # Filter by event type
    docker-compose logs agent | python scripts/inspect_logs.py --event webhook_received
    
    # Filter by correlation ID
    docker-compose logs agent | python scripts/inspect_logs.py --correlation-id abc-123
    
    # Show only errors
    docker-compose logs agent | python scripts/inspect_logs.py --level error
    
    # Filter by workflow ID
    docker-compose logs agent | python scripts/inspect_logs.py --workflow-id 1234567890
"""

import argparse
import json
import sys
import re
from typing import Dict, Any, List, Optional
from datetime import datetime


def parse_log_line(line: str) -> Optional[Dict[str, Any]]:
    """
    Parse a log line (JSON or key-value format).
    
    Args:
        line: Log line to parse
        
    Returns:
        Parsed log dictionary or None if not parseable
    """
    # Try JSON parsing first
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        pass
    
    # Try key-value parsing
    try:
        # Look for timestamp, level, event pattern
        match = re.search(r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})', line)
        if match:
            log_dict = {"raw": line, "timestamp": match.group(1)}
            
            # Extract level
            level_match = re.search(r'\[(INFO|DEBUG|WARNING|ERROR|CRITICAL)\]', line)
            if level_match:
                log_dict["level"] = level_match.group(1)
            
            # Extract event
            event_match = re.search(r'event=(\w+)', line)
            if event_match:
                log_dict["event"] = event_match.group(1)
            
            # Extract correlation_id
            corr_match = re.search(r'correlation_id=([a-zA-Z0-9\-]+)', line)
            if corr_match:
                log_dict["correlation_id"] = corr_match.group(1)
            
            # Extract workflow_id
            wf_match = re.search(r'workflow_id=([a-zA-Z0-9\-_*]+)', line)
            if wf_match:
                log_dict["workflow_id"] = wf_match.group(1)
            
            return log_dict
    except Exception:
        pass
    
    return None


def format_log_entry(log_dict: Dict[str, Any], verbose: bool = False) -> str:
    """
    Format a log entry for display.
    
    Args:
        log_dict: Parsed log dictionary
        verbose: Show all fields
        
    Returns:
        Formatted string
    """
    timestamp = log_dict.get("timestamp", "")
    level = log_dict.get("level", "INFO")
    event = log_dict.get("event", "unknown")
    
    # Color codes
    colors = {
        "DEBUG": "\033[36m",    # Cyan
        "INFO": "\033[32m",     # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",    # Red
        "CRITICAL": "\033[35m", # Magenta
        "RESET": "\033[0m"
    }
    
    color = colors.get(level, "")
    reset = colors["RESET"]
    
    # Basic format
    output = f"{color}[{timestamp}] [{level:8s}]{reset} {event}"
    
    # Add correlation ID if present
    if "correlation_id" in log_dict:
        output += f" [corr: {log_dict['correlation_id'][:8]}...]"
    
    # Add workflow ID if present
    if "workflow_id" in log_dict:
        output += f" [wf: {log_dict['workflow_id']}]"
    
    # Add duration if present
    if "duration_ms" in log_dict:
        output += f" [{log_dict['duration_ms']}ms]"
    
    # Add status code if present
    if "status_code" in log_dict:
        output += f" [HTTP {log_dict['status_code']}]"
    
    # Show all fields in verbose mode
    if verbose:
        output += "\n"
        for key, value in sorted(log_dict.items()):
            if key not in ["timestamp", "level", "event", "correlation_id", "workflow_id", "raw"]:
                output += f"  {key}: {value}\n"
    
    return output


def filter_logs(
    logs: List[Dict[str, Any]],
    event: Optional[str] = None,
    level: Optional[str] = None,
    correlation_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Filter logs based on criteria.
    
    Args:
        logs: List of parsed log dictionaries
        event: Filter by event name
        level: Filter by log level
        correlation_id: Filter by correlation ID
        workflow_id: Filter by workflow ID
        since: Filter logs after this time
        until: Filter logs before this time
        
    Returns:
        Filtered list of logs
    """
    filtered = logs
    
    if event:
        filtered = [log for log in filtered if log.get("event") == event]
    
    if level:
        filtered = [log for log in filtered if log.get("level", "").upper() == level.upper()]
    
    if correlation_id:
        filtered = [log for log in filtered if correlation_id in log.get("correlation_id", "")]
    
    if workflow_id:
        filtered = [log for log in filtered if workflow_id in log.get("workflow_id", "")]
    
    # Time filtering (simplified - just string comparison)
    if since:
        filtered = [log for log in filtered if log.get("timestamp", "") >= since]
    
    if until:
        filtered = [log for log in filtered if log.get("timestamp", "") <= until]
    
    return filtered


def analyze_logs(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze logs and generate statistics.
    
    Args:
        logs: List of parsed log dictionaries
        
    Returns:
        Analysis dictionary
    """
    analysis = {
        "total_logs": len(logs),
        "by_level": {},
        "by_event": {},
        "unique_correlation_ids": set(),
        "unique_workflow_ids": set(),
        "errors": [],
        "slow_operations": []
    }
    
    for log in logs:
        # Count by level
        level = log.get("level", "UNKNOWN")
        analysis["by_level"][level] = analysis["by_level"].get(level, 0) + 1
        
        # Count by event
        event = log.get("event", "unknown")
        analysis["by_event"][event] = analysis["by_event"].get(event, 0) + 1
        
        # Track correlation IDs
        if "correlation_id" in log:
            analysis["unique_correlation_ids"].add(log["correlation_id"])
        
        # Track workflow IDs
        if "workflow_id" in log:
            analysis["unique_workflow_ids"].add(log["workflow_id"])
        
        # Collect errors
        if level in ["ERROR", "CRITICAL"]:
            analysis["errors"].append(log)
        
        # Collect slow operations
        if "duration_ms" in log and float(log.get("duration_ms", 0)) > 2000:
            analysis["slow_operations"].append(log)
    
    # Convert sets to counts
    analysis["unique_correlation_ids"] = len(analysis["unique_correlation_ids"])
    analysis["unique_workflow_ids"] = len(analysis["unique_workflow_ids"])
    
    return analysis


def print_analysis(analysis: Dict[str, Any]) -> None:
    """Print log analysis."""
    print(f"\n{'='*60}")
    print("Log Analysis")
    print(f"{'='*60}\n")
    
    print(f"Total logs: {analysis['total_logs']}")
    print(f"Unique requests: {analysis['unique_correlation_ids']}")
    print(f"Unique workflows: {analysis['unique_workflow_ids']}")
    
    print(f"\nBy Level:")
    for level, count in sorted(analysis["by_level"].items()):
        print(f"  {level:10s}: {count}")
    
    print(f"\nTop Events:")
    sorted_events = sorted(analysis["by_event"].items(), key=lambda x: x[1], reverse=True)
    for event, count in sorted_events[:10]:
        print(f"  {event:30s}: {count}")
    
    if analysis["errors"]:
        print(f"\n⚠️  Found {len(analysis['errors'])} errors")
    
    if analysis["slow_operations"]:
        print(f"\n⏱️  Found {len(analysis['slow_operations'])} slow operations (>2000ms)")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Inspect and filter structlog output")
    parser.add_argument(
        "--event",
        help="Filter by event name"
    )
    parser.add_argument(
        "--level",
        help="Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    parser.add_argument(
        "--correlation-id",
        help="Filter by correlation ID (partial match)"
    )
    parser.add_argument(
        "--workflow-id",
        help="Filter by workflow ID (partial match)"
    )
    parser.add_argument(
        "--since",
        help="Show logs since this time (ISO format)"
    )
    parser.add_argument(
        "--until",
        help="Show logs until this time (ISO format)"
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Show log analysis summary"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show all log fields"
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )
    
    args = parser.parse_args()
    
    # Read logs from stdin
    print("Reading logs from stdin...", file=sys.stderr)
    logs = []
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        parsed = parse_log_line(line)
        if parsed:
            logs.append(parsed)
    
    print(f"Parsed {len(logs)} log entries", file=sys.stderr)
    
    # Filter logs
    filtered = filter_logs(
        logs,
        event=args.event,
        level=args.level,
        correlation_id=args.correlation_id,
        workflow_id=args.workflow_id,
        since=args.since,
        until=args.until
    )
    
    print(f"Filtered to {len(filtered)} entries\n", file=sys.stderr)
    
    # Show analysis if requested
    if args.analyze:
        analysis = analyze_logs(filtered)
        print_analysis(analysis)
        return
    
    # Display filtered logs
    for log in filtered:
        print(format_log_entry(log, verbose=args.verbose))
    
    # Show summary
    if filtered:
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"Displayed {len(filtered)} log entries", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)


if __name__ == "__main__":
    main()

