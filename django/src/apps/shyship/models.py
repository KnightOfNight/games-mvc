import random
import uuid

from django.contrib.auth.models import User
from django.db import models

SHIP_SIZES = [5, 4, 3, 3, 2]


def place_ships_randomly():
    forbidden = set()
    result = []
    for size in SHIP_SIZES:
        placed = False
        while not placed:
            horizontal = random.choice([True, False])
            if horizontal:
                row = random.randint(0, 9)
                col = random.randint(0, 10 - size)
                ship = [(row, col + i) for i in range(size)]
            else:
                row = random.randint(0, 10 - size)
                col = random.randint(0, 9)
                ship = [(row + i, col) for i in range(size)]
            if not any(cell in forbidden for cell in ship):
                for r, c in ship:
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            nr, nc = r + dr, c + dc
                            if 0 <= nr <= 9 and 0 <= nc <= 9:
                                forbidden.add((nr, nc))
                result += [[r, c] for r, c in ship]
                placed = True
    return result


class ShyshipGame(models.Model):
    WAITING = 'waiting'
    ACTIVE = 'active'
    DONE = 'done'
    CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (WAITING, 'Waiting'),
        (ACTIVE, 'Active'),
        (DONE, 'Done'),
        (CANCELLED, 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player1 = models.ForeignKey(User, related_name='shyship_p1', on_delete=models.CASCADE)
    player2 = models.ForeignKey(
        User, null=True, blank=True, related_name='shyship_p2', on_delete=models.SET_NULL
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=WAITING)
    winner = models.IntegerField(null=True, blank=True)
    current_turn = models.IntegerField(default=1)
    ships_p1 = models.JSONField(default=list)
    ships_p2 = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        p2 = self.player2.username if self.player2_id else 'waiting...'
        return f'{self.player1.username} vs {p2} [{self.status}]'


class ShyshipMove(models.Model):
    game = models.ForeignKey(ShyshipGame, related_name='moves', on_delete=models.CASCADE)
    player_num = models.IntegerField()
    row = models.IntegerField()
    col = models.IntegerField()
    is_hit = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
