import json
from datetime import date

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
