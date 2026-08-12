"""
highscores.py
Wczytywanie, zapisywanie i sprawdzanie najlepszych wyników - osobny plik
JSON dla każdego poziomu trudności.
"""
import os
import json
import config as cfg

os.makedirs(cfg.SCORES_DIR, exist_ok=True)


def _score_file(level):
    return os.path.join(cfg.SCORES_DIR, f"level{level}_scores.json")


def load_highscores(level):
    try:
        with open(_score_file(level), "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_highscores(level, scores):
    with open(_score_file(level), "w", encoding="utf-8") as f:
        json.dump(scores, f, ensure_ascii=False)


def add_score(level, name, score):
    """Dopisuje wynik, sortuje malejąco i przycina do MAX_HIGHSCORES."""
    scores = load_highscores(level)
    scores.append({"name": name, "score": score})
    scores.sort(key=lambda x: x["score"], reverse=True)
    scores = scores[:cfg.MAX_HIGHSCORES]
    save_highscores(level, scores)
    return scores


def qualifies(level, score):
    """Czy dany wynik załapałby się do TOP MAX_HIGHSCORES na danym poziomie."""
    scores = load_highscores(level)
    if len(scores) < cfg.MAX_HIGHSCORES:
        return True
    return score > scores[-1]["score"]
