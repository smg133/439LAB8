from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Contact
from .forms import ContactForm

def contact_list(request):
    q = request.GET.get("q", "")
    contacts = Contact.objects.all()
    if q:
        contacts = contacts.filter(name__icontains=q)
    return render(request, "myapp1/contact_list.html", {"contacts": contacts, "q": q})

def contact_detail(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    return render(request, "myapp1/contact_detail.html", {"contact": contact})

def contact_create(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Contact added.")
            return redirect("contact_list")
    else:
        form = ContactForm()
    return render(request, "myapp1/contact_form.html", {"form": form, "title": "Add Contact"})

def contact_update(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    if request.method == "POST":
        form = ContactForm(request.POST, instance=contact)
        if form.is_valid():
            form.save()
            messages.success(request, "Contact updated.")
            return redirect("contact_detail", pk=pk)
    else:
        form = ContactForm(instance=contact)
    return render(request, "myapp1/contact_form.html", {"form": form, "title": "Edit Contact"})

def contact_delete(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    if request.method == "POST":
        contact.delete()
        messages.success(request, "Contact deleted.")
        return redirect("contact_list")
    return render(request, "myapp1/contact_confirm_delete.html", {"contact": contact})
