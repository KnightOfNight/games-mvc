"""v20 brief 3 (#22): the command grammar resolver.

The single authoritative item/NPC-reference matcher. Every command that
takes an object reference resolves it here — there is no other legal
matcher (`parse_item_noun` and the ad-hoc `startswith` matchers it
replaces are gone). Corpse references keep their own small matcher
(`item_utils.parse_corpse_noun`); corpses are not items.

Reference grammar::

    <verb> [all | N] [rarity] [noun]      plus the index form  [rarity] N.noun

- ``all`` — every matching instance. ``N`` — exactly N, all-or-nothing.
- ``rarity`` — closed vocabulary (``RARITY_WORDS``), an instance filter
  applied before matching and selection. Authoring law (enforced by the
  seed verify): no ItemDefinition or NpcDefinition name begins with a
  rarity word, so a leading rarity token is never a name token.
- The noun may be omitted only when a rarity qualifier is present.
- ``N.noun`` — the Nth matching instance in stable age order.

Matching: the reference's tokens must prefix-match the candidate's
display-name-with-tier tokens as an ordered subsequence. Case-
insensitive. A token with no match falls back through plural forms in
order: strip ``es``, strip ``s``, ``ves``→``fe``, ``ies``→``y``.

Ambiguity: matches spanning multiple distinct definitions refuse with a
disambiguation list — never guess across definitions. The only exception
is ``all`` with no noun (``sell all common``, ``loot all``), where the
player explicitly asked for everything.
"""
from dataclasses import dataclass, field

from .item_utils import get_display_name, get_display_name_with_tier

RARITY_WORDS = ('common', 'uncommon', 'rare', 'epic', 'legendary', 'artifact')

RARITY_RANK = {
    'common': 1, 'uncommon': 2, 'rare': 3,
    'epic': 4, 'legendary': 5, 'artifact': 6,
}


def entry_display_name(entry):
    """Player-visible name for a VendorEntry (a definition + tier, not an
    instance), honoring suppress_mk_suffix."""
    name = entry.item_definition.name
    if entry.item_definition.suppress_mk_suffix:
        return name
    return f'{name} Mk {entry.mk_tier}'


# ----------------------------------------------------------------------
# Candidate accessors — one per candidate kind
# ----------------------------------------------------------------------

def _age_key(created_at, pk):
    return (created_at.timestamp() if created_at is not None else 0.0, pk or 0)


class _ItemAccessor:
    """ItemInstance candidates (use/sell/drop/equip/unequip/pickup/
    examine/loot/repair)."""
    @staticmethod
    def tokens(item):
        return get_display_name_with_tier(item).lower().split()

    @staticmethod
    def base_name(item):
        return get_display_name(item)

    @staticmethod
    def def_key(item):
        return item.definition_id if item.definition_id is not None else id(item.definition)

    @staticmethod
    def rarity_rank(item):
        return RARITY_RANK.get(item.rarity, 0)

    @staticmethod
    def rarity(item):
        return item.rarity

    @staticmethod
    def age(item):
        return _age_key(item.created_at, item.pk)

    @staticmethod
    def durability(item):
        return item.durability_current

    @staticmethod
    def is_equipped(item):
        return item.is_equipped


class _EntryAccessor:
    """VendorEntry candidates (buy). Vendor stock mints Common instances,
    so a stock entry's rarity is 'common' for filtering purposes."""
    @staticmethod
    def tokens(entry):
        return entry_display_name(entry).lower().split()

    @staticmethod
    def base_name(entry):
        return entry.item_definition.name

    @staticmethod
    def def_key(entry):
        return (entry.item_definition_id
                if entry.item_definition_id is not None
                else id(entry.item_definition))

    @staticmethod
    def rarity_rank(entry):
        return RARITY_RANK['common']

    @staticmethod
    def rarity(entry):
        return 'common'

    @staticmethod
    def age(entry):
        return _age_key(None, entry.pk)

    @staticmethod
    def durability(entry):
        return 100.0

    @staticmethod
    def is_equipped(entry):
        return False


