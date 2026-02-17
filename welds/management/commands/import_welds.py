from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
import pandas as pd
from welds.models import Weld
from datetime import datetime


class Command(BaseCommand):
    help = 'Import weld data from an Excel file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the Excel file')

    def handle(self, *args, **options):
        file_path = options['file_path']

        try:
            df = pd.read_excel(file_path, header=0)
        except Exception as e:
            raise CommandError(f'Error reading Excel file: {e}')

        # Print column names for debugging
        self.stdout.write(f'Columns found: {list(df.columns)}')

        # Find MT column (contains "MT" in name)
        mt_column = None
        for col in df.columns:
            if 'MT' in str(col).upper():
                mt_column = col
                break

        created_count = 0
        updated_count = 0

        for _, row in df.iterrows():
            # Skip if section is blank
            section = row.get('Section')
            if pd.isna(section) or section == '':
                continue

            # Helper functions
            def to_int_or_default(val, default=0):
                try:
                    return int(float(val)) if pd.notna(val) else default
                except (ValueError, TypeError):
                    return default

            def to_float_or_none(val):
                try:
                    return float(val) if pd.notna(val) else None
                except (ValueError, TypeError):
                    return None

            def to_string(val):
                if pd.isna(val):
                    return ''
                return str(val).strip()

            def to_date(val):
                if pd.isna(val):
                    return None
                if isinstance(val, pd.Timestamp):
                    return val.date()
                if isinstance(val, datetime):
                    return val.date()
                if isinstance(val, str):
                    try:
                        return datetime.strptime(val, '%m/%d/%Y').date()
                    except ValueError:
                        try:
                            return datetime.strptime(val, '%Y-%m-%d').date()
                        except ValueError:
                            return None
                return None

            # Map and clean data
            weld_data = {
                'report': to_int_or_default(row.get('Report'), 0),
                'side': to_string(row.get('Side')),
                'section': to_string(section),
                'weld_id': to_string(row.get('Weld ID')),
                'weld_id2': to_string(row.get('Weld ID2')),
                'weld_id3': to_string(row.get('Weld ID3')),
                'weld_id4': to_string(row.get('Weld ID4')),
                'estimated_repair_length': to_float_or_none(row.get('Estimated Repair Length')),
                'total_weld_length': to_float_or_none(row.get('Total Weld Length')),
                'table_6_1_criteria_1': to_string(row.get('Table 6.1 AWS Visual Inspection Criteria 1')),
                'table_6_1_criteria_2': to_string(row.get('Table 6.1 AWS Visual Inspection Criteria 2')),
                'table_6_1_criteria_3': to_string(row.get('Table 6.1 AWS Visual Inspection Criteria 3')),
                'weld_type': to_string(row.get('Weld Type')),
                'weld_size': to_string(row.get('Weld Size')),
                'wps_number': to_string(row.get('WPS #')) or 'DWPS-SM-Special-B-3-N Rev 0',
                'inspection_utsw': to_string(row.get('Inspection UTSW')),
                'inspection_mt': to_string(row.get(mt_column)) if mt_column else '',
                'inspector': to_string(row.get('Inspector')),
                'date': to_date(row.get('Date')),
                'pass_fail': to_string(row.get('Pass_Fail')),
                'corrective_action_taken': to_string(row.get('Corrective Action Taken')),
                'repair_welder': to_string(row.get('Repair Welder')),
                'repair_inspection_date': to_date(row.get('Repair Inspection Date')),
                'weld_process': to_string(row.get('Weld Process')),
                'note': to_string(row.get('Note')),
            }

            # Use update_or_create
            weld, created = Weld.objects.update_or_create(
                section=weld_data['section'],
                weld_id4=weld_data['weld_id4'],
                defaults=weld_data
            )

            if created:
                self.stdout.write(f"Created: {weld_data['section']} - {weld_data['weld_id4']}")
                created_count += 1
            else:
                self.stdout.write(f"Updated: {weld_data['section']} - {weld_data['weld_id4']}")
                updated_count += 1

        total = created_count + updated_count
        self.stdout.write(self.style.SUCCESS(f'Total: {total} (Created: {created_count}, Updated: {updated_count})'))