"""
Sentiment Analyzer Agent for AgentOS Runtime
No exception handling - sandbox doesn't include Exception
"""
import time

# Agent execution starts here
start_time = time.time()
agent_id = "sentiment-analyzer-v1"

print(f"[AGENT_LOG] START agent={agent_id}")

# Get text from input_data (provided by runtime)
text = input_data.get("text", "")

# Analyze sentiment using keyword matching
positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
                  'love', 'best', 'happy', 'awesome', 'perfect', 'beautiful']

negative_words = ['bad', 'terrible', 'awful', 'horrible', 'worst', 'hate',
                  'sad', 'angry', 'disappointing', 'poor', 'ugly', 'useless']

text_lower = text.lower()
words = text_lower.split()

pos_count = sum(1 for word in words if any(pw in word for pw in positive_words))
neg_count = sum(1 for word in words if any(nw in word for nw in negative_words))

total_words = len(words) if len(words) > 0 else 1

# Calculate sentiment score
score = (pos_count - neg_count) / total_words
score = max(-1.0, min(1.0, score * 5))  # Scale and clamp

# Determine sentiment label
if score > 0.2:
    label = "positive"
elif score < -0.2:
    label = "negative"
else:
    label = "neutral"

# Calculate metrics
processing_time_ms = (time.time() - start_time) * 1000
word_count = len(words)
char_count = len(text)

# Log completion with metrics
print(f"[AGENT_LOG] COMPLETE agent={agent_id} sentiment={label} score={score:.2f} time_ms={processing_time_ms:.1f} words={word_count}")

# Set result (required by runtime)
result = {
    "agent_id": agent_id,
    "sentiment": {
        "score": round(score, 3),
        "label": label,
        "confidence": round(abs(score), 3)
    },
    "analysis": {
        "positive_words_found": pos_count,
        "negative_words_found": neg_count,
        "word_count": word_count,
        "character_count": char_count
    },
    "metrics": {
        "processing_time_ms": round(processing_time_ms, 2),
        "timestamp": str(time.time())
    },
    "status": "success"
}
