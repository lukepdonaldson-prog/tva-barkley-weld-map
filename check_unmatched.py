import os
import sys
import csv
import django

sys.path.insert(0, r'C:\Users\lukep\OneDrive\Desktop\TVA Database\tva-barkley-weld-map')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weldmap.settings')
django.setup()
from welds.models import Weld

csv_path = r'C:\Users\lukep\OneDrive\Desktop\TVA Database\TVA Pictures\unmatched_photos.csv'

with open(csv_path, encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

no_section = 0
section_not_in_db = 0
code_mismatch = 0
code_mismatch_examples = []

for r in rows:
    if 'No section found' in r['reason']:
        no_section += 1
    elif r['section']:
        welds = Weld.objects.filter(section__iexact=r['section'])
        if not welds.exists():
            section_not_in_db += 1
        else:
            code_mismatch += 1
            if len(code_mismatch_examples) < 30:
                db_codes = sorted(set(welds.values_list('weld_id4', flat=True)))
                code_mismatch_examples.append(
                    f"  {r['section']:>12} | Tried: {r['codes']:>20} | DB: {db_codes}"
                )

print(f"Total unmatched: {len(rows)}")
print(f"  No section in filename:   {no_section}  (BEAM/MISC — later phase)")
print(f"  Section not in DB:        {section_not_in_db}  (can't fix)")
print(f"  Code mismatch:            {code_mismatch}  (photo code ≠ any DB code)")
print()
print(f"  FIXABLE TOTAL:            ~{code_mismatch} (if we keep tuning)")
print(f"  UNFIXABLE:                ~{no_section + section_not_in_db}")
print()
print("REMAINING CODE MISMATCHES (unique, first 30):")
print("=" * 130)
for ex in code_mismatch_examples:
    print(ex)