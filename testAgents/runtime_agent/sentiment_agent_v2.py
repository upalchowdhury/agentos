"""
Sentiment Analyzer Agent - Working version for AgentOS Runtime sandbox
"""
import time

# Start timing
start_time = time.time()

# Get input
text = input_data.get("text", "")

# Count sentiment words (avoiding generator expressions that cause scope issues)
positive_count = 0
negative_count = 0

positive_keywords = "good great excellent amazing wonderful fantastic love best happy awesome perfect beautiful"
negative_keywords = "bad terrible awful horrible worst hate sad angry disappointing poor ugly useless"

text_lower = text.lower()

# Count positive words
for word in positive_keywords.split():
    if word in text_lower:
        positive_count = positive_count + 1

# Count negative words
for word in negative_keywords.split():
    if word in text_lower:
        negative_count = negative_count + 1

# Calculate score
word_list = text.split()
word_count = len(word_list)
total = word_count if word_count > 0 else 1

score_raw = float(positive_count - negative_count) / float(total)
score = max(-1.0, min(1.0, score_raw * 5.0))

# Determine label
if score > 0.2:
    label = "positive"
elif score < -0.2:
    label = "negative"
else:
    label = "neutral"

# Calculate processing time
processing_time_ms = (time.time() - start_time) * 1000.0

# Log to stdout (captured by runtime)
print(f"[AGENT_LOG] agent=sentiment-v1 sentiment={label} score={score:.2f} time_ms={processing_time_ms:.1f} words={word_count} pos={positive_count} neg={negative_count}")

# Set result (required)
result = {
    "agent_id": "sentiment-analyzer-v1",
    "sentiment": {
        "score": round(score, 3),
        "label": label
    },
    "metrics": {
        "processing_time_ms": round(processing_time_ms, 2),
        "word_count": word_count,
        "positive_words": positive_count,
        "negative_words": negative_count
    },
    "status": "success"
}
