# myapp1/forms.py
from django import forms
from .models import Contact

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = [
            "name", "email", "tel_number",
            "city", "country", "specialty",
            "address", "state", "postal_code",
            "fee", "rating", "latitude", "longitude",
        ]
