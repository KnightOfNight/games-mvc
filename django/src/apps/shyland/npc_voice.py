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
