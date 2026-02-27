"""
Lightweight sentiment analyser for food feedback comments.
Uses keyword matching — no external ML library required at runtime.
Install textblob on your server for better accuracy:
    pip install textblob
"""

# ── keyword lists ──────────────────────────────────────────────
POSITIVE = {
    "excellent","amazing","great","good","tasty","delicious","yummy","loved",
    "perfect","wonderful","fantastic","nice","superb","best","awesome",
    "fresh","hot","flavourful","flavorful","soft","crispy","well cooked",
    "well-cooked","enjoyed","satisfying","satisfied","happy","love","liked",
    "better","improved","outstanding","brilliant","fabulous"
}

NEGATIVE = {
    "bad","terrible","awful","horrible","disgusting","worst","hate","hated",
    "cold","stale","undercooked","overcooked","bland","tasteless","salty",
    "spicy","hard","soggy","raw","burnt","burned","dirty","unhygienic",
    "disappointed","disappointing","poor","unpleasant","unacceptable",
    "gross","nasty","rotten","smelly","worse","horrible","dreadful","pathetic"
}

NEGATION = {"not","no","never","wasn't","isn't","doesn't","don't","didn't","none","hardly","barely"}

def analyse(text: str) -> dict:
    """
    Returns:
        {
          "label":  "Positive" | "Neutral" | "Negative",
          "score":  float  (-1.0 … +1.0),
          "emoji":  str
        }
    """
    if not text or not text.strip():
        return {"label": "Neutral", "score": 0.0, "emoji": "😐"}

    words = text.lower().split()
    score = 0
    i = 0
    while i < len(words):
        w = words[i]
        negate = (i > 0 and words[i - 1] in NEGATION)
        if w in POSITIVE:
            score += -1 if negate else 1
        elif w in NEGATIVE:
            score += 1 if negate else -1
        i += 1

    # normalise to -1 … +1
    total = len(words) or 1
    norm = max(-1.0, min(1.0, score / (total ** 0.5)))

    if norm > 0.1:
        label, emoji = "Positive", "😊"
    elif norm < -0.1:
        label, emoji = "Negative", "😞"
    else:
        label, emoji = "Neutral", "😐"

    return {"label": label, "score": round(norm, 3), "emoji": emoji}


def analyse_batch(comments: list) -> dict:
    """
    Summarise a list of comment strings.
    Returns counts, percentages, top positive/negative words.
    """
    counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
    word_pos = {}
    word_neg = {}

    for c in comments:
        if not c:
            counts["Neutral"] += 1
            continue
        r = analyse(c)
        counts[r["label"]] += 1
        words = c.lower().split()
        for w in words:
            if w in POSITIVE:
                word_pos[w] = word_pos.get(w, 0) + 1
            elif w in NEGATIVE:
                word_neg[w] = word_neg.get(w, 0) + 1

    total = sum(counts.values()) or 1
    pct = {k: round(v / total * 100, 1) for k, v in counts.items()}

    top_pos = sorted(word_pos.items(), key=lambda x: -x[1])[:5]
    top_neg = sorted(word_neg.items(), key=lambda x: -x[1])[:5]

    return {
        "counts": counts,
        "percentages": pct,
        "top_positive_words": top_pos,
        "top_negative_words": top_neg,
        "total": total
    }
