#!/usr/bin/env python3
"""
Manual webhook testing script.

This script simulates webhook calls to the WhatsApp ChatOps Agent for manual testing.
Useful for debugging without needing the full WAHA setup.

Usage:
    python scripts/test_webhook.py
    python scripts/test_webhook.py --message "Custom narrative|Custom maxim"
    python scripts/test_webhook.py --phone "1234567890" --file test_messages.txt
"""

import argparse
import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional


def send_webhook(
    url: str,
    from_number: str,
    message: str,
    correlation_id: Optional[str] = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Send a webhook request to the agent service.
    
    Args:
        url: Webhook URL
        from_number: Phone number
        message: Message body
        correlation_id: Optional correlation ID
        verbose: Print detailed output
        
    Returns:
        Response data dictionary
    """
    # Build payload
    payload = {
        "from": from_number,
        "body": message,
        "timestamp": int(datetime.now().timestamp())
    }
    
    # Build headers
    headers = {"Content-Type": "application/json"}
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id
    
    if verbose:
        print(f"\n{'='*60}")
        print("Sending webhook request:")
        print(f"{'='*60}")
        print(f"URL: {url}")
        print(f"Headers: {json.dumps(headers, indent=2)}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        print(f"{'='*60}\n")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        result = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
            "success": 200 <= response.status_code < 300
        }
        
        if verbose:
            print(f"\n{'='*60}")
            print("Response received:")
            print(f"{'='*60}")
            print(f"Status: {result['status_code']}")
            print(f"Correlation ID: {response.headers.get('X-Correlation-ID', 'N/A')}")
            print(f"Body: {json.dumps(result['body'], indent=2)}")
            print(f"{'='*60}\n")
        
        return result
        
    except requests.RequestException as e:
        print(f"❌ Request failed: {e}")
        return {
            "status_code": 0,
            "error": str(e),
            "success": False
        }


def test_valid_message(url: str, phone: str, verbose: bool = False) -> bool:
    """Test with a valid message."""
    print("\n[TEST] Valid message with delimiter")
    result = send_webhook(
        url,
        phone,
        "I observed a colleague taking credit for someone else's work|Always give credit where credit is due",
        verbose=verbose
    )
    success = result["success"]
    print(f"✅ PASS" if success else f"❌ FAIL - Status: {result.get('status_code')}")
    return success


def test_missing_delimiter(url: str, phone: str, verbose: bool = False) -> bool:
    """Test with missing delimiter."""
    print("\n[TEST] Missing delimiter (should fail)")
    result = send_webhook(
        url,
        phone,
        "This message is missing the delimiter",
        verbose=verbose
    )
    # Should return 400
    success = result["status_code"] == 400
    print(f"✅ PASS (correctly rejected)" if success else f"❌ FAIL - Expected 400, got {result.get('status_code')}")
    return success


def test_empty_narrative(url: str, phone: str, verbose: bool = False) -> bool:
    """Test with empty narrative."""
    print("\n[TEST] Empty narrative")
    result = send_webhook(
        url,
        phone,
        "|Some maxim here",
        verbose=verbose
    )
    success = result["success"]
    print(f"Result: Status {result.get('status_code')}")
    return success


def test_empty_maxim(url: str, phone: str, verbose: bool = False) -> bool:
    """Test with empty maxim."""
    print("\n[TEST] Empty maxim")
    result = send_webhook(
        url,
        phone,
        "Some narrative here|",
        verbose=verbose
    )
    success = result["success"]
    print(f"Result: Status {result.get('status_code')}")
    return success


def test_unicode_content(url: str, phone: str, verbose: bool = False) -> bool:
    """Test with unicode characters."""
    print("\n[TEST] Unicode content")
    result = send_webhook(
        url,
        phone,
        "Problème éthique 中文 😟|Respecter les autres 尊重 ✅",
        verbose=verbose
    )
    success = result["success"]
    print(f"✅ PASS" if success else f"❌ FAIL - Status: {result.get('status_code')}")
    return success


def test_multiple_delimiters(url: str, phone: str, verbose: bool = False) -> bool:
    """Test with multiple pipe delimiters."""
    print("\n[TEST] Multiple delimiters")
    result = send_webhook(
        url,
        phone,
        "First part|Second part|Third part",
        verbose=verbose
    )
    success = result["success"]
    print(f"✅ PASS" if success else f"❌ FAIL - Status: {result.get('status_code')}")
    return success


def test_very_long_message(url: str, phone: str, verbose: bool = False) -> bool:
    """Test with very long message."""
    print("\n[TEST] Very long message")
    narrative = "A" * 5000
    maxim = "B" * 1000
    result = send_webhook(
        url,
        phone,
        f"{narrative}|{maxim}",
        verbose=verbose
    )
    success = result["success"]
    print(f"✅ PASS" if success else f"❌ FAIL - Status: {result.get('status_code')}")
    return success


def run_all_tests(url: str, phone: str, verbose: bool = False) -> Dict[str, int]:
    """
    Run all test cases.
    
    Returns:
        Dictionary with pass/fail counts
    """
    print(f"\n{'='*60}")
    print("Running WhatsApp ChatOps Agent Webhook Tests")
    print(f"{'='*60}")
    print(f"URL: {url}")
    print(f"Test Phone: {phone}")
    
    tests = [
        ("Valid message", test_valid_message),
        ("Missing delimiter", test_missing_delimiter),
        ("Empty narrative", test_empty_narrative),
        ("Empty maxim", test_empty_maxim),
        ("Unicode content", test_unicode_content),
        ("Multiple delimiters", test_multiple_delimiters),
        ("Very long message", test_very_long_message),
    ]
    
    results = {"passed": 0, "failed": 0}
    
    for test_name, test_func in tests:
        try:
            passed = test_func(url, phone, verbose)
            if passed:
                results["passed"] += 1
            else:
                results["failed"] += 1
        except Exception as e:
            print(f"❌ Test '{test_name}' raised exception: {e}")
            results["failed"] += 1
    
    print(f"\n{'='*60}")
    print("Test Summary")
    print(f"{'='*60}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Total:  {results['passed'] + results['failed']}")
    print(f"{'='*60}\n")
    
    return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test WhatsApp ChatOps Agent webhook")
    parser.add_argument(
        "--url",
        default="http://localhost:8080/webhook",
        help="Webhook URL (default: http://localhost:8080/webhook)"
    )
    parser.add_argument(
        "--phone",
        default="1234567890",
        help="Test phone number (default: 1234567890)"
    )
    parser.add_argument(
        "--message",
        help="Custom message to send"
    )
    parser.add_argument(
        "--correlation-id",
        help="Custom correlation ID for request"
    )
    parser.add_argument(
        "--file",
        help="File containing messages to test (one per line)"
    )
    parser.add_argument(
        "--all-tests",
        action="store_true",
        help="Run all test cases"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    if args.all_tests:
        results = run_all_tests(args.url, args.phone, args.verbose)
        sys.exit(0 if results["failed"] == 0 else 1)
    
    elif args.file:
        print(f"Reading messages from: {args.file}")
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                messages = [line.strip() for line in f if line.strip()]
            
            print(f"Found {len(messages)} messages to test\n")
            
            success_count = 0
            for i, message in enumerate(messages, 1):
                print(f"\n[{i}/{len(messages)}] Testing message...")
                result = send_webhook(
                    args.url,
                    args.phone,
                    message,
                    verbose=args.verbose
                )
                if result["success"]:
                    success_count += 1
                    print(f"✅ Success")
                else:
                    print(f"❌ Failed - Status: {result.get('status_code')}")
            
            print(f"\n{'='*60}")
            print(f"Results: {success_count}/{len(messages)} successful")
            print(f"{'='*60}\n")
            
        except FileNotFoundError:
            print(f"❌ File not found: {args.file}")
            sys.exit(1)
    
    elif args.message:
        result = send_webhook(
            args.url,
            args.phone,
            args.message,
            args.correlation_id,
            verbose=True
        )
        if result["success"]:
            print("\n✅ Request successful")
            sys.exit(0)
        else:
            print(f"\n❌ Request failed - Status: {result.get('status_code')}")
            sys.exit(1)
    
    else:
        # Default: send one test message
        print("Sending default test message...")
        result = send_webhook(
            args.url,
            args.phone,
            "Test narrative from script|Test maxim from script",
            verbose=True
        )
        if result["success"]:
            print("\n✅ Request successful")
            sys.exit(0)
        else:
            print(f"\n❌ Request failed - Status: {result.get('status_code')}")
            sys.exit(1)


if __name__ == "__main__":
    main()

