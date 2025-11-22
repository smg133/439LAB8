# myapp1/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q

from .models import Contact
from .forms import ContactForm
from .utils import haversine_km, parse_nl_query


def contact_list(request):
    q = request.GET.get("q", "").strip()
    qs = Contact.objects.all()
    if q:
        qs = qs.filter(
            Q(name__icontains=q)
            | Q(email__icontains=q)
            | Q(city__icontains=q)
            | Q(specialty__icontains=q)
        )
    return render(request, "myapp1/contact_list.html", {"contacts": qs, "q": q})


def contact_detail(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    return render(request, "myapp1/contact_detail.html", {"contact": contact})


def contact_create(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("contact_list")
    else:
        form = ContactForm()
    return render(request, "myapp1/contact_form.html", {"form": form})


def contact_update(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    if request.method == "POST":
        form = ContactForm(request.POST, instance=contact)
        if form.is_valid():
            form.save()
            return redirect("contact_detail", pk=contact.pk)
    else:
        form = ContactForm(instance=contact)
    return render(request, "myapp1/contact_form.html", {"form": form})


def contact_delete(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    if request.method == "POST":
        contact.delete()
        return redirect("contact_list")
    return render(request, "myapp1/contact_confirm_delete.html", {"contact": contact})


def recommendations(request):
    # Natural-language query
    q_nl = request.GET.get("q_nl", "").strip()

    # Explicit filters
    q_spec = request.GET.get("specialty", "").strip()
    q_city = request.GET.get("city", "").strip()
    q_fee = request.GET.get("max_fee", "").strip()
    q_lat = request.GET.get("lat", "").strip()
    q_lng = request.GET.get("lng", "").strip()
    q_maxk = request.GET.get("max_km", "").strip()
    q_min_rating = request.GET.get("min_rating", "").strip()

    parsed = parse_nl_query(q_nl) if q_nl else {
        "specialty": None,
        "city": None,
        "max_fee": None,
        "min_rating": None,
        "max_km": None,
    }

    # Combine parsed + explicit (explicit overrides)
    specialty = q_spec or parsed["specialty"]
    city = q_city or parsed["city"]

    # max fee
    max_fee = None
    if q_fee:
        try:
            max_fee = float(q_fee)
        except ValueError:
            max_fee = None
    elif parsed["max_fee"] is not None:
        max_fee = parsed["max_fee"]

    # min rating
    min_rating = None
    if q_min_rating:
        try:
            min_rating = float(q_min_rating)
        except ValueError:
            min_rating = None
    elif parsed["min_rating"] is not None:
        min_rating = parsed["min_rating"]

    # distance
    lat = float(q_lat) if q_lat else None
    lng = float(q_lng) if q_lng else None

    max_km = None
    if q_maxk:
        try:
            max_km = float(q_maxk)
        except ValueError:
            max_km = None
    elif parsed["max_km"] is not None:
        max_km = parsed["max_km"]

    # Base queryset
    qs = Contact.objects.all()

    if specialty:
        qs = qs.filter(
            Q(specialty__icontains=specialty)
            | Q(profession__icontains=specialty)
        )

    if city:
        qs = qs.filter(city__icontains=city)

    if max_fee is not None:
        qs = qs.filter(fee__isnull=False, fee__lte=max_fee)

    if min_rating is not None:
        qs = qs.filter(rating__isnull=False, rating__gte=min_rating)

    # Distance filter + sort
    results = []
    for c in qs:
        dist = haversine_km(lat, lng, c.latitude, c.longitude) if (lat is not None and lng is not None) else None
        if max_km is not None and dist is not None and dist > max_km:
            continue
        results.append((dist, c))

    def sort_key(item):
        dist, c = item
        dist_key = 1e9 if dist is None else dist
        fee_val = float(c.fee) if c.fee is not None else 1e9
        rating_val = c.rating or 0.0
        return (dist_key, -rating_val, fee_val)

    results.sort(key=sort_key)

    return render(
        request,
        "myapp1/recommendations.html",
        {
            "results": results,
            "params": {
                "q_nl": q_nl,
                "specialty": specialty or "",
                "city": city or "",
                "max_fee": max_fee if max_fee is not None else "",
                "lat": q_lat,
                "lng": q_lng,
                "max_km": max_km if max_km is not None else "",
                "min_rating": min_rating if min_rating is not None else "",
                "parsed": parsed,
            },
        },
    )
