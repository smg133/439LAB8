# myapp1/models.py
from django.db import models
from django.core.validators import RegexValidator

class Contact(models.Model):
    # original fields, now nullable
    name = models.CharField(max_length=255, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    profession = models.CharField(max_length=120, blank=True, null=True)

    phone_regex = RegexValidator(
        regex=r'^\+?[0-9\s\-()]{7,20}$',
        message="Enter a valid phone number."
    )
    tel_number = models.CharField(
        max_length=25,
        validators=[phone_regex],
        verbose_name="Telephone",
        blank=True,
        null=True,
    )

    email = models.EmailField(blank=True, null=True)

    # dataset-friendly fields
    first_name = models.CharField(max_length=120, blank=True, null=True)
    last_name  = models.CharField(max_length=120, blank=True, null=True)
    organization = models.CharField(max_length=255, blank=True, null=True)

    city = models.CharField(max_length=120, blank=True, null=True)
    state = models.CharField(max_length=120, blank=True, null=True)
    country = models.CharField(max_length=120, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)

    specialty = models.CharField(max_length=120, blank=True, null=True)
    fee = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    rating = models.FloatField(null=True, blank=True)

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["tel_number"]),
            models.Index(fields=["city"]),
            models.Index(fields=["specialty"]),
        ]

    def display_name(self):
        if self.name:
            return self.name
        if self.organization:
            return self.organization
        fn = (self.first_name or "").strip()
        ln = (self.last_name or "").strip()
        full = (fn + " " + ln).strip()
        return full or (self.email or "Contact")

    def __str__(self):
        return self.display_name()
