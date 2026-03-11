import os
import re
from django.core.management.base import BaseCommand
from django.core.files import File
from welds.models import WeldPhoto


def shorten_filename(filename):
    """Shorten long filenames to avoid Django's max_length issues."""
    name, ext = os.path.splitext(filename)
    if len(name) > 80:
        name = name[:80]
    return name + ext


def normalize_section(section):
    fixed = re.sub(r'^([A-Za-z]+)(\d)', r'\1-\2', section)
    return fixed.upper()


def extract_section_from_filename(filename):
    """Try to pull a section like AX-6.3 from the start of the filename."""
    name = os.path.splitext(filename)[0]
    # Strip leading numbers (e.g., "01 AX-6.3 ...")
    name = re.sub(r'^\d+\s+', '', name)

    match = re.match(
        r'^([A-Za-z]{1,3}[-.]?\d+(?:\.\d+)?(?:\([A-Za-z0-9]+\))?)\s*(.*)',
        name
    )
    if match:
        section = normalize_section(match.group(1))
        description = match.group(2).strip()
        return section, description

    return '', name


class Command(BaseCommand):
    help = 'Import weld photos into the photo library'

    def add_arguments(self, parser):
        parser.add_argument(
            'photos_dir', type=str,
            help='Root path to TVA Pictures folder'
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview without importing'
        )

    def handle(self, *args, **options):
        photos_dir = options['photos_dir']
        dry_run = options['dry_run']

        if not os.path.exists(photos_dir):
            self.stderr.write(f"ERROR: Directory not found: {photos_dir}")
            return

        imported = 0
        skipped = 0

        for root, dirs, files in os.walk(photos_dir):
            for filename in files:
                if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    continue

                filepath = os.path.join(root, filename)

                # Get path parts relative to photos_dir
                rel_path = os.path.relpath(root, photos_dir)
                path_parts = rel_path.replace('\\', '/').split('/')

                # Extract report number from path (first folder that's a number)
                report_number = ''
                for part in path_parts:
                    if re.match(r'^\d+[A-Za-z]?$', part):
                        report_number = part
                        break

                # Extract subfolder (the folder directly containing the file)
                # e.g., "AX-6" or "BEAM L102B" or "MISC"
                subfolder = path_parts[-1] if len(path_parts) > 1 else ''

                # Try to get section from filename first, then from subfolder
                section, description = extract_section_from_filename(filename)

                if not section and subfolder:
                    # Try to extract section from subfolder name
                    match = re.match(r'^([A-Za-z]{1,3}[-.]?\d+(?:\.\d+)?)', subfolder)
                    if match:
                        section = normalize_section(match.group(1))

                if not dry_run:
                    with open(filepath, 'rb') as f:
                        photo = WeldPhoto(
                            section=section,
                            report_number=report_number,
                            subfolder=subfolder,
                            description=description,
                            original_filename=filename,
                        )
                        photo.photo.save(shorten_filename(filename), File(f), save=True)

                imported += 1

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(f"  PHOTO IMPORT SUMMARY {'(DRY RUN)' if dry_run else ''}")
        self.stdout.write("=" * 60)
        self.stdout.write(f"  Photos imported:     {imported}")
        self.stdout.write(f"  Total files:         {imported}")
        self.stdout.write("=" * 60)