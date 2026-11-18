import re
import math
# Local mathematical AI detector analyzing sentence burstiness, vocabulary, and punctuation
def check_AI_score(text: str) -> int:
    if not text or len(text.strip()) < 30:
        return 15
    # Split text into sentences and calculate sentence length variance (burstiness)
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip().split()) >= 2]
    if len(sentences) < 2:
        return 35
    lengths = [len(s.split()) for s in sentences]
    mean_len = sum(lengths) / len(lengths)
    variance = sum((x - mean_len) ** 2 for x in lengths) / len(lengths)
    std_dev = math.sqrt(variance)
    if std_dev >= 8.0: burstiness_score = 15
    elif std_dev >= 5.0: burstiness_score = 40
    else: burstiness_score = 80
    # Calculate lexical diversity (unique words ratio)
    words = re.findall(r'\b\w+\b', text.lower())
    unique_ratio = len(set(words)) / max(1, len(words))
    diversity_score = int((1.0 - unique_ratio) * 140)
    # Penalize frequent AI-favored punctuation marks (colons and em-dashes)
    punct_count = text.count(":") + text.count("—")
    cliche_bonus = min(20, int((punct_count / max(1, len(words))) * 300))
    # Compute final weighted AI probability score (clamped between 5% and 98%)
    final_score = int(burstiness_score * 0.6 + diversity_score * 0.4 + cliche_bonus)
    return max(5, min(98, final_score))