"""
Debug utilities for payload inspection and debugging.

Provides tools for pretty-printing payloads, inspecting requests,
and other debugging helpers.
"""

import json
from typing import Any, Dict
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


def dump_payload(payload: Dict[str, Any], title: str = "Payload", redact: bool = True) -> str:
    """
    Pretty-print a payload for debugging.
    
    Args:
        payload: Payload dictionary to dump
        title: Title for the dump
        redact: Whether to redact sensitive data
        
    Returns:
        Pretty-printed string representation
    """
    import copy
    
    if redact:
        payload = copy.deepcopy(payload)
        # Redact phone numbers
        if "from" in payload and isinstance(payload["from"], str):
            phone = payload["from"]
            if len(phone) > 4:
                payload["from"] = "***" + phone[-4:]
        if "workflow_id" in payload and isinstance(payload["workflow_id"], str):
            wid = payload["workflow_id"]
            if len(wid) > 4:
                payload["workflow_id"] = "***" + wid[-4:]
    
    try:
        json_str = json.dumps(payload, indent=2, ensure_ascii=False, default=str)
        return f"\n{'=' * 60}\n{title}\n{'=' * 60}\n{json_str}\n{'=' * 60}\n"
    except Exception as e:
        return f"Error dumping payload: {e}"


def dump_request(data: Dict[str, Any]) -> str:
    """
    Dump a webhook request for debugging.
    
    Args:
        data: Request data dictionary
        
    Returns:
        Formatted request dump
    """
    return dump_payload(data, title="WhatsApp Webhook Request")


def dump_response(data: Dict[str, Any]) -> str:
    """
    Dump a response for debugging.
    
    Args:
        data: Response data dictionary
        
    Returns:
        Formatted response dump
    """
    return dump_payload(data, title="Response", redact=False)


def dump_union_payload(workflow_id: str, narrative: str, maxim: str) -> str:
    """
    Dump the payload that will be sent to Union Action API.
    
    Args:
        workflow_id: Workflow identifier
        narrative: Ethics narrative
        maxim: Ethics maxim
        
    Returns:
        Formatted payload dump
    """
    payload = {
        "workflow_id": workflow_id,
        "source_data": {
            "narrative": narrative,
            "pentadic_context": {
                "act": "Narrative submission",
                "scene": {"phenomenal": "WhatsApp chat", "noumenal": "Ethical concern"},
                "agent": {"role": "Participant"}
            },
            "maxim_extraction": maxim
        }
    }
    return dump_payload(payload, title="Union Action API Payload")


def inspect_message(message: str) -> Dict[str, Any]:
    """
    Inspect a message and return diagnostic information.
    
    Args:
        message: Message string to inspect
        
    Returns:
        Dictionary of diagnostic information
    """
    info = {
        "length": len(message),
        "has_delimiter": "|" in message,
        "delimiter_count": message.count("|"),
        "has_newlines": "\n" in message,
        "has_tabs": "\t" in message,
        "starts_with_space": message.startswith(" ") if message else False,
        "ends_with_space": message.endswith(" ") if message else False,
        "is_empty": len(message) == 0,
        "is_whitespace_only": message.isspace() if message else True,
        "preview": message[:100] if len(message) > 100 else message
    }
    
    # If message has delimiter, inspect parts
    if info["has_delimiter"]:
        parts = message.split("|", 1)
        info["narrative_length"] = len(parts[0])
        info["maxim_length"] = len(parts[1]) if len(parts) > 1 else 0
        info["narrative_preview"] = parts[0][:50]
        info["maxim_preview"] = parts[1][:50] if len(parts) > 1 else ""
        
        # Check for empty parts after stripping
        info["narrative_empty_after_strip"] = len(parts[0].strip()) == 0
        info["maxim_empty_after_strip"] = len(parts[1].strip()) == 0 if len(parts) > 1 else True
    
    return info


