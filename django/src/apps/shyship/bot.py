import random


def _in_bounds(r, c):
    return 0 <= r <= 9 and 0 <= c <= 9


def _random_unfired(fired):
    candidates = [[r, c] for r in range(10) for c in range(10) if (r, c) not in fired]
    return random.choice(candidates) if candidates else None


def _reverse_or_hunt(state, fired):
    if not state.get('reversed'):
        state['dir'] = [-state['dir'][0], -state['dir'][1]]
        state['last_hit'] = state['first_hit']
        state['reversed'] = True
        nr = state['last_hit'][0] + state['dir'][0]
        nc = state['last_hit'][1] + state['dir'][1]
        if _in_bounds(nr, nc) and (nr, nc) not in fired:
            return [nr, nc]
    state.clear()
    return _random_unfired(fired)


def next_bot_cell(state, fired):
    """Return [row, col] for the bot's next shot. Mutates state in place."""
    if not state.get('first_hit'):
        return _random_unfired(fired)

    if state.get('dir'):
        nr = state['last_hit'][0] + state['dir'][0]
        nc = state['last_hit'][1] + state['dir'][1]
        if _in_bounds(nr, nc) and (nr, nc) not in fired:
            return [nr, nc]
        return _reverse_or_hunt(state, fired)

    pending = state.get('pending', [])
    while pending:
        pr, pc = pending[0]
        if _in_bounds(pr, pc) and (pr, pc) not in fired:
            return [pr, pc]
        pending.pop(0)
    state.clear()
    return _random_unfired(fired)


def update_bot_state(state, row, col, is_hit, sunk):
    """Update targeting state after a bot move. Mutates state in place."""
    if sunk:
        state.clear()
        return
    if not is_hit:
        return
    if not state.get('first_hit'):
        state.update({
            'first_hit': [row, col],
            'last_hit': [row, col],
            'dir': None,
            'reversed': False,
            'pending': [[row - 1, col], [row + 1, col], [row, col - 1], [row, col + 1]],
        })
    elif not state.get('dir'):
        state['dir'] = [row - state['first_hit'][0], col - state['first_hit'][1]]
        state['last_hit'] = [row, col]
    else:
        state['last_hit'] = [row, col]
