"""
Content source for the Emoji/Word picture-guess mini-game.

No live AI-generation is wired up here (this project has no
chat-completion API integrated, and posting unreviewed AI output
straight into groups automatically is a real quality/safety risk).
Instead, both pools are large enough that rounds effectively never
feel repetitive:

- EMOJI_POOL: a flat pool of 172 emoji. Each round picks 1 as the
  answer and 7 random *others* as distractors — with a pool this size
  there are millions of possible 8-button combinations, so the same
  exact round essentially never repeats.
- WORD_ROUNDS: 179 real words across movies, actors, cricketers,
  animals, fruits/veggies, cities, festivals, sports, and general
  objects — kept lowercase since guesses are matched case-insensitively.
"""

import random

from CRAZYHUBBOT.utils.picguess_ai import ai_generate_words

# Lazily-filled cache of AI-generated words (only used if GEMINI_API_KEY
# is set — see picguess_ai.py). Refilled a batch at a time so we don't
# hit the API on every single round.
_ai_cache = []
_ai_recent = []  # last ~60 AI words used, sent to the API as "don't repeat these"


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


EMOJI_POOL = [
    "🔥", "💧", "🌙", "⭐", "🍎", "⚽", "🎸", "🚗", "❤️", "💙", "💚", "🖤", "🤍", "💛", "🧡", "💜", "🐶", "🐱",
    "🐰", "🦊", "🐼", "🐵", "🐯", "🐸", "🐮", "🐷", "🐔", "🐧", "🦉", "🦇", "🐺", "🦄", "🍕", "🍔", "🌮", "🍟",
    "🍩", "🍦", "🍰", "🌭", "🍫", "🍿", "🥤", "🍪", "🍇", "🍉", "🍌", "🍓", "🏀", "🏏", "🎾", "🏐", "🏓", "🥊",
    "🏸", "🏈", "🎳", "🏹", "⛳", "🥋", "🛹", "🚴", "🏊", "🧗", "🎧", "🎤", "🎹", "🎷", "🥁", "🎺", "📻", "🎬",
    "🎨", "🎭", "🎪", "🎡", "🎢", "🎯", "🧩", "🌧️", "☀️", "❄️", "🌪️", "🌈", "⛈️", "🌤️", "☁️", "⚡", "🌊",
    "🌋", "🏔️", "🌵", "🌴", "🌳", "🍁", "🚀", "✈️", "🚁", "🚢", "🛸", "🚂", "🛵", "🚲", "🛴", "🚌", "🚕", "🚓",
    "🚑", "🚒", "🛶", "⛵", "👑", "💎", "🏆", "🎖️", "🥇", "🔱", "🗝️", "⚱️", "💰", "💸", "🎁", "🔔", "🕯️",
    "🧨", "💣", "🪄", "🎮", "🕹️", "📱", "💻", "🖥️", "📺", "🎲", "🃏", "♟️", "🎰", "🧸", "🪀", "🪁", "🧿",
    "🦁", "🐘", "🦒", "🦓", "🐻", "🦌", "🐗", "🦘", "🦔", "🦦", "🦥", "🐨", "🐹", "🐭", "🐁", "🦫", "🌺", "🌹",
    "🌻", "🌷", "🌼", "🌸", "🍀", "🌾", "🍄", "🌿", "☘️", "🪴", "🥀", "💐", "🌱",
]

WORD_ROUNDS = [
    "pushpa", "bahubali", "rrr", "kgf", "dangal", "sholay", "jawan", "pathaan", "animal",
    "gadar", "chennai", "lagaan", "devdas", "krrish", "dhoom", "singham", "drishyam",
    "padmaavat", "tanhaji", "tumbbad", "andhadhun", "gully", "masaan", "udaan", "kaminey",
    "raazi", "talvar", "haider", "omkara", "fukrey", "shahrukh", "salman", "aamir", "akshay",
    "hrithik", "ranbir", "ranveer", "varun", "ajay", "sunny", "deepika", "priyanka", "katrina",
    "alia", "kareena", "anushka", "kajol", "madhuri", "sridevi", "rekha", "kohli", "dhoni",
    "sachin", "rohit", "bumrah", "pandya", "gill", "jadeja", "rahul", "pant", "gambhir",
    "sehwag", "dravid", "ganguly", "kapil", "yuvraj", "harbhajan", "zaheer", "ashwin",
    "kumble", "tiger", "lion", "elephant", "giraffe", "zebra", "monkey", "panda", "kangaroo",
    "dolphin", "penguin", "cheetah", "leopard", "rhino", "hippo", "camel", "wolf", "fox",
    "rabbit", "squirrel", "otter", "eagle", "parrot", "peacock", "sparrow", "owl", "crow",
    "pigeon", "flamingo", "swan", "crane", "mango", "banana", "apple", "orange", "papaya",
    "guava", "pineapple", "watermelon", "grapes", "pomegranate", "potato", "tomato", "onion",
    "carrot", "spinach", "cabbage", "cauliflower", "pumpkin", "cucumber", "radish", "mumbai",
    "delhi", "bangalore", "kolkata", "hyderabad", "jaipur", "lucknow", "pune", "surat",
    "india", "china", "japan", "france", "germany", "brazil", "canada", "russia", "egypt",
    "australia", "diwali", "holi", "dussehra", "navratri", "onam", "pongal", "baisakhi", "eid",
    "christmas", "raksha", "cricket", "football", "hockey", "badminton", "tennis", "kabaddi",
    "wrestling", "boxing", "chess", "volleyball", "guitar", "piano", "violin", "trumpet",
    "laptop", "camera", "rocket", "bicycle", "umbrella", "telescope", "mountain", "volcano",
    "rainbow", "glacier", "desert", "waterfall", "island", "forest", "river", "ocean",
]


def pick_emoji_round(exclude_answer: str = None) -> dict:
    """Picks a random answer emoji plus 7 random distractor emoji from
    EMOJI_POOL — not a fixed pre-paired list, so combinations are for
    all practical purposes unlimited."""
    pool = [e for e in EMOJI_POOL if e != exclude_answer] or EMOJI_POOL
    answer = random.choice(pool)
    remaining = [e for e in EMOJI_POOL if e != answer]
    distractors = random.sample(remaining, min(7, len(remaining)))
    options = distractors + [answer]
    random.shuffle(options)
    return {"answer": answer, "options": options}


def pick_word_round(exclude_answer: str = None) -> str:
    pool = [w for w in WORD_ROUNDS if w != exclude_answer] or WORD_ROUNDS
    return random.choice(pool)


async def pick_word_round_ai(exclude_answer: str = None) -> str:
    """AI-first word picker: uses the AI-generated cache when available
    (refilling it in batches of 15 from Gemini), otherwise falls back
    to the curated WORD_ROUNDS list — same as pick_word_round(). Safe
    to call even if GEMINI_API_KEY was never set: ai_generate_words()
    just returns [] immediately and this falls through to the curated
    list every time, with zero extra latency."""
    global _ai_cache, _ai_recent

    if len(_ai_cache) < 3:
        fresh = await ai_generate_words(count=15, avoid=_ai_recent[-30:])
        for w in fresh:
            if w not in _ai_cache:
                _ai_cache.append(w)

    if _ai_cache:
        word = _ai_cache.pop()
        if word != exclude_answer:
            _ai_recent.append(word)
            if len(_ai_recent) > 60:
                _ai_recent.pop(0)
            return word

    return pick_word_round(exclude_answer)
