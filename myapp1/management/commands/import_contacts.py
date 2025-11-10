# myapp1/management/commands/import_contacts.py
import csv
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from myapp1.models import Contact

# Dataset columns in contacts2.csv:
# phone_number, name, email, city, age, sex, married_status, job, income, religion, nationality

COLUMN_MAP = {
    "name": "name",
    "first_name": None,
    "last_name": None,
    "organization": None,

    "email": "email",
    "tel_number": "phone_number",
    "address": None,

    "city": "city",
    "state": None,
    "country": "nationality",
    "postal_code": None,

    # map job -> specialty for recommendations
    "specialty": "job",

    "fee": None,
    "rating": None,
    "latitude": None,
    "longitude": None,
}

# Choose a unique key present in most rows:
UNIQUE_KEY = "email"  # change to "tel_number" if emails are missing or duplicated

def _cast_float(val):
    try:
        return float(val) if val not in (None, "") else None
    except ValueError:
        return None

class Command(BaseCommand):
    help = "Import contacts from CSV into the Contact model."

    def add_arguments(self, parser):
        # default path uses your file name contacts2.csv
        parser.add_argument("--file", type=str, default="myapp1/data/contacts2.csv")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **opts):
        csv_path = Path(opts["file"])
        if not csv_path.exists():
            raise CommandError(f"CSV not found: {csv_path}")

        created = updated = skipped = 0
        count = 0

        with csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = set(reader.fieldnames or [])

            missing = [h for h in COLUMN_MAP.values() if h and h not in headers]
            if missing:
                self.stdout.write(self.style.WARNING(f"Warning: missing columns in CSV: {missing}"))

            for row in reader:
                count += 1
                data = {}
                for field, col in COLUMN_MAP.items():
                    if not col:
                        data[field] = None
                        continue
                    val = row.get(col, "")
                    val = val.strip() if isinstance(val, str) else val
                    if val == "":
                        val = None
                    if field in {"fee", "rating", "latitude", "longitude"}:
                        val = _cast_float(val)
                    data[field] = val

                # ensure a display name
                if not data.get("name"):
                    fn = (data.get("first_name") or "").strip()
                    ln = (data.get("last_name") or "").strip()
                    data["name"] = (fn + " " + ln).strip() or (data.get("organization") or "")

                # derive first/last if only "name" provided
                if data.get("name") and not data.get("first_name") and not data.get("last_name"):
                    parts = data["name"].split()
                    if len(parts) >= 2:
                        data["first_name"] = parts[0]
                        data["last_name"] = " ".join(parts[1:])

                # avoid NOT NULL issues on legacy CharFields (we made them nullable, but keep safe)
                for char_field in ("name","address","profession","tel_number","email"):
                    if data.get(char_field) is None:
                        data[char_field] = None  # ok since model allows nulls

                unique_value = data.get(UNIQUE_KEY)
                if not unique_value:
                    skipped += 1
                    continue

                if opts["dry_run"]:
                    continue

                obj, is_created = Contact.objects.update_or_create(
                    **{UNIQUE_KEY: unique_value},
                    defaults=data
                )
                if is_created:
                    created += 1
                else:
                    updated += 1

                if count % 200 == 0:
                    self.stdout.write(f"Processed {count} rows...")

        self.stdout.write(self.style.SUCCESS(
            f"Done. created={created}, updated={updated}, skipped={skipped}, rows_seen={count}, dry_run={opts['dry_run']}"
        ))
