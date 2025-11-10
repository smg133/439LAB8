from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Contact
from .forms import ContactForm
from django.db.models import Q
from .utils import haversine_km

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

def recommendations(request):
    from .models import Contact

    q_spec = request.GET.get("specialty", "").strip()
    q_city = request.GET.get("city", "").strip()
    q_fee  = request.GET.get("max_fee", "").strip()
    q_lat  = request.GET.get("lat", "").strip()
    q_lng  = request.GET.get("lng", "").strip()
    q_maxk = request.GET.get("max_km", "").strip()

    qs = Contact.objects.all()
    if q_spec:
        qs = qs.filter(Q(specialty__icontains=q_spec) | Q(profession__icontains=q_spec))
    if q_city:
        qs = qs.filter(city__icontains=q_city)

    try:
        max_fee = float(q_fee) if q_fee else None
    except ValueError:
        max_fee = None
    if max_fee is not None:
        qs = qs.filter(fee__isnull=False, fee__lte=max_fee)

    lat = float(q_lat) if q_lat else None
    lng = float(q_lng) if q_lng else None
    max_km = float(q_maxk) if q_maxk else None

    results = []
    for c in qs:
        dist = haversine_km(lat, lng, c.latitude, c.longitude) if lat is not None and lng is not None else None
        if max_km is not None and dist is not None and dist > max_km:
            continue
        results.append((dist, c))

    def sort_key(item):
        dist, c = item
        return (1, 0) if dist is None else (0, dist), -(c.rating or 0)

    results.sort(key=sort_key)

    return render(request, "myapp1/recommendations.html", {
        "results": results,
        "params": {"specialty": q_spec, "city": q_city, "max_fee": q_fee, "lat": q_lat, "lng": q_lng, "max_km": q_maxk},
    })