class _NpcAccessor:
    """NpcInstance candidates (attack/kill)."""
    @staticmethod
    def tokens(npc):
        return npc.definition.name.lower().split()

    @staticmethod
    def base_name(npc):
        return npc.definition.name

    @staticmethod
    def def_key(npc):
        return npc.definition_id if npc.definition_id is not None else id(npc.definition)

    @staticmethod
    def rarity_rank(npc):
        return 0

    @staticmethod
    def rarity(npc):
        return ''

    @staticmethod
    def age(npc):
        return _age_key(getattr(npc, 'spawned_at', None), npc.pk)

    @staticmethod
    def durability(npc):
        return 0.0

    @staticmethod
    def is_equipped(npc):
        return False


_ACCESSORS = {'item': _ItemAccessor, 'entry': _EntryAccessor, 'npc': _NpcAccessor}


# ----------------------------------------------------------------------
# Per-verb policy
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Policy:
    kind: str = 'item'
    # 'lowest': lowest rarity, most damaged, oldest (sell/drop)
    # 'highest': highest rarity, best condition, oldest (equip)
    # 'oldest': oldest only (everything else)
    selection: str = 'oldest'
    allow_quantifier: bool = True     # all / N accepted at all
    bare_all: bool = False            # bare 'all' (no rarity, no noun) allowed
    purchase: bool = False            # N is a purchase count, not a match count (buy)
    allow_rarity: bool = True
    allow_plurals: bool = True
    exclude_equipped: bool = False    # sell/drop: equipped never resolve
    not_found: str = "You aren't carrying that."
    bad_index: str = "You don't have that many of those."
    too_few: str = 'You only have {n}.'
    no_multi: str = ''                # refusal when quantifier not allowed
    bare_all_msg: str = ''            # refusal when bare 'all' not allowed


POLICIES = {
    'use': Policy(
        allow_quantifier=False,
        no_multi="You can't use everything at once.",
    ),
    'equip': Policy(
        selection='highest',
        allow_quantifier=False,
        no_multi="You can't equip everything at once.",
    ),
    'unequip': Policy(
        allow_quantifier=False,
        no_multi="You can't unequip everything at once.",
        not_found="You don't have that equipped.",
        bad_index="You don't have that many of those equipped.",
    ),
    'examine': Policy(
        allow_quantifier=False,
        no_multi="You can't examine everything at once.",
        not_found="You don't see that here.",
        bad_index="There aren't that many of those.",
    ),
    'sell': Policy(
        selection='lowest',
        exclude_equipped=True,
        bare_all_msg="Sell all of what? Try 'sell all <item>' or 'sell all <rarity>'.",
    ),
    'drop': Policy(
        selection='lowest',
        bare_all=True,
        exclude_equipped=True,
    ),
    'pickup': Policy(
        bare_all=True,
        not_found="You don't see that here.",
        bad_index="There aren't that many of those here.",
        too_few='There are only {n} here.',
    ),
    'loot': Policy(
        bare_all=True,
        not_found="You don't see that here.",
        bad_index="There aren't that many of those.",
        too_few='There are only {n}.',
    ),
    'repair': Policy(
        allow_quantifier=False,
        no_multi="Repair one item at a time, or 'repair all'.",
    ),
    'buy': Policy(
        kind='entry',
        purchase=True,
        not_found="They don't sell that.",
        bad_index="They don't sell that many.",
        bare_all_msg="Buy how many? Try 'buy <N> <item>'.",
    ),
    'attack': Policy(
        kind='npc',
        allow_quantifier=False,
        allow_rarity=False,
        allow_plurals=False,
        no_multi='You can only attack one target.',
        not_found="You don't see that here.",
        bad_index="You don't see that here.",
    ),
}


# ----------------------------------------------------------------------
# Result
# ----------------------------------------------------------------------

