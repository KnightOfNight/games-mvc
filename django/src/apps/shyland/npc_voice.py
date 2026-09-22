"""v23 B4 (#40): the NPC voice pools.

Every transactional and reactive line that used to be a single hardcoded
string lives here as a pool. Selection is plain random choice — the
kibitz-style pattern that already existed, per the #40 ruling. No
per-player last-line state is tracked; these lines are low-frequency
enough that consecutive repeats are acceptable and stateful selection
would be novel architecture the ruling excluded.

NO-LEAK RULE (#138, operator ruling 2026-07-24): no line in this module
may name or imply an item's rarity, tier, or true name. Unidentified
items veil all three, and vendor speech must not lift the veil. Refusal
pools are deliberately generic so that they read correctly for any
non-sellable category, present or future.
"""
import random


def pick(pool, **fields):
    """Choose a line at random and substitute {placeholders}."""
    line = random.choice(pool)
    for key, value in fields.items():
        line = line.replace('{' + key + '}', str(value))
    return line


# --- Sell refusals (#138). Generic by ruling: never name the rarity. ---
SELL_REFUSAL_SINGLE = [
    '{vendor} looks it over and pushes it back toward you. "I\'m not interested in that."',
    '{vendor} does not reach for it. "I don\'t want to buy that."',
    '{vendor} declines. "That is not something I can put a number on."',
    '"No," {vendor} says. "Not that one."',
    '{vendor} returns it to you unpriced. "Keep it."',
    '{vendor} considers it, then sets it down again. "I would not know what to ask for it."',
]

SELL_REFUSAL_PARTIAL = [
    '{vendor} counts out the coin. "I took what I wanted, you can keep the rest."',
    '"That\'s all I want from you today," {vendor} says. "You can keep the other items for now."',
    '{vendor} pushes the remainder back across to you. "The rest stays yours."',
    '"I\'ll take these," {vendor} says. "Not the rest."',
]

SELL_REFUSAL_NONE = [
    '{vendor} looks over what you\'re carrying and declines all of it. "I\'m not interested in any of it."',
    '"I don\'t recognize anything you\'re carrying," {vendor} says, "and I wouldn\'t even know how much to pay you for it."',
    '{vendor} takes nothing. "There\'s nothing here I can use."',
    '"Not today," {vendor} says. "None of it."',
]

# Last-ditch guard rail. Not a pool: it has no population today (after
# #138, artifacts are the only refusable category and they have voiced
# pools above). If this string ever appears in play, that is the signal
# that a new non-sellable category shipped without its own voice — author
# a proper pool then.
SELL_REFUSAL_FALLBACK = "You can't sell that."


# --- Sell acknowledgments (#40). ---
SELL_SINGLE = [
    'You sell {name} for {amount}.',
    '{vendor} takes {name} and pays you {amount}.',
    '{name} changes hands for {amount}.',
    'You part with {name}. {vendor} parts with {amount}.',
]

SELL_BULK = [
    'You sell {name} ×{qty} for {amount}.',
    '{vendor} takes {name} ×{qty} and counts out {amount}.',
    'You sell {name} ×{qty}. {amount} for the lot.',
]

# --- Worthless acceptance (#138). Replaces the payment sentence. ---
SELL_WORTHLESS_SINGLE = [
    '{vendor} takes {name} off your hands. No coin changes hands, and none was going to.',
    '"I\'ll get rid of that for you," {vendor} says, taking {name}. "Free of charge. Mine, not yours."',
    '{vendor} accepts {name} the way one accepts trash from a guest: politely, and straight into the bin.',
    '{vendor} takes {name} and pays you exactly what it\'s worth. Nothing.',
    '"You want this gone? It\'s gone," {vendor} says, and {name} disappears under the counter. No coin follows.',
]

SELL_WORTHLESS_TRAILING = [
    '{vendor} sweeps the rest off the counter too. "That I\'ll take for free — call it a courtesy."',
    '"And I\'ll take the junk off your hands as well," {vendor} adds. "No charge. To either of us."',
    '{vendor} takes the worthless remainder as well, and pays for exactly none of it.',
    '"The rest isn\'t worth coin," {vendor} says, dropping it out of sight anyway. "But it\'s gone."',
]

