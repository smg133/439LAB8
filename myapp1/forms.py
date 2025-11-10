from django import forms
from .models import Contact

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ["name", "address", "profession", "tel_number", "email"]
        
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Full name"}),
            "address": forms.TextInput(attrs={"placeholder": "Address (optional)"}),
            "profession": forms.TextInput(attrs={"placeholder": "Profession (optional)"}),
            "tel_number": forms.TextInput(attrs={"placeholder": "+961 70 123 456"}),
            "email": forms.EmailInput(attrs={"placeholder": "name@example.com"}),
        }
