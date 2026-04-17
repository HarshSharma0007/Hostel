from django.db import models

class Hostel(models.Model):
    name = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def total_floors(self):
        return self.floors.count()

    @property
    def total_rooms(self):
        return sum([f.rooms.count() for f in self.floors.all()])

class Floor(models.Model):
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name='floors')
    floor_number = models.IntegerField()
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('hostel', 'floor_number')

    def __str__(self):
        return f"{self.hostel.name} - Floor {self.floor_number}"

class Room(models.Model):
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('floor', 'room_number')

    def __str__(self):
        return f"Room {self.room_number} ({self.floor})"