# --- Buy acknowledgments (#40). The vendor never spoke here before. ---
BUY_SINGLE = [
    'You buy {name} for {amount}.',
    '{vendor} takes your coin and hands over {name}. ({amount})',
    'You hand over {amount}; {vendor} hands over {name}.',
    '{name} is yours for {amount}.',
]

BUY_BULK = [
    'You buy {name} ×{qty} for {amount}.',
    '{vendor} counts out {name} ×{qty} and takes {amount} for the lot.',
    'You buy {name} ×{qty}. {amount}, all told.',
]

SOLD_OUT = [
    'Sold out.',
    'That shelf is empty.',
    '{vendor} has none of those left.',
]


# --- Free repair (#40). Keyed by NPC slug; per-NPC voice. ---
PITY_REPAIR_LINES = {
    'morra': [
        'Morra turns the piece over once, snorts softly, and fixes it for '
        'nothing. "Come back when you\'ve got something worth charging for."',
        'Morra fixes it without asking and without charging. "I\'m not taking '
        'coin for that. I\'d be embarrassed."',
        'Morra works the damage out in three motions and waves you off. '
        '"Don\'t. Just don\'t."',
    ],
    'pella': [
        "Pella tuts over the wear like it's a personal affront and mends it "
        'free. "There. Don\'t thank me, just eat something."',
        'Pella has it mended before you\'ve finished offering to pay. "Coin? '
        'For that? Absolutely not."',
        'Pella repairs it and presses it back into your hands. "No charge. '
        'You\'ll be back with something worse, and I\'ll charge you then."',
    ],
    'ferwick': [
        'Ferwick waves off payment before you can reach for your purse. '
        '"The city gave it to you; the city can keep it standing."',
        'Ferwick mends it and refuses your coin twice. "It costs the city '
        'nothing. It costs you nothing. Good."',
        'Ferwick sets it right and shrugs. "Free issue, free repair. That\'s '
        'how it was explained to me, anyway."',
    ],
    'repairbot-prime': [
        'Repairbot Prime completes the work in silence. "COST: NEGLIGIBLE. '
        'WAIVED. MAINTAIN YOUR EQUIPMENT."',
        'Repairbot Prime restores the item in four seconds. "BILLING SKIPPED. '
        'VALUE BELOW THRESHOLD. NEXT."',
        'Repairbot Prime repairs it without prompting. "NO CHARGE ISSUED. THIS '
        'UNIT DECLINES TO INVOICE FOR THAT."',
    ],
    'maro-the-mender': [
        'Maro mends it on the bench without looking up. "That one\'s free. '
        'Wouldn\'t feel right otherwise."',
        'Maro turns it in the light, fixes it, and hands it back. "No charge. '
        'Bring me something harder next time."',
        'Maro repairs it and glances at the shard as if checking. "Free," he '
        'says. "We agree on that."',
    ],
    'tavik-the-mender': [
        'Tavik has it stitched before you sit down. "Nothing owed. It was '
        'barely work."',
        'Tavik mends it and sets it beside you. "Travelers always need '
        'something sewn. I don\'t charge for the easy ones."',
        'Tavik works the awl through twice and calls it done. "Keep your coin. '
        'That wasn\'t worth taking it for."',
    ],
    'old-brammel': [
        'Old Brammel repairs it by the light of the little lamp and refuses '
        'payment. "Not for that, friend. Not for that."',
        'Old Brammel mends it, slow and sure. "No coin. I\'ve been doing this '
        'longer than that thing\'s been broken."',
        'Old Brammel hands it back mended. "Free. Tell the lamp I said so."',
    ],
}

PITY_REPAIR_FALLBACK = [
    '{name} looks your battered gear over, takes pity, and repairs it for nothing.',
    '{name} fixes it without mentioning a price, which is its own kind of answer.',
    '{name} makes the repair and waves off your coin.',
]

