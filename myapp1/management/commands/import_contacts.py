# myapp1/management/commands/import_contacts.py
import csv
from pathlib import Path
from typing import Dict, Any, Optional

from django.core.management.base import BaseCommand, CommandError
from myapp1.models import Contact


# Default mapping for a rich dataset like contacts_reco_400.csv
# Adjust the right-hand side values to match your CSV headers.
COLUMN_MAP: Dict[str, Optional[str]] = {
    # Identity / display
    "name": "name",
    "first_name": None,
    "last_name": None,
    "organization": "organization",

    # Contact
    "email": "email",
    "tel_number": "tel_number",
    "address": "address",

    # Location
    "city": "city",
    "state": None,
    "country": None,
    "postal_code": None,

    # Recommender fields
    "specialty": "specialty",
    "fee": "fee",
    "rating": "rating",
    "latitude": "lat",
    "longitude": "lng",

    # Legacy compatibility (kept if your model has it)
    "profession": None,  # if your CSV uses "profession" instead of "specialty", set to "profession"
}

# Choose the field used to upsert (must be in your model and usually unique in your CSV).
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
            default="myapp1/data/contacts_reco_400.csv",
            help="Path to CSV file (default: myapp1/data/contacts_reco_400.csv)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and validate but do not write to DB",
        )
        parser.add_argument(
            "--unique-key",
            type=str,
            default=UNIQUE_KEY_DEFAULT,
            help=f"Model field to use as unique key (default: {UNIQUE_KEY_DEFAULT})",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Import only the first N data rows (after header)",
        )
        parser.add_argument(
            "--verbose-every",
            type=int,
            default=200,
            help="Print progress every N rows (default: 200)",
        )

    def handle(self, *args, **opts):
        csv_path = Path(opts["file"])
        dry_run: bool = bool(opts["dry_run"])
        unique_key: str = str(opts["unique_key"])
        limit: Optional[int] = opts["limit"]
        verbose_every: int = int(opts["verbose_every"])

        if not csv_path.exists():
            raise CommandError(f"CSV not found: {csv_path}")

        # Basic validation
        if unique_key not in Contact._meta.fields_map and unique_key not in [f.name for f in Contact._meta.fields]:
            raise CommandError(f"Unique key '{unique_key}' is not a field on Contact.")

        created = updated = skipped = 0
        rows_seen = 0

        with csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = set(reader.fieldnames or [])
            if not headers:
                raise CommandError("CSV has no header row.")

            # Warn for mapped columns not present in the CSV
            missing = [col for col in COLUMN_MAP.values() if col and col not in headers]
            if missing:
                self.stdout.write(self.style.WARNING(f"Warning: missing CSV columns: {missing}"))
                self.stdout.write("Proceeding. Unmapped fields will import as NULL.")

            for row in reader:
                rows_seen += 1
                if limit is not None and rows_seen > limit:
                    break

                data: Dict[str, Any] = {}

                # Build model defaults dict from CSV row via COLUMN_MAP
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

                # Derive display name if missing
                if not data.get("name"):
                    fn = (data.get("first_name") or "").strip()
                    ln = (data.get("last_name") or "").strip()
                    data["name"] = (fn + " " + ln).strip() or (data.get("organization") or "")

                # If only "name" exists, split to first/last heuristically
                if data.get("name") and not data.get("first_name") and not data.get("last_name"):
                    parts = data["name"].split()
                    if len(parts) >= 2:
                        data["first_name"] = parts[0]
                        data["last_name"] = " ".join(parts[1:])

                # Ensure CharFields that your form relies on are not None if you prefer empty string
                # (Your model allows nulls, so None is fine. Keep as-is.)
                # Example to force empty strings:
                # for cf in ("name","address","profession","tel_number","email"):
                #     if data.get(cf) is None:
                #         data[cf] = ""

                unique_value = data.get(unique_key)
                if not unique_value:
                    skipped += 1
                    continue

                if dry_run:
                    # No DB writes
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
