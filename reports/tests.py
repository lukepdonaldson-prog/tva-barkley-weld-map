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

    def test_report_list_hides_uploaded_columns(self):
        NDEReport.objects.create(
            title='UT Report AX',
            report_type='UT',
            section='AX',
            report_file=SimpleUploadedFile('ut.pdf', b'%PDF-1.4\n%%EOF', content_type='application/pdf'),
            notes='sample',
            uploaded_by='tester',
        )
        self.client.login(username='tester', password='pass12345')

        response = self.client.get(reverse('report_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<th>Title</th>', html=False)
        self.assertContains(response, '<th>Type</th>', html=False)
        self.assertContains(response, '<th>Section</th>', html=False)
        self.assertContains(response, '<th>Actions</th>', html=False)
        self.assertNotContains(response, '<th>Uploaded</th>', html=False)
        self.assertNotContains(response, '<th>Uploaded By</th>', html=False)

    def test_report_view_uses_object_and_hides_uploaded_metadata(self):
        report = NDEReport.objects.create(
            title='MT Report View',
            report_type='MT',
            section='AX',
            report_file=SimpleUploadedFile('mt-view.pdf', b'%PDF-1.4\n%%EOF', content_type='application/pdf'),
            notes='viewer test',
            uploaded_by='tester',
        )
        self.client.login(username='tester', password='pass12345')

        response = self.client.get(reverse('report_view', args=[report.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Open PDF in New Tab')
        self.assertContains(response, 'Download PDF')
        self.assertContains(response, '<object data="', html=False)
        self.assertNotContains(response, '<iframe', html=False)
        self.assertNotContains(response, '<strong>Uploaded:</strong>', html=False)
        self.assertNotContains(response, '<strong>Uploaded by:</strong>', html=False)

    def test_report_upload_includes_drag_drop_and_title_autofill_script(self):
        self.client.login(username='tester', password='pass12345')
        response = self.client.get(reverse('report_upload'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="pdf-drop-zone"', html=False)
        self.assertContains(response, 'Drag &amp; drop your PDF here')
        self.assertContains(response, 'or click to browse')
        self.assertContains(response, 'function setTitleFromFile(file)')
        self.assertContains(response, "titleInput.dataset.autoFilled = 'true';")