@dataclass
class Resolution:
    ok: bool
    items: list = field(default_factory=list)
    quantity: int = 1                 # purchase count (buy)
    mode: str = 'single'              # 'single' | 'index' | 'all' | 'count'
    error: str = ''                   # code when not ok
    message: str = ''                 # player-facing refusal line


def _err(code, message):
    return Resolution(ok=False, error=code, message=message)


# ----------------------------------------------------------------------
# Matching
# ----------------------------------------------------------------------

def _plural_variants(token):
    """Fallback forms tried in order when the raw token has no match:
    strip 'es', strip 's', 'ves'→'fe', 'ies'→'y'."""
    variants = []
    if token.endswith('es'):
        variants.append(token[:-2])
    if token.endswith('s'):
        variants.append(token[:-1])
    if token.endswith('ves'):
        variants.append(token[:-3] + 'fe')
    if token.endswith('ies'):
        variants.append(token[:-3] + 'y')
    return variants


def tokens_match(query_tokens, name_tokens, allow_plurals=True):
    """True if every query token prefix-matches a name token, in order,
    as an ordered subsequence. Empty query matches everything."""
    pos = 0
    for qt in query_tokens:
        forms = [qt] + (_plural_variants(qt) if allow_plurals else [])
        found = None
        for form in forms:
            if not form:
                continue
            for i in range(pos, len(name_tokens)):
                if name_tokens[i].startswith(form):
                    found = i
                    break
            if found is not None:
                break
        if found is None:
            return False
        pos = found + 1
    return True


# ----------------------------------------------------------------------
# Resolution
# ----------------------------------------------------------------------

def _selection_sort(matches, acc, selection):
    if selection == 'lowest':
        key = lambda c: (acc.rarity_rank(c), acc.durability(c), acc.age(c))
    elif selection == 'highest':
        key = lambda c: (-acc.rarity_rank(c), -acc.durability(c), acc.age(c))
    else:
        key = acc.age
    return sorted(matches, key=key)


def resolve(verb, args, candidates):
    """Resolve a reference against a candidate list. ``verb`` picks the
    policy (canonical verb name); ``candidates`` come from the calling
    command's scope (see the per-command providers in the consumer)."""
    policy = POLICIES[verb]
    acc = _ACCESSORS[policy.kind]
    tokens = (args or '').strip().lower().split()

    if not tokens:
        return _err('not_found', policy.not_found)

    # [all | N]
    quantifier = None
    if tokens[0] == 'all':
        quantifier = 'all'
        tokens = tokens[1:]
    elif tokens[0].isdigit():
        n = int(tokens[0])
        if n <= 0:
            return _err('not_found', policy.not_found)
        quantifier = n
        tokens = tokens[1:]

    if quantifier is not None and not policy.allow_quantifier:
        return _err('no_multi', policy.no_multi)
    if quantifier == 'all' and policy.purchase:
        return _err('usage', policy.bare_all_msg)

    # [rarity]
    rarity = None
    if policy.allow_rarity and tokens and tokens[0] in RARITY_WORDS:
        rarity = tokens[0]
        tokens = tokens[1:]

    # index form: N.noun on the first noun token
    index = None
    if tokens and '.' in tokens[0]:
        head, rest = tokens[0].split('.', 1)
        if head.isdigit():
            if int(head) <= 0 or not rest:
                return _err('not_found', policy.not_found)
            index = int(head)
            tokens = [rest] + tokens[1:]

    if index is not None and quantifier is not None:
        return _err('usage', "You can't combine a count with an indexed item.")

    noun_tokens = tokens

    # Bare quantifier with nothing to qualify it.
    if not noun_tokens and rarity is None:
        if quantifier == 'all' and policy.bare_all:
            pass  # explicit everything — allowed for this verb
        elif quantifier is not None:
            return _err('usage', policy.bare_all_msg or policy.no_multi
                        or policy.not_found)
        else:
            return _err('not_found', policy.not_found)

    # Rarity filter first, then matching.
    pool = candidates
    if rarity is not None:
        pool = [c for c in pool if acc.rarity(c) == rarity]

    matches = [c for c in pool
               if tokens_match(noun_tokens, acc.tokens(c), policy.allow_plurals)]

    if policy.exclude_equipped:
        unequipped = [c for c in matches if not acc.is_equipped(c)]
        if matches and not unequipped:
            return _err('equipped', "You'll have to unequip it first.")
        matches = unequipped

    if not matches:
        return _err('not_found', policy.not_found)

    # Cross-definition ambiguity: never guess. The one exception is an
    # explicit 'all' with no noun ('sell all common', 'loot all').
    def_keys = {acc.def_key(c) for c in matches}
    if len(def_keys) > 1 and not (quantifier == 'all' and not noun_tokens):
        by_age = sorted(matches, key=acc.age)
        names, seen = [], set()
        for c in by_age:
            name = acc.base_name(c)
            if name not in seen:
                seen.add(name)
                names.append(name)
        return _err('ambiguous', f"Which do you mean: {', '.join(names)}?")

    if index is not None:
        by_age = sorted(matches, key=acc.age)
        if index > len(by_age):
            return _err('bad_index', policy.bad_index)
        return Resolution(ok=True, items=[by_age[index - 1]], mode='index')

    ordered = _selection_sort(matches, acc, policy.selection)

    if policy.purchase:
        quantity = quantifier if isinstance(quantifier, int) else 1
        return Resolution(ok=True, items=[ordered[0]], quantity=quantity,
                          mode='count' if quantity > 1 else 'single')

    if quantifier == 'all':
        return Resolution(ok=True, items=ordered, mode='all')
    if isinstance(quantifier, int):
        if quantifier > len(ordered):
            return _err('too_few', policy.too_few.format(n=len(ordered)))
        return Resolution(ok=True, items=ordered[:quantifier], mode='count')

    return Resolution(ok=True, items=[ordered[0]], mode='single')


