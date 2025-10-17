"""
Continuous health monitoring script for WhatsApp ChatOps Agent.

Monitors the /health endpoint and alerts on failures or degraded status.
Useful for operational monitoring and alerting.
"""

import requests
import time
import sys
import os
from datetime import datetime

# Configuration
AGENT_URL = os.getenv("AGENT_URL", "http://localhost:8080")
CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))  # seconds
ALERT_ON_DEGRADED = os.getenv("ALERT_ON_DEGRADED", "true").lower() == "true"


def check_health():
    """Query health endpoint and return status."""
    try:
        response = requests.get(f"{AGENT_URL}/health", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"status": "unreachable", "error": str(e)}


def print_health_status(health_data):
    """Print health status with color coding."""
    status = health_data.get("status", "unknown")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if status == "ok":
        print(f"[{timestamp}] ✅ Status: {status.upper()}")
    elif status == "degraded":
        print(f"[{timestamp}] ⚠️  Status: {status.upper()}")
    elif status in ["down", "unreachable"]:
        print(f"[{timestamp}] ❌ Status: {status.upper()}")
    else:
        print(f"[{timestamp}] ❓ Status: {status.upper()}")
    
    # Print key metrics
    if "uptime" in health_data:
        print(f"         Uptime: {health_data['uptime']}")
    
    if "dependencies" in health_data:
        deps = health_data["dependencies"]
        for dep_name, dep_info in deps.items():
            dep_status = dep_info.get("status", "unknown")
            symbol = "✅" if dep_status == "ok" else "❌"
            print(f"         {symbol} {dep_name}: {dep_status}")
    
    if "error_metrics" in health_data:
        errors = health_data["error_metrics"]
        if errors.get("recent_errors_last_5min", 0) > 0:
            print(f"         Recent errors (5min): {errors['recent_errors_last_5min']}")


def main():
    """Main monitoring loop."""
    print(f"🔍 Health Monitor Starting")
    print(f"   Target: {AGENT_URL}")
    print(f"   Check Interval: {CHECK_INTERVAL}s")
    print(f"   Alert on Degraded: {ALERT_ON_DEGRADED}")
    print("   Press Ctrl+C to stop\n")
    
    consecutive_failures = 0
    
    try:
        while True:
            health_data = check_health()
            status = health_data.get("status")
            
            print_health_status(health_data)
            
            # Track consecutive failures
            if status in ["down", "unreachable"]:
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    print(f"\n🚨 ALERT: Service down for {consecutive_failures} consecutive checks!\n")
            elif status == "degraded" and ALERT_ON_DEGRADED:
                print(f"\n⚠️  ALERT: Service degraded!\n")
                consecutive_failures = 0
            else:
                consecutive_failures = 0
            
            print("")  # Blank line
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n✅ Health monitoring stopped")
        sys.exit(0)


if __name__ == "__main__":
    main()