# --- Paid repair outcomes (#40). Shared pools: the composition sites
# interpolate the repairer where they already had it, and the bulk sweep
# never named the repairer to begin with. Per-repairer voice here would
# need architecture the ruling excluded. ---
REPAIR_SUCCESS_BULK = [
    '{name} is restored to full condition. ({cost})',
    '{name} comes back sound. ({cost})',
    '{name} is whole again. ({cost})',
    'The work holds — {name} is as good as it was. ({cost})',
]

REPAIR_SUCCESS_SINGLE = [
    '{repairer} restores your {name} to full condition. ({cost})',
    '{repairer} works the damage out of your {name} and hands it back sound. ({cost})',
    '{repairer} takes your {name}, takes their time, and returns it whole. ({cost})',
    'Your {name} comes back from {repairer} in full condition. ({cost})',
]

REPAIR_FAIL_BULK = [
    "The mending on {name} didn't take. ({cost})",
    'The repair on {name} fails to hold. ({cost})',
    '{name} resists the work — no better than before. ({cost})',
    'The fix on {name} comes apart under the tools. ({cost})',
]

REPAIR_FAIL_SINGLE = [
    "{repairer} works on your {name}, but the mending didn't take. ({cost})",
    '{repairer} tries your {name} twice and gives up. Nothing holds. ({cost})',
    '{repairer} does the work, but your {name} is no better for it. ({cost})',
    'Your {name} defeats {repairer} — the repair simply refuses to set. ({cost})',
]

REPAIR_POOR_BULK = [
    "You can't afford to repair {name} ({cost}) — you stop there.",
    'Repairing {name} would cost {cost}. You stop there.',
    "{name} needs {cost} you don't have. The sweep stops there.",
]

REPAIR_POOR_SINGLE = [
    "Repairing your {name} costs {cost} — you can't afford it.",
    'Your {name} would take {cost} to mend. You have less.',
    "{cost} to fix your {name}. You can't cover it.",
]


# --- Curse cleansing (v26.3, #297). Keyed by cleanser slug; per-NPC
# voice, narration form (the NPC's name inside the line, quoted speech
# allowed). Placeholders: {item}, {price}. The no-leak rule holds here
# too: no line names a curse's identity or effect — "the curse" and
# "something wrong" are as specific as the voice gets. ---
CLEANSE_SUCCESS_LINES = {
    'mother-tansy': [
        'Mother Tansy takes your {item} in both hands, murmurs something '
        'older than the ring, and hands it back lighter. "There, love. '
        'It\'s only itself now." ({price})',
        'Mother Tansy rubs a bitter-smelling salve along your {item} until '
        'the wrongness lets go. "Done. Don\'t go finding another one." '
        '({price})',
        'Mother Tansy works over your {item} with smoke and patience, and '
        'whatever was in it leaves. "That\'s the last of it, love." '
        '({price})',
    ],
    'maro-the-mender': [
        'Maro sets your {item} on the bench, works at it in silence, and '
        'hands it back clean. "It\'s out. Mind what you pick up." ({price})',
        'Maro turns your {item} in the light until the wrongness shows, '
        'then draws it off like a splinter. "Done," he says. ({price})',
        'Maro holds your {item} still a long moment. Something leaves it. '
        '"That\'s it gone. The item\'s sound." ({price})',
    ],
    'tavik-the-mender': [
        'Tavik picks the curse out of your {item} like a bad seam, one '
        'thread at a time. "There. It\'ll carry easier now." ({price})',
        'Tavik works over your {item} with needle-fine care until it sits '
        'quiet. "Gone. Travelers bring me worse every season." ({price})',
        'Tavik smooths your {item} flat, and what was knotted into it '
        'unravels. "Done and paid for. Safe roads." ({price})',
    ],
    'old-brammel': [
        'Old Brammel holds your {item} near the little lamp until the '
        'shadow in it thins and goes. "There, friend. All quiet now." '
        '({price})',
        'Old Brammel works at your {item}, slow and sure, and the wrongness '
        'gives up before he does. ({price})',
        'Old Brammel murmurs to your {item} like an old acquaintance, and '
        'whatever held it lets go. "Tell the lamp I said thanks." ({price})',
    ],
}

