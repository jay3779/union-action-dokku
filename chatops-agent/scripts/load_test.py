"""
Load testing script for WhatsApp ChatOps Agent.

Simulates concurrent webhook requests to test performance under load.
"""

import requests
import time
import threading
import sys
import os
from datetime import datetime
from collections import defaultdict

# Configuration
AGENT_URL = os.getenv("AGENT_URL", "http://localhost:8080")
NUM_REQUESTS = int(os.getenv("LOAD_TEST_REQUESTS", "100"))
CONCURRENCY = int(os.getenv("LOAD_TEST_CONCURRENCY", "10"))


class LoadTestResults:
    """Collect and aggregate load test results."""
    
    def __init__(self):
        self.lock = threading.Lock()
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.response_times = []
        self.status_codes = defaultdict(int)
        self.errors = []
    
    def record_request(self, duration_ms, status_code, error=None):
        """Record a completed request."""
        with self.lock:
            self.total_requests += 1
            self.response_times.append(duration_ms)
            self.status_codes[status_code] += 1
            
            if status_code == 200:
                self.successful_requests += 1
            else:
                self.failed_requests += 1
                if error:
                    self.errors.append(error)
    
    def get_summary(self):
        """Get summary statistics."""
        if not self.response_times:
            return {}
        
        sorted_times = sorted(self.response_times)
        
        return {
            "total_requests": self.total_requests,
            "successful": self.successful_requests,
            "failed": self.failed_requests,
            "min_ms": round(min(sorted_times), 2),
            "max_ms": round(max(sorted_times), 2),
            "avg_ms": round(sum(sorted_times) / len(sorted_times), 2),
            "p50_ms": round(sorted_times[len(sorted_times) // 2], 2),
            "p95_ms": round(sorted_times[int(len(sorted_times) * 0.95)], 2),
            "p99_ms": round(sorted_times[int(len(sorted_times) * 0.99)], 2),
            "status_codes": dict(self.status_codes),
            "error_count": len(self.errors)
        }


def send_webhook_request(url, payload, results):
    """Send a single webhook request and record results."""
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{url}/webhook",
            json=payload,
            timeout=30
        )
        duration_ms = (time.time() - start_time) * 1000
        results.record_request(duration_ms, response.status_code)
        
    except requests.Timeout:
        duration_ms = (time.time() - start_time) * 1000
        results.record_request(duration_ms, 504, "Timeout")
        
    except requests.RequestException as e:
        duration_ms = (time.time() - start_time) * 1000
        results.record_request(duration_ms, 0, str(e))


def worker(url, payloads, results):
    """Worker thread that sends multiple requests."""
    for payload in payloads:
        send_webhook_request(url, payload, results)


def generate_test_payloads(count):
    """Generate test webhook payloads."""
    payloads = []
    for i in range(count):
        payloads.append({
            "from": f"load_test_user_{i}",
            "body": f"Load test narrative {i}|Load test maxim {i}",
            "timestamp": int(time.time())
        })
    return payloads


def print_progress(current, total, start_time):
    """Print progress bar."""
    percent = (current / total) * 100
    elapsed = time.time() - start_time
    rate = current / elapsed if elapsed > 0 else 0
    
    bar_length = 40
    filled = int(bar_length * current / total)
    bar = "=" * filled + "-" * (bar_length - filled)
    
    sys.stdout.write(f"\r[{bar}] {percent:.1f}% ({current}/{total}) | {rate:.1f} req/s")
    sys.stdout.flush()


def run_load_test(url, num_requests, concurrency):
    """Run the load test."""
    print(f"🚀 Load Test Starting")
    print(f"   Target: {url}")
    print(f"   Total Requests: {num_requests}")
    print(f"   Concurrency: {concurrency}\n")
    
    # Generate payloads
    payloads = generate_test_payloads(num_requests)
    results = LoadTestResults()
    
    # Distribute payloads across workers
    payloads_per_worker = num_requests // concurrency
    worker_payloads = []
    for i in range(concurrency):
        start_idx = i * payloads_per_worker
        end_idx = start_idx + payloads_per_worker if i < concurrency - 1 else num_requests
        worker_payloads.append(payloads[start_idx:end_idx])
    
    # Start workers
    start_time = time.time()
    threads = []
    for worker_payloads_chunk in worker_payloads:
        t = threading.Thread(target=worker, args=(url, worker_payloads_chunk, results))
        t.start()
        threads.append(t)
    
    # Wait for completion with progress updates
    while any(t.is_alive() for t in threads):
        print_progress(results.total_requests, num_requests, start_time)
        time.sleep(0.1)
    
    # Final progress update
    print_progress(results.total_requests, num_requests, start_time)
    print("\n")  # New line after progress bar
    
    # Wait for all threads
    for t in threads:
        t.join()
    
    total_duration = time.time() - start_time
    
    # Print results
    summary = results.get_summary()
    
    print("=" * 60)
    print("📊 Load Test Results")
    print("=" * 60)
    print(f"Total Duration:     {total_duration:.2f}s")
    print(f"Requests/sec:       {num_requests / total_duration:.2f}")
    print(f"Total Requests:     {summary['total_requests']}")
    print(f"Successful:         {summary['successful']} ({summary['successful']/num_requests*100:.1f}%)")
    print(f"Failed:             {summary['failed']} ({summary['failed']/num_requests*100:.1f}%)")
    print("")
    print("Response Times (ms):")
    print(f"  Min:              {summary['min_ms']}")
    print(f"  Average:          {summary['avg_ms']}")
    print(f"  P50 (median):     {summary['p50_ms']}")
    print(f"  P95:              {summary['p95_ms']}")
    print(f"  P99:              {summary['p99_ms']}")
    print(f"  Max:              {summary['max_ms']}")
    print("")
    print("Status Codes:")
    for code, count in sorted(summary['status_codes'].items()):
        print(f"  {code}:              {count}")
    
    if summary['error_count'] > 0:
        print(f"\n⚠️  {summary['error_count']} errors occurred")
    
    print("=" * 60)


def main():
    """Main entry point."""
    try:
        run_load_test(AGENT_URL, NUM_REQUESTS, CONCURRENCY)
    except KeyboardInterrupt:
        print("\n\n❌ Load test interrupted")
        sys.exit(1)


if __name__ == "__main__":
    main()

