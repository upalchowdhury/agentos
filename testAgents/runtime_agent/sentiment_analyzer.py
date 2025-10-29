"""
Sentiment Analysis Agent for AgentOS Runtime
This agent analyzes text sentiment and logs detailed usage metrics.
"""
import json
import time
from datetime import datetime
from typing import Dict, Any


def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for the agent.
    Analyzes sentiment of provided text and logs metrics.
    
    Args:
        input_data: Dictionary containing 'text' key with text to analyze
        
    Returns:
        Dictionary with sentiment analysis results and metrics
    """
    start_time = time.time()
    agent_id = "sentiment-analyzer-v1"
    
    # Log invocation start
    log_event("invocation_started", {
        "agent_id": agent_id,
        "timestamp": datetime.utcnow().isoformat(),
        "input_length": len(str(input_data))
    })
    
    try:
        # Extract text from input
        text = input_data.get("text", "")
        if not text:
            raise ValueError("No text provided for analysis")
        
        # Perform sentiment analysis (simple keyword-based)
        sentiment_score, sentiment_label = analyze_sentiment(text)
        
        # Extract entities (simple word frequency)
        entities = extract_entities(text)
        
        # Calculate processing metrics
        processing_time = time.time() - start_time
        word_count = len(text.split())
        char_count = len(text)
        
        # Prepare response
        result = {
            "agent_id": agent_id,
            "sentiment": {
                "score": sentiment_score,
                "label": sentiment_label,
                "confidence": abs(sentiment_score)
            },
            "entities": entities,
            "metrics": {
                "processing_time_ms": round(processing_time * 1000, 2),
                "word_count": word_count,
                "character_count": char_count,
                "timestamp": datetime.utcnow().isoformat()
            },
            "status": "success"
        }
        
        # Log successful completion with metrics
        log_event("invocation_completed", {
            "agent_id": agent_id,
            "sentiment": sentiment_label,
            "processing_time_ms": result["metrics"]["processing_time_ms"],
            "word_count": word_count,
            "status": "success"
        })
        
        return result
        
    except Exception as e:
        # Log error
        error_time = time.time() - start_time
        log_event("invocation_failed", {
            "agent_id": agent_id,
            "error": str(e),
            "processing_time_ms": round(error_time * 1000, 2),
            "status": "error"
        })
        
        return {
            "agent_id": agent_id,
            "status": "error",
            "error": str(e),
            "metrics": {
                "processing_time_ms": round(error_time * 1000, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
        }


def analyze_sentiment(text: str) -> tuple:
    """
    Analyze sentiment using keyword matching.
    Returns (score, label) where score is between -1 and 1.
    """
    positive_words = [
        'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
        'love', 'best', 'happy', 'joy', 'awesome', 'perfect', 'beautiful'
    ]
    
    negative_words = [
        'bad', 'terrible', 'awful', 'horrible', 'worst', 'hate',
        'sad', 'angry', 'disappointing', 'poor', 'ugly', 'useless'
    ]
    
    text_lower = text.lower()
    words = text_lower.split()
    
    positive_count = sum(1 for word in words if any(pw in word for pw in positive_words))
    negative_count = sum(1 for word in words if any(nw in word for nw in negative_words))
    
    total_words = len(words)
    if total_words == 0:
        return 0.0, "neutral"
    
    # Calculate score
    score = (positive_count - negative_count) / total_words
    score = max(-1.0, min(1.0, score * 5))  # Scale and clamp
    
    # Determine label
    if score > 0.2:
        label = "positive"
    elif score < -0.2:
        label = "negative"
    else:
        label = "neutral"
    
    return round(score, 3), label


def extract_entities(text: str) -> Dict[str, int]:
    """
    Extract key entities (simple word frequency analysis).
    Returns top 5 most common words (excluding common stop words).
    """
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'was', 'are', 'were', 'be', 'been',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
        'can', 'could', 'may', 'might', 'this', 'that', 'these', 'those'
    }
    
    words = text.lower().split()
    word_freq = {}
    
    for word in words:
        # Clean word
        word = ''.join(c for c in word if c.isalnum())
        if word and word not in stop_words and len(word) > 2:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Get top 5
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return dict(sorted_words[:5])


def log_event(event_type: str, data: Dict[str, Any]) -> None:
    """
    Log event for monitoring and observability.
    In production, this would send to a logging/metrics system.
    """
    log_entry = {
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data
    }
    # Print to stdout (captured by runtime)
    print(f"[AGENT_LOG] {json.dumps(log_entry)}")


# Test function for local development
if __name__ == "__main__":
    # Test cases
    test_inputs = [
        {"text": "This is a great and amazing product! I love it!"},
        {"text": "This is terrible and awful. I hate it."},
        {"text": "The weather is okay today. Nothing special."},
        {"text": ""}  # Error case
    ]
    
    print("Testing Sentiment Analyzer Agent")
    print("=" * 60)
    
    for i, test_input in enumerate(test_inputs, 1):
        print(f"\nTest {i}: {test_input}")
        result = run(test_input)
        print(f"Result: {json.dumps(result, indent=2)}")
        print("-" * 60)
