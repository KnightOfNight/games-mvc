from django.test import TestCase
from apps.shyland.models import Area, Room, Zone


class AreaModelTests(TestCase):

    def setUp(self):
        self.zone = Zone.objects.create(
            name='Test Zone',
            slug='test-zone',
            genre_tone='Test',
            danger_level='beginner',
            description='A test zone.',
        )
        self.area = Area.objects.create(
            zone=self.zone,
            name='Test Market',
            slug='test-market',
            area_description='Busy market sounds fill the air.',
        )
        self.room_with_area = Room.objects.create(
            zone=self.zone,
            area=self.area,
            name='Market Stall',
            description='A vendor eyes you from behind a counter.',
            brief_description='A market stall.',
        )
        self.room_without_area = Room.objects.create(
            zone=self.zone,
            area=None,
            name='Empty Road',
            description='A dusty road.',
            brief_description='A dusty road.',
        )

    def test_area_str(self):
        self.assertEqual(str(self.area), 'Test Zone / Test Market')

    def test_room_area_relationship(self):
        self.assertEqual(self.room_with_area.area, self.area)
        self.assertIsNone(self.room_without_area.area)

    def test_area_rooms_related_manager(self):
        self.assertIn(self.room_with_area, self.area.rooms.all())
        self.assertNotIn(self.room_without_area, self.area.rooms.all())

    def test_zone_areas_related_manager(self):
        self.assertIn(self.area, self.zone.areas.all())

    def test_room_without_area_does_not_break(self):
        """Rooms without an area must remain fully functional."""
        room = self.room_without_area
        self.assertIsNone(room.area)
        exits = room.exits()
        self.assertIsInstance(exits, dict)
