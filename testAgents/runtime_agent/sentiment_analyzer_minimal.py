"""
Minimal Sentiment Analysis Agent for AgentOS Runtime
Works within the strictest security sandbox.
"""
import time


def run(input_data):
    """Main entry point - analyzes sentiment and logs metrics."""
    start_time = time.time()
    agent_id = "sentiment-analyzer-v1"
    
    print(f"[AGENT_LOG] START agent={agent_id}")
    
    try:
        text = input_data.get("text", "")
        if not text:
            raise ValueError("No text provided")
        
        # Analyze sentiment
        score, label = analyze_sentiment(text)
        
        # Calculate metrics
        processing_time_ms = (time.time() - start_time) * 1000
        word_count = len(text.split())
        
        # Log completion
        print(f"[AGENT_LOG] COMPLETE agent={agent_id} sentiment={label} score={score} time_ms={processing_time_ms:.1f} words={word_count}")
        
        return {
            "agent_id": agent_id,
            "sentiment": {
                "score": score,
                "label": label
            },
            "metrics": {
                "processing_time_ms": round(processing_time_ms, 2),
                "word_count": word_count,
                "character_count": len(text)
            },
            "status": "success"
        }
        
    except Exception as e:
        error_time_ms = (time.time() - start_time) * 1000
        print(f"[AGENT_LOG] ERROR agent={agent_id} error={str(e)} time_ms={error_time_ms:.1f}")
        
        return {
            "agent_id": agent_id,
            "status": "error",
            "error": str(e),
            "processing_time_ms": round(error_time_ms, 2)
        }


def analyze_sentiment(text):
    """Simple keyword-based sentiment analysis."""
    positive = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
                'love', 'best', 'happy', 'awesome', 'perfect', 'beautiful']
    
    negative = ['bad', 'terrible', 'awful', 'horrible', 'worst', 'hate',
                'sad', 'angry', 'disappointing', 'poor', 'ugly', 'useless']
    
    text_lower = text.lower()
    words = text_lower.split()
    
    pos_count = sum(1 for word in words if any(pw in word for pw in positive))
    neg_count = sum(1 for word in words if any(nw in word for nw in negative))
    
    total = len(words) if len(words) > 0 else 1
    score = (pos_count - neg_count) / total
    score = max(-1.0, min(1.0, score * 5))
    
    if score > 0.2:
        label = "positive"
    elif score < -0.2:
        label = "negative"
    else:
        label = "neutral"
    
    return round(score, 3), label
