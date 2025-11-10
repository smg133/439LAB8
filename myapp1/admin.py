from django.contrib import admin
from .models import Contact

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "tel_number", "profession")
    search_fields = ("name", "email", "profession", "address", "tel_number")
    list_filter = ("profession",)