def format_log_output(log_dict: Dict[str, Any]) -> str:
    """
    Format a log dictionary for human-readable output.
    
    Args:
        log_dict: Log dictionary
        
    Returns:
        Formatted log string
    """
    timestamp = log_dict.get("timestamp", datetime.now().isoformat())
    level = log_dict.get("level", "INFO")
    event = log_dict.get("event", "unknown")
    
    lines = [
        f"[{timestamp}] [{level:8s}] {event}"
    ]
    
    # Add other fields
    for key, value in sorted(log_dict.items()):
        if key not in ["timestamp", "level", "event"]:
            lines.append(f"  {key}: {value}")
    
    return "\n".join(lines)


def create_test_payload(from_number: str, message: str, **kwargs) -> Dict[str, Any]:
    """
    Create a test webhook payload.
    
    Args:
        from_number: Phone number
        message: Message body
        **kwargs: Additional fields
        
    Returns:
        Webhook payload dictionary
    """
    payload = {
        "from": from_number,
        "body": message,
        "timestamp": int(datetime.now().timestamp())
    }
    payload.update(kwargs)
    return payload


def validate_webhook_payload(payload: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate a webhook payload structure.
    
    Args:
        payload: Payload to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(payload, dict):
        return False, "Payload must be a dictionary"
    
    if "from" not in payload:
        return False, "Missing 'from' field"
    
    if "body" not in payload:
        return False, "Missing 'body' field"
    
    if not payload["body"]:
        return False, "Body field is empty"
    
    if "|" not in payload["body"]:
        return False, "Body missing delimiter '|'"
    
    return True, "Payload is valid"


def analyze_error(error: Exception) -> Dict[str, Any]:
    """
    Analyze an exception for debugging.
    
    Args:
        error: Exception to analyze
        
    Returns:
        Dictionary of error analysis
    """
    import traceback
    
    analysis = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "error_module": type(error).__module__,
        "traceback": traceback.format_exc(),
        "timestamp": datetime.now().isoformat()
    }
    
    # Add specific analysis for common error types
    if hasattr(error, "response"):
        # HTTP error
        response = error.response
        analysis["http_status"] = getattr(response, "status_code", None)
        analysis["http_reason"] = getattr(response, "reason", None)
        analysis["http_url"] = getattr(response, "url", None)
        analysis["http_body"] = getattr(response, "text", None)[:500]
    
    if hasattr(error, "args"):
        analysis["error_args"] = str(error.args)
    
    return analysis


def print_debug_header(title: str) -> None:
    """
    Print a debug section header.
    
    Args:
        title: Section title
    """
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def print_debug_section(title: str, content: Any) -> None:
    """
    Print a debug section with title and content.
    
    Args:
        title: Section title
        content: Content to print
    """
    print(f"\n{'-' * 60}")
    print(f"{title}:")
    print(f"{'-' * 60}")
    if isinstance(content, dict):
        print(json.dumps(content, indent=2, ensure_ascii=False, default=str))
    else:
        print(content)
    print()


# Helper functions for interactive debugging

def quick_test_message(message: str) -> None:
    """
    Quick test of message parsing logic.
    
    Args:
        message: Message to test
    """
    print_debug_header("Message Parsing Test")
    
    # Inspect message
    print_debug_section("Message Inspection", inspect_message(message))
    
    # Try parsing
    if "|" in message:
        narrative, maxim = message.split("|", 1)
        result = {
            "narrative_raw": narrative,
            "maxim_raw": maxim,
            "narrative_stripped": narrative.strip(),
            "maxim_stripped": maxim.strip()
        }
        print_debug_section("Parsing Result", result)
    else:
        print("❌ No delimiter found in message")


def quick_test_payload(payload: Dict[str, Any]) -> None:
    """
    Quick test of payload validation.
    
    Args:
        payload: Payload to test
    """
    print_debug_header("Payload Validation Test")
    
    # Dump payload
    print(dump_request(payload))
    
    # Validate
    is_valid, message = validate_webhook_payload(payload)
    if is_valid:
        print("✅ Payload is valid")
    else:
        print(f"❌ Payload validation failed: {message}")
    
    # Inspect message if present
    if "body" in payload:
        print_debug_section("Message Analysis", inspect_message(payload["body"]))

