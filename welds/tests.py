import json
from io import BytesIO
from datetime import date

import openpyxl
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from reports.models import NDEReport
from welds.models import Weld, WeldPhoto


class DashboardViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='dashboard-user',
            password='secret123',
        )

    def _create_weld(self, **overrides):
        defaults = {
            'report': 1,
            'side': 'N',
            'section': 'AX',
            'weld_id': 'W-1',
            'weld_id4': 'AX-1',
            'inspector': 'Inspector',
            'date': date(2026, 1, 1),
            'pass_fail': 'Pass',
            'weld_type': 'Fillet',
            'total_weld_length': 10.0,
        }
        defaults.update(overrides)
        return Weld.objects.create(**defaults)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_root_redirects_to_dashboard(self):
        self.client.force_login(self.user)
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/welds/dashboard/')

    def test_dashboard_context_stats(self):
        self._create_weld(section='AX', weld_id='W-1', weld_id4='AX-1', pass_fail='Pass')
        self._create_weld(section='AX', weld_id='W-2', weld_id4='AX-2', pass_fail='Fail')
        self._create_weld(
            section='BX',
            weld_id='W-3',
            weld_id4='BX-1',
            pass_fail='',
            inspector='Inspector',
            date=date(2026, 1, 2),
            weld_type='Groove',
            total_weld_length=8.0,
        )

        NDEReport.objects.create(
            title='Report 1',
            report_type='MT',
            section='AX',
            report_file=SimpleUploadedFile('report.pdf', b'%PDF-1.4 test', content_type='application/pdf'),
        )
        WeldPhoto.objects.create(
            photo=SimpleUploadedFile('photo.jpg', b'photo-bytes', content_type='image/jpeg'),
            section='AX',
            report_number='1',
            original_filename='photo.jpg',
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'welds/dashboard.html')
        self.assertEqual(response.context['total_welds'], 3)
        self.assertEqual(response.context['pass_count'], 1)
        self.assertEqual(response.context['fail_count'], 1)
        self.assertEqual(response.context['incomplete_count'], 1)
        self.assertEqual(response.context['not_inspected'], 1)
        self.assertEqual(response.context['pass_rate'], 50.0)
        self.assertEqual(response.context['total_photos'], 1)
        self.assertEqual(response.context['total_reports'], 1)

        donut_data = json.loads(response.context['donut_data_json'])
        self.assertEqual(donut_data, {'pass': 1, 'fail': 1, 'not_inspected': 1})


class ImportWeldsExcelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='import-user',
            password='secret123',
        )

    def _build_excel_file(self, rows):
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        headers = [
            'Report',
            'Side',
            'Section',
            'Weld ID',
            'Weld ID2',
            'Weld ID3',
            'Weld ID4',
            'Total Weld Length',
            'Weld Type',
            'Inspector',
            'Date',
            'Pass_Fail',
            'Note',
            'Inspection Stage',
        ]
        worksheet.append(headers)
        for row in rows:
            worksheet.append(row)

        content = BytesIO()
        workbook.save(content)
        content.seek(0)
        return SimpleUploadedFile(
            'welds.xlsx',
            content.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

    def test_import_creates_duplicate_welds_and_tracks_inspection_stage(self):
        self.client.force_login(self.user)
        WeldPhoto.objects.create(
            photo=SimpleUploadedFile('photo.jpg', b'photo-bytes', content_type='image/jpeg'),
            section='BX-1.3',
            report_number='29',
            original_filename='photo.jpg',
        )

        excel_file = self._build_excel_file([
            [29, 'N', 'BX-1.3', 'W-1', '', '', 'FP', 12, 'Fillet', 'Inspector A', '01/02/2026', 'Fail', 'Needs repair', 'Initial Inspection'],
            [29, 'N', 'BX-1.3', 'W-1', '', '', 'FP', 12, 'Fillet', 'Inspector A', '01/03/2026', 'Pass', 'Ready for repair', 'Prior To Welding'],
            [29, 'N', 'BX-1.4', 'W-2', '', '', 'FD', 8, 'Fillet', 'Inspector B', '01/04/2026', 'Pass', 'Completed', 'Finished Weld'],
            [29, 'N', 'BX-1.5', 'W-3', '', '', 'CD', 7, 'Fillet', 'Inspector C', '01/05/2026', 'Pass', 'Support unclear', 'Provided support was not clear enough for the aspects missing'],
            [29, 'N', 'BX-1.6', 'W-4', '', '', 'LU', 6, 'Fillet', 'Inspector D', '01/06/2026', 'Pass', 'No repair needed', 'N/A'],
        ])

        response = self.client.post(
            reverse('import_welds_excel'),
            {'file': excel_file, 'mode': 'update_add'},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['status'], 'ok')
        self.assertEqual(payload['created'], 5)
        self.assertEqual(payload['deleted'], 0)
        self.assertEqual(payload['skipped'], 0)
        self.assertEqual(payload['errors'], [])
        self.assertEqual(payload['warnings'], [])
        self.assertNotIn('updated', payload)

        self.assertEqual(Weld.objects.filter(section='BX-1.3', weld_id4='FP').count(), 2)
        self.assertEqual(
            set(Weld.objects.values_list('inspection_stage', flat=True)),
            {
                'Initial Inspection',
                'Prior To Welding',
                'Finished Weld',
                'Provided support was not clear enough for the aspects missing',
                'N/A',
            },
        )
        self.assertEqual(WeldPhoto.objects.count(), 1)

    def test_import_converts_float_like_report_values_without_warning(self):
        self.client.force_login(self.user)

        excel_file = self._build_excel_file([
            ['11.0', 'N', 'BX-2.1', 11.0, 12.0, 13.0, 'FP', 12, 'Fillet', 'Inspector A', '01/02/2026', 'Pass', '', 'Initial Inspection'],
        ])

        response = self.client.post(
            reverse('import_welds_excel'),
            {'file': excel_file, 'mode': 'update_add'},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['errors'], [])
        self.assertEqual(payload['warnings'], [])
        weld = Weld.objects.get(section='BX-2.1')
        self.assertEqual(weld.report, 11)
        self.assertEqual(weld.weld_id, '11')
        self.assertEqual(weld.weld_id2, '12')
        self.assertEqual(weld.weld_id3, '13')

    def test_import_defaults_blank_report_to_zero_without_warning(self):
        self.client.force_login(self.user)

        excel_file = self._build_excel_file([
            ['', 'N', 'BX-2.2', 'W-6', '', '', 'FD', 10, 'Fillet', 'Inspector B', '01/03/2026', 'Pass', '', 'Initial Inspection'],
        ])

        response = self.client.post(
            reverse('import_welds_excel'),
            {'file': excel_file, 'mode': 'update_add'},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['errors'], [])
        self.assertEqual(payload['warnings'], [])
        self.assertEqual(Weld.objects.get(section='BX-2.2').report, 0)

    def test_import_warns_when_report_value_cannot_be_converted(self):
        self.client.force_login(self.user)

        excel_file = self._build_excel_file([
            ['not-a-number', 'N', 'BX-2.3', 'W-7', '', '', 'CD', 9, 'Fillet', 'Inspector C', '01/04/2026', 'Fail', '', 'Initial Inspection'],
        ])

        response = self.client.post(
            reverse('import_welds_excel'),
            {'file': excel_file, 'mode': 'update_add'},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['errors'], [])
        self.assertEqual(
            payload['warnings'],
            ['⚠️ Row 2: Could not convert Report value \'not-a-number\' to integer (Original value: "not-a-number", Section: BX-2.3)'],
        )
        self.assertEqual(Weld.objects.get(section='BX-2.3').report, 0)


class WeldDetailNavigationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='nav-user',
            password='secret123',
        )
        self.client.force_login(self.user)

    def _create_weld(self, **overrides):
        defaults = {
            'report': 1,
            'side': 'N',
            'section': 'AX',
            'weld_id': 'W-1',
            'weld_id4': 'AX-1',
            'inspector': 'Inspector',
            'date': date(2026, 1, 1),
            'pass_fail': 'Pass',
            'weld_type': 'Fillet',
            'total_weld_length': 10.0,
        }
        defaults.update(overrides)
        return Weld.objects.create(**defaults)

    def test_filtered_navigation_uses_session_ids(self):
        first = self._create_weld(section='BX-10', weld_id='W-1', weld_id4='BX-10-1')
        self._create_weld(section='AX-1', weld_id='W-2', weld_id4='AX-1-2')
        last = self._create_weld(section='BX-10', weld_id='W-3', weld_id4='BX-10-3')

        self.client.get(reverse('weld_list'), {'section': 'BX-10'})
        self.assertEqual(
            self.client.session.get('filtered_weld_ids'),
            [first.id, last.id],
        )

        response = self.client.get(reverse('weld_detail', args=[first.id]))
        self.assertIsNone(response.context['prev_weld_id'])
        self.assertEqual(response.context['next_weld_id'], last.id)

        response = self.client.get(reverse('weld_detail', args=[last.id]))
        self.assertEqual(response.context['prev_weld_id'], first.id)
        self.assertIsNone(response.context['next_weld_id'])

    def test_weld_list_without_filters_clears_filtered_navigation_session(self):
        first = self._create_weld(section='BX-10', weld_id='W-1', weld_id4='BX-10-1')
        self._create_weld(section='AX-1', weld_id='W-2', weld_id4='AX-1-2')
        last = self._create_weld(section='BX-10', weld_id='W-3', weld_id4='BX-10-3')

        self.client.get(reverse('weld_list'), {'section': 'BX-10'})
        self.assertEqual(self.client.session.get('filtered_weld_ids'), [first.id, last.id])

        self.client.get(reverse('weld_list'))
        self.assertNotIn('filtered_weld_ids', self.client.session)

    def test_navigation_falls_back_when_weld_not_in_filtered_session(self):
        first = self._create_weld(section='AX-1', weld_id='W-1', weld_id4='AX-1-1')
        middle = self._create_weld(section='AX-2', weld_id='W-2', weld_id4='AX-2-2')
        last = self._create_weld(section='AX-3', weld_id='W-3', weld_id4='AX-3-3')

        session = self.client.session
        session['filtered_weld_ids'] = [first.id, last.id]
        session.save()

        response = self.client.get(reverse('weld_detail', args=[middle.id]))
        self.assertEqual(response.context['prev_weld_id'], first.id)
        self.assertEqual(response.context['next_weld_id'], last.id)
