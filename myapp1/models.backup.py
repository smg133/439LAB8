from django.db import models
from django.core.validators import RegexValidator

class Contact(models.Model):
    name = models.CharField(max_length=120)
    address = models.CharField(max_length=255, blank=True)
    profession = models.CharField(max_length=120, blank=True)

    phone_regex = RegexValidator(
        regex=r'^\+?[0-9\s\-()]{7,20}$',
        message="Enter a valid phone number."
    )
    tel_number = models.CharField(max_length=20, validators=[phone_regex], verbose_name="Telephone")

    email = models.EmailField()

    def __str__(self):
        return f"{self.name} ({self.email})"
