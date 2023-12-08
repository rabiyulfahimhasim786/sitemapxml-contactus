# models.py
from django.db import models

class ContactInfo(models.Model):
    url = models.URLField()
    emails = models.TextField(blank=True)
    phones = models.TextField(blank=True)

    def __str__(self):
        return self.url



