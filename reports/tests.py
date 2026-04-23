import os
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import NDEReport


TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class NDEReportTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        if TEMP_MEDIA_ROOT and os.path.isdir(TEMP_MEDIA_ROOT):
            shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='pass12345')

    def test_report_list_requires_login(self):
        response = self.client.get(reverse('report_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_report_upload_creates_record_and_sets_uploaded_by(self):
        self.client.login(username='tester', password='pass12345')
        pdf_file = SimpleUploadedFile(
            'sample.pdf',
            b'%PDF-1.4\n%minimal\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF',
            content_type='application/pdf',
        )

        response = self.client.post(reverse('report_upload'), {
            'title': 'UT Report AX-1',
            'report_type': 'UT',
            'section': 'AX',
            'report_file': pdf_file,
            'notes': 'keyword',
        })

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('report_list'))
        report = NDEReport.objects.get(title='UT Report AX-1')
        self.assertEqual(report.uploaded_by, 'tester')

    def test_report_list_search_filters_notes(self):
        NDEReport.objects.create(
            title='MT Report',
            report_type='MT',
            section='AX',
            report_file=SimpleUploadedFile('mt.pdf', b'%PDF-1.4\n%%EOF', content_type='application/pdf'),
            notes='contains crack indicator',
            uploaded_by='tester',
        )
        self.client.login(username='tester', password='pass12345')

        response = self.client.get(reverse('report_list'), {'search': 'crack'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'MT Report')
