"""
Simplified Sentiment Analysis Agent for AgentOS Runtime
This version works within the runtime's security sandbox.
"""
import time
from datetime import datetime
from typing import Dict, Any


def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for the agent.
    Analyzes sentiment of provided text and logs metrics.
    """
    start_time = time.time()
    agent_id = "sentiment-analyzer-v1"
    
    # Log invocation start
    print(f"[AGENT_LOG] invocation_started: agent={agent_id} time={datetime.now().isoformat()}")
    
    try:
        # Extract text from input
        text = input_data.get("text", "")
        if not text:
            raise ValueError("No text provided for analysis")
        
        # Perform sentiment analysis
        sentiment_score, sentiment_label = analyze_sentiment(text)
        
        # Extract entities
        entities = extract_entities(text)
        
        # Calculate metrics
        processing_time = (time.time() - start_time) * 1000  # ms
        word_count = len(text.split())
        char_count = len(text)
        
        # Log completion
        print(f"[AGENT_LOG] invocation_completed: agent={agent_id} sentiment={sentiment_label} time_ms={processing_time:.2f} words={word_count}")
        
        # Return results
        return {
            "agent_id": agent_id,
            "sentiment": {
                "score": sentiment_score,
                "label": sentiment_label,
                "confidence": abs(sentiment_score)
            },
            "entities": entities,
            "metrics": {
                "processing_time_ms": round(processing_time, 2),
                "word_count": word_count,
                "character_count": char_count,
                "timestamp": datetime.now().isoformat()
            },
            "status": "success"
        }
        
    except Exception as e:
        error_time = (time.time() - start_time) * 1000
        print(f"[AGENT_LOG] invocation_failed: agent={agent_id} error={str(e)} time_ms={error_time:.2f}")
        
        return {
            "agent_id": agent_id,
            "status": "error",
            "error": str(e),
            "metrics": {
                "processing_time_ms": round(error_time, 2),
                "timestamp": datetime.now().isoformat()
            }
        }


def analyze_sentiment(text: str) -> tuple:
    """Analyze sentiment using keyword matching."""
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
    
    total_words = len(words) if len(words) > 0 else 1
    
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
    """Extract key entities (word frequency)."""
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'was', 'are', 'were', 'be', 'been',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
        'can', 'could', 'may', 'might', 'this', 'that', 'these', 'those'
    }
    
    words = text.lower().split()
    word_freq = {}
    
    for word in words:
        word = ''.join(c for c in word if c.isalnum())
        if word and word not in stop_words and len(word) > 2:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Get top 5
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return dict(sorted_words[:5])