# ----------------------------------------------------------------------
# Tab completion (v20 brief 3, #19)
# ----------------------------------------------------------------------

COMPLETION_CAP = 50


def complete(verb, arg_text, candidates):
    """Server-side argument completion: options for the last (possibly
    empty) token of ``arg_text``, drawn from the same candidate scope the
    verb resolves against, plus grammar qualifier words where valid."""
    policy = POLICIES.get(verb)
    if policy is None:
        return []
    acc = _ACCESSORS[policy.kind]

    # Split into completed words and the trailing partial token.
    if arg_text.endswith(' ') or not arg_text:
        prev, partial = arg_text.lower().split(), ''
    else:
        words = arg_text.lower().split()
        prev, partial = words[:-1], words[-1]

    # Consume leading qualifiers already typed.
    consumed_rarity = None
    noun_prev = list(prev)
    qualifiers_done = 0
    if noun_prev and (noun_prev[0] == 'all' or noun_prev[0].isdigit()):
        noun_prev.pop(0)
        qualifiers_done += 1
    if policy.allow_rarity and noun_prev and noun_prev[0] in RARITY_WORDS:
        consumed_rarity = noun_prev.pop(0)
        qualifiers_done += 1

    pool = candidates
    if consumed_rarity is not None:
        pool = [c for c in pool if acc.rarity(c) == consumed_rarity]

    options = set()
    for cand in pool:
        name_tokens = acc.tokens(cand)
        if not tokens_match(noun_prev, name_tokens, policy.allow_plurals):
            continue
        for t in name_tokens:
            if t.startswith(partial):
                options.add(t)

    # Qualifier words are only valid before any noun token.
    if not noun_prev:
        if policy.allow_quantifier and not policy.purchase and qualifiers_done == 0:
            if 'all'.startswith(partial):
                options.add('all')
        if policy.allow_rarity and consumed_rarity is None:
            rarities_present = {acc.rarity(c) for c in candidates}
            for word in RARITY_WORDS:
                if word.startswith(partial) and word in rarities_present:
                    options.add(word)

    return sorted(options)[:COMPLETION_CAP]