CLEANSE_SUCCESS_FALLBACK = [
    '{name} works the curse out of your {item} and hands it back clean. ({price})',
    '{name} draws whatever was in your {item} away. It sits quiet now. ({price})',
    '{name} takes your {item}, takes their time, and returns it free of its curse. ({price})',
]

# The refusal is the quote: every line names {price}.
CLEANSE_POOR_LINES = {
    'mother-tansy': [
        'Mother Tansy names her price — {price} — and pats your hand when '
        'you come up short. "Come back when you\'ve got it, love. It\'ll '
        'keep. That\'s the trouble with these things."',
        '"That\'s {price} to lift, love," Mother Tansy says, "and you '
        'haven\'t got it. I don\'t work these on credit."',
        'Mother Tansy counts what you have without touching it. "{price}, '
        'and not a copper less. The remedy costs what it costs."',
    ],
    'maro-the-mender': [
        '"{price}," Maro says, and looks at your purse. "You\'re short. '
        'Come back when you\'re not."',
        'Maro names the work at {price} and shakes his head at your coin. '
        '"Not enough. It stays in until it\'s paid."',
        'Maro sets the price at {price}. "That\'s the cost. I don\'t haggle '
        'with curses, or about them."',
    ],
    'tavik-the-mender': [
        '"That kind of unpicking runs {price}," Tavik says, eyeing your '
        'purse. "You\'re light. It\'ll wait — that sort always waits."',
        'Tavik quotes {price} and folds his hands. "Short. Come back with '
        'the full amount and I\'ll start that hour."',
        '"{price} for that work," Tavik says. "No less. Bad stitching is '
        'free everywhere; good unstitching costs."',
    ],
    'old-brammel': [
        'Old Brammel names it gently: {price}. "You haven\'t the coin, '
        'friend. It\'s dear work. Come back — it\'ll still be here, more\'s '
        'the pity."',
        '"That one runs {price}," Old Brammel says, "and I can see from '
        'here you\'re short. No shame in it. Come back."',
        'Old Brammel looks from the item to your purse and back. "{price}, '
        'friend. The lamp and I don\'t do it cheaper."',
    ],
}

CLEANSE_POOR_FALLBACK = [
    '{name} names the price — {price} — and you can\'t cover it. The curse stays.',
    '"{price}," {name} says. You come up short, and the work goes undone.',
    '{name} quotes {price} for the lifting. Your purse says otherwise.',
]

CLEANSE_NOTHING_LINES = {
    'mother-tansy': [
        'Mother Tansy turns your {item} over once and hands it straight '
        'back. "Nothing in that but honest wear, love."',
        'Mother Tansy sniffs at your {item} and shakes her head. "That '
        'one\'s clean. Save your coin for the draughts."',
        '"There\'s no curse in that," Mother Tansy says, handing back your '
        '{item}. "Whatever it\'s done to you, it did fairly."',
    ],
    'maro-the-mender': [
        'Maro glances at your {item} and pushes it back. "Nothing in it. '
        'Don\'t pay me to fix what isn\'t broken that way."',
        '"Clean," Maro says, barely looking up from the bench. "Nothing '
        'riding that one."',
        'Maro weighs your {item} in one hand. "No curse. You\'re carrying '
        'worry, not trouble."',
    ],
    'tavik-the-mender': [
        'Tavik runs a thumb along your {item} and hands it back. "Every '
        'thread of that is exactly where it should be. Nothing to unpick."',
        '"That one\'s clean," Tavik says. "I\'d charge you for the look, '
        'but it was a short look."',
        'Tavik barely glances at your {item}. "Nothing in it. Travelers '
        'worry more than they\'re cursed — it\'s the better problem."',
    ],
    'old-brammel': [
        'Old Brammel holds your {item} to the little lamp and smiles. '
        '"Clean as morning, friend. Nothing for me to do."',
        '"No, friend," Old Brammel says, handing your {item} back. "That '
        'one carries nothing it shouldn\'t."',
        'Old Brammel listens to your {item} a moment, the way he does. '
        '"Quiet," he says. "Keep it well."',
    ],
}

