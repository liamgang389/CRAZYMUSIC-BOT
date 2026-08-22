"""
Content source for the Emoji/Word picture-guess mini-game.

Each emoji round has one correct emoji plus 7 distractor emojis (8
buttons total once shuffled). Each word round has one correct word —
kept lowercase since guesses are matched case-insensitively.
"""

import random


def scramble(word: str) -> str:
    """Returns a shuffled version of the letters for display, so the
    card shows a puzzle instead of the plain answer. Retries a few
    times to avoid landing back on the original order by chance."""
    letters = list(word)
    scrambled = word
    for _ in range(5):
        random.shuffle(letters)
        scrambled = "".join(letters)
        if scrambled != word:
            break
    return scrambled

EMOJI_ROUNDS = [
    {"answer": "🔥", "distractors": ["💧", "🌙", "⭐", "🍎", "⚽", "🎸", "🚗"]},
    {"answer": "❤️", "distractors": ["💙", "💚", "🖤", "🤍", "💛", "🧡", "💜"]},
    {"answer": "🐶", "distractors": ["🐱", "🐰", "🦊", "🐼", "🐵", "🐯", "🐸"]},
    {"answer": "🍕", "distractors": ["🍔", "🌮", "🍟", "🍩", "🍦", "🍰", "🌭"]},
    {"answer": "⚽", "distractors": ["🏀", "🏏", "🎾", "🏐", "🏓", "🥊", "🏸"]},
    {"answer": "🎧", "distractors": ["🎤", "🎸", "🎹", "🎷", "🥁", "🎺", "📻"]},
    {"answer": "🌧️", "distractors": ["☀️", "❄️", "🌪️", "🌈", "⛈️", "🌤️", "☁️"]},
    {"answer": "🚀", "distractors": ["✈️", "🚁", "🚗", "🚢", "🛸", "🚂", "🛵"]},
    {"answer": "👑", "distractors": ["💎", "🏆", "🎖️", "🥇", "🔱", "🗝️", "⚱️"]},
    {"answer": "🎮", "distractors": ["🕹️", "📱", "💻", "🖥️", "📺", "🎲", "🃏"]},
    {"answer": "🦁", "distractors": ["🐯", "🐘", "🦒", "🦓", "🐻", "🦌", "🐗"]},
    {"answer": "🌺", "distractors": ["🌹", "🌻", "🌷", "🌼", "🌸", "🍀", "🌵"]},
]

WORD_ROUNDS = [
    "pushpa",
    "bahubali",
    "rrr",
    "kgf",
    "dangal",
    "sholay",
    "jawan",
    "pathaan",
    "animal",
    "gadar",
]


def pick_emoji_round(exclude_answer: str = None) -> dict:
    pool = [r for r in EMOJI_ROUNDS if r["answer"] != exclude_answer] or EMOJI_ROUNDS
    chosen = random.choice(pool)
    options = list(chosen["distractors"]) + [chosen["answer"]]
    random.shuffle(options)
    return {"answer": chosen["answer"], "options": options}


def pick_word_round(exclude_answer: str = None) -> str:
    pool = [w for w in WORD_ROUNDS if w != exclude_answer] or WORD_ROUNDS
    return random.choice(pool)
