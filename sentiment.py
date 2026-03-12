"""
Enhanced sentiment analyser for food feedback comments.
Supports: bigrams, intensity modifiers, 2-word negation window.
No external ML library required.
"""

# ── keyword lists ──────────────────────────────────────────────
POSITIVE = {
    "excellent","amazing","great","good","tasty","delicious","yummy","loved","love",
    "perfect","wonderful","fantastic","nice","superb","best","awesome","liked",
    "fresh","hot","flavourful","flavorful","soft","crispy","well","enjoyed",
    "satisfying","satisfied","happy","better","improved","outstanding","brilliant",
    "fabulous","juicy","aromatic","hearty","wholesome","tender","smooth","creamy",
    "crunchy","divine","heavenly","recommend","refreshing","balanced","filling",
    "comforting","warm","generous","plenty","enough","upgrade","impressive","rich",
}

NEGATIVE = {
    "bad","terrible","awful","horrible","disgusting","worst","hate","hated",
    "cold","stale","undercooked","overcooked","bland","tasteless","salty",
    "spicy","hard","soggy","raw","burnt","burned","dirty","unhygienic",
    "disappointed","disappointing","poor","unpleasant","unacceptable",
    "gross","nasty","rotten","smelly","worse","dreadful","pathetic",
    "oily","watery","rubbery","chewy","greasy","flavorless","mediocre",
    "inedible","lousy","subpar","lacking","insufficient","sour","rancid",
    "complaint","issue","problem","delay","late","slow","waste",
}

NEGATION = {"not","no","never","wasn't","isn't","doesn't","don't","didn't",
            "none","hardly","barely","neither","nor","without","couldn't","shouldn't"}

INTENSIFIERS = {"very","really","extremely","super","quite","absolutely","totally",
                "incredibly","highly","especially","particularly","so"}

POSITIVE_PHRASES = [
    "well cooked","well made","very good","really good","so good","very tasty",
    "really tasty","perfectly cooked","well seasoned","well prepared",
    "super tasty","finger licking","loved it","really liked","quite good",
    "pretty good","nicely done","highly recommend","top notch","really enjoyed",
    "fresh and hot","fresh and tasty","perfectly spiced","worth it",
]

NEGATIVE_PHRASES = [
    "not good","not fresh","not tasty","too spicy","too salty","too oily",
    "too cold","too hard","not cooked","half cooked","under cooked","over cooked",
    "very bad","really bad","so bad","not worth","waste of","didn't like",
    "don't like","could be better","needs improvement","not satisfying",
    "left hungry","not enough","very disappointing","really disappointing",
    "food poisoning","stomach ache","hygiene issue","not clean",
]


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

    text_lower = text.lower()

    # Phase 1: Check phrases first
    score = 0
    for p in POSITIVE_PHRASES:
        if p in text_lower:
            score += 2
            text_lower = text_lower.replace(p, ' ', 1)
    for p in NEGATIVE_PHRASES:
        if p in text_lower:
            score -= 2
            text_lower = text_lower.replace(p, ' ', 1)

    # Phase 2: Single-word scoring with negation + intensity
    words = text_lower.split()
    cleaned = [w.strip('.,!?;:()[]"\'') for w in words]

    i = 0
    while i < len(cleaned):
        w = cleaned[i]
        negated = (i > 0 and cleaned[i-1] in NEGATION) or \
                  (i > 1 and cleaned[i-2] in NEGATION)
        intense = (i > 0 and cleaned[i-1] in INTENSIFIERS)
        weight = 1.5 if intense else 1.0

        if w in POSITIVE:
            score += (-weight) if negated else weight
        elif w in NEGATIVE:
            score += weight if negated else (-weight)
        i += 1

    # normalise to -1 … +1
    if score > 0.5:
        label, emoji = "Positive", "😊"
        norm = min(round(score / 4, 3), 1.0)
    elif score < -0.5:
        label, emoji = "Negative", "😞"
        norm = max(round(score / 4, 3), -1.0)
    else:
        label, emoji = "Neutral", "😐"
        norm = 0.0

    return {"label": label, "score": norm, "emoji": emoji}


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
            w = w.strip('.,!?;:')
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