CLEANSE_NOTHING_FALLBACK = [
    '{name} looks your {item} over and finds nothing to lift. No charge.',
    '{name} hands your {item} back. "There\'s no curse in that."',
    '{name} checks your {item} and waves you off — it carries nothing wrong.',
]


# --- The inspect sweep (v26.3, #297). Same shape. Placeholders:
# {count}, {price}. NEVER name a curse's identity or effect here —
# presence only; the itemized lines that follow the found line are
# composed item lines, not voice. ---
INSPECT_CLEAN_LINES = {
    'mother-tansy': [
        'Mother Tansy goes through your pack piece by piece, unhurried, '
        'and finds nothing that bites. "All clean, love." ({price})',
        'Mother Tansy sweeps her hands over everything you carry and nods. '
        '"Not a whisper of anything wrong." ({price})',
        '"Clean through, love," Mother Tansy says, closing your pack. '
        '"Every piece of it." ({price})',
    ],
    'maro-the-mender': [
        'Maro goes through your gear methodically, sets the last piece '
        'down, and nods once. "Clean. All of it." ({price})',
        'Maro checks everything you carry against some standard only he '
        'knows. "Nothing in any of it," he says. ({price})',
        '"Your pack\'s sound," Maro says, pushing it back across the '
        'bench. "No curses." ({price})',
    ],
    'tavik-the-mender': [
        'Tavik runs every piece you carry through his hands like cloth off '
        'a bolt. "All of it clean." ({price})',
        'Tavik checks seam by seam, item by item, and finds nothing. '
        '"You carry nothing cursed." ({price})',
        '"Clean," Tavik says, repacking your things neater than you had '
        'them. "Every piece." ({price})',
    ],
    'old-brammel': [
        'Old Brammel goes through your pack by lamplight, slow and '
        'thorough, and finds only honest gear. "All quiet, friend." '
        '({price})',
        '"Nothing, friend," Old Brammel says when the last piece is '
        'checked. "Your pack\'s as clean as the lamp is old." ({price})',
        'Old Brammel touches each thing you carry in turn and smiles at '
        'the end of it. "No curses here." ({price})',
    ],
}

INSPECT_CLEAN_FALLBACK = [
    '{name} sweeps everything you carry and finds no curses. ({price})',
    '{name} checks your pack piece by piece — all clean. ({price})',
    '{name} goes through your gear and hands it back untroubled. ({price})',
]

INSPECT_FOUND_LINES = {
    'mother-tansy': [
        'Mother Tansy stops partway through your pack, mouth tightening. '
        '"There\'s trouble in here, love. {count} of these — I\'ll show '
        'you which." ({price})',
        'Mother Tansy finishes the sweep and sets {count} of your things '
        'apart from the rest, careful not to linger on them. "Those." '
        '({price})',
        '"You\'ve been carrying bad company, love," Mother Tansy says, '
        'tapping the air over {count} of your things. ({price})',
    ],
    'maro-the-mender': [
        'Maro works through your gear and sets {count} of your things '
        'apart without comment. Then: "Those. Cursed." ({price})',
        '"Found some," Maro says flatly, and counts off {count}. "Cursed, '
        'the lot of them." ({price})',
        'Maro finishes the check and holds up {count} fingers. "That many. '
        'I\'ll name them." ({price})',
    ],
    'tavik-the-mender': [
        'Tavik stops twice mid-sweep, then lays {count} of your things '
        'apart from the rest. "Bad thread in those." ({price})',
        '"Some of this is knotted wrong," Tavik says, separating {count} '
        'pieces. "Cursed. I\'ll point them out." ({price})',
        'Tavik finishes and taps the pile he\'s made — {count} of your '
        'things. "Those carry curses." ({price})',
    ],
    'old-brammel': [
        'Old Brammel goes quiet partway through, and by the end has set '
        '{count} of your things by the lamp. "Those are cursed, friend." '
        '({price})',
        '"I\'m sorry, friend," Old Brammel says, and shows you {count} of '
        'your things. "Cursed, each one. Best you know." ({price})',
        'Old Brammel finishes the sweep slower than he started it. '
        '"{count} of them, friend. Cursed. Here." ({price})',
    ],
}

