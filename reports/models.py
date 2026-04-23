from django.db import models

REPORT_TYPE_CHOICES = [
    ('UT', 'UT — Ultrasonic Testing'),
    ('MT', 'MT — Magnetic Particle Testing'),
    ('PT', 'PT — Penetrant Testing'),
    ('VT', 'VT — Visual Testing'),
    ('RT', 'RT — Radiographic Testing'),
    ('Other', 'Other'),
]


class NDEReport(models.Model):
    title = models.CharField(max_length=300)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES, default='UT', db_index=True)
    section = models.CharField(max_length=100, blank=True, db_index=True, help_text='e.g. AX, CX, BX')
    report_file = models.FileField(upload_to='nde_reports/', max_length=500)
    notes = models.TextField(blank=True, help_text='Optional notes, keywords, or summary for searching')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.title
