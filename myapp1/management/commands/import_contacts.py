# myapp1/management/commands/import_contacts.py
import csv
from pathlib import Path
from typing import Dict, Any, Optional

from django.core.management.base import BaseCommand, CommandError
from myapp1.models import Contact

COLUMN_MAP: Dict[str, Optional[str]] = {
    "name": "name",
    "first_name": None,
    "last_name": None,
    "organization": "organization",

    "email": "email",
    "tel_number": "tel_number",
    "address": "address",

    "city": "city",
    "state": None,
    "country": None,
    "postal_code": None,

    "specialty": "specialty",
    "fee": "fee",
    "rating": "rating",
    "latitude": "lat",
    "longitude": "lng",
}

UNIQUE_KEY_DEFAULT = "email"

def _cast_float(val: Any) -> Optional[float]:
    if val in (None, ""):
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None

class Command(BaseCommand):
    help = "Import contacts from CSV into the Contact model (idempotent upsert)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default="myapp1/data/contacts_reco_400.csv",  # <--- IMPORTANT
            help="Path to CSV file",
        )
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--unique-key", type=str, default=UNIQUE_KEY_DEFAULT)
        parser.add_argument("--limit", type=int, default=None)
        parser.add_argument("--verbose-every", type=int, default=200)

    def handle(self, *args, **opts):
        csv_path = Path(opts["file"])
        dry_run = bool(opts["dry_run"])
        unique_key = str(opts["unique_key"])
        limit = opts["limit"]
        verbose_every = int(opts["verbose_every"])

        if not csv_path.exists():
            raise CommandError(f"CSV not found: {csv_path}")

        created = updated = skipped = 0
        rows_seen = 0

        with csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = set(reader.fieldnames or [])
            if not headers:
                raise CommandError("CSV has no header row.")

            missing = [col for col in COLUMN_MAP.values() if col and col not in headers]
            if missing:
                self.stdout.write(self.style.WARNING(f"Warning: missing CSV columns: {missing}"))

            for row in reader:
                rows_seen += 1
                if limit is not None and rows_seen > limit:
                    break

                data: Dict[str, Any] = {}
                for field, csv_col in COLUMN_MAP.items():
                    if not csv_col:
                        data[field] = None
                        continue
                    raw = row.get(csv_col, "")
                    raw = raw.strip() if isinstance(raw, str) else raw
                    if raw == "":
                        raw = None
                    if field in {"fee", "rating", "latitude", "longitude"}:
                        raw = _cast_float(raw)
                    data[field] = raw

                if not data.get("name"):
                    fn = (data.get("first_name") or "").strip()
                    ln = (data.get("last_name") or "").strip()
                    data["name"] = (fn + " " + ln).strip() or (data.get("organization") or "")

                if data.get("name") and not data.get("first_name") and not data.get("last_name"):
                    parts = data["name"].split()
                    if len(parts) >= 2:
                        data["first_name"] = parts[0]
                        data["last_name"] = " ".join(parts[1:])

                unique_value = data.get(unique_key)
                if not unique_value:
                    skipped += 1
                    continue

                if dry_run:
                    if rows_seen % verbose_every == 0:
                        self.stdout.write(f"[dry-run] processed {rows_seen} rows...")
                    continue

                obj, is_created = Contact.objects.update_or_create(
                    **{unique_key: unique_value},
                    defaults=data,
                )
                if is_created:
                    created += 1
                else:
                    updated += 1

                if rows_seen % verbose_every == 0:
                    self.stdout.write(f"Processed {rows_seen} rows...")

        self.stdout.write(self.style.SUCCESS(
            f"Done. rows_seen={rows_seen}, created={created}, updated={updated}, skipped={skipped}, dry_run={dry_run}"
        ))