INSPECT_FOUND_FALLBACK = [
    '{name} sweeps your pack and sets {count} of your things apart — cursed. ({price})',
    '{name} finds curses on {count} of the things you carry. ({price})',
    '{name} finishes the sweep grim-faced: {count} cursed. ({price})',
]

INSPECT_POOR_LINES = {
    'mother-tansy': [
        '"A sweep of all that runs {price}, love," Mother Tansy says, '
        'eyeing your purse. "And you haven\'t got it. Come back heavier."',
        'Mother Tansy tallies your pack at a glance. "{price} to check the '
        'lot. You\'re short, love. The worry\'s free; the sweep isn\'t."',
        'Mother Tansy shakes her head kindly. "{price} for the full '
        'going-over, and you can\'t cover it. Off you go."',
    ],
    'maro-the-mender': [
        '"{price} to check all that," Maro says. "You\'re short. Come back '
        'when you\'re not."',
        'Maro counts your gear, names {price}, and looks at your purse. '
        '"No. Not on credit."',
        '"The sweep costs {price}," Maro says, already turning back to the '
        'bench. "You haven\'t got it."',
    ],
    'tavik-the-mender': [
        '"Piece rate," Tavik says. "{price} for everything you\'re '
        'carrying. You\'re light. Come back with it."',
        'Tavik tallies the sweep at {price} and shakes his head at your '
        'coin. "Short. The checking waits."',
        '"{price} for the full look-through," Tavik says. "You can\'t '
        'cover it. No offense meant — the rate\'s the rate."',
    ],
    'old-brammel': [
        '"That much gear runs {price} to check, friend," Old Brammel says, '
        '"and you haven\'t the coin. Come back — the lamp and I keep long '
        'hours."',
        'Old Brammel names it gently: {price}. "More than you\'ve got, '
        'friend. No harm in that. Another day."',
        '"{price}, friend," Old Brammel says, "and I can see you\'re '
        'short. The sweep will keep. I hope your pack does too."',
    ],
}

INSPECT_POOR_FALLBACK = [
    '{name} names the sweep at {price} — more than you\'re carrying in coin.',
    '"{price} for the full check," {name} says. You can\'t cover it.',
    '{name} quotes {price} to sweep your pack. Your purse disagrees.',
]


# v23 brief 5 (#147): the render rule. Keyword responses are SPEECH — they
# take the 'Name: ' attribution and the say color, matching player speech.
# Greeting and departure entries are NARRATION — authored in the third person,
# they broadcast verbatim at category 'room', unprefixed and unconnectived.
# Mirrors DialogueEntry.ENTRY_KEYWORD; the lockstep is guarded by test.
SPEECH_ENTRY_TYPES = ('keyword',)


def dialogue_line(entry_type, npc_name, text):
    """Compose one delivered dialogue line. Returns (text, category)."""
    if entry_type in SPEECH_ENTRY_TYPES:
        return (f'{npc_name}: {text}', 'say')
    return (text, 'room')


# --- Kibitz (#40). Machinery already existed; the pool grows. ---
KIBITZ_LINES = [
    '{other} watches the exchange and nods approvingly.',
    '{other} pretends not to supervise, and supervises.',
    '{other} rearranges the shelf, satisfied.',
    '{other} makes a small noise that could be approval or indigestion.',
    '{other} counts something on the far shelf, twice, loudly.',
    '{other} looks away the instant you glance over.',
]

# --- Aggro engagement (#40). One string served every aggressive NPC in
# the game at three call sites. {name} is the ordinal-aware display name.
AGGRO_ENGAGE = [
    '{name} snarls and moves to attack!',
    '{name} closes on you without warning!',
    '{name} sees you and comes straight in!',
    '{name} breaks toward you, fast!',
    '{name} gives no warning at all — it attacks!',
    '{name} turns on you and charges!',
]
