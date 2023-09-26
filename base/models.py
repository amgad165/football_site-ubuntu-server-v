from django.db import models

# Create your models here.

class team_data_modes(models.Model):
    MODE_CHOICES = [
        ('scrape', 'scrape'),
        ('db', 'db'),
      
    ]

    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='db')

    def __str__(self):
        return self.mode
    




class PlayerInfo(models.Model):
    Player = models.CharField(max_length=255)
    Country = models.CharField(max_length=100)
    Position = models.CharField(max_length=100)
    Born = models.CharField(max_length=255)
    Club = models.CharField(max_length=255)

    def __str__(self):
        return self.Player