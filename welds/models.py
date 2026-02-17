from django.db import models


class Weld(models.Model):
    """Model representing a weld inspection record."""
    report = models.IntegerField()
    side = models.CharField(max_length=50)
    section = models.CharField(max_length=100, db_index=True)
    weld_id = models.CharField(max_length=50)
    weld_id2 = models.CharField(max_length=50, blank=True)
    weld_id3 = models.CharField(max_length=50, blank=True)
    weld_id4 = models.CharField(max_length=50, blank=True)
    estimated_repair_length = models.FloatField(null=True, blank=True)
    total_weld_length = models.FloatField(null=True, blank=True)
    table_6_1_criteria_1 = models.CharField(max_length=200, blank=True)
    table_6_1_criteria_2 = models.CharField(max_length=200, blank=True)
    table_6_1_criteria_3 = models.CharField(max_length=200, blank=True)
    weld_type = models.CharField(max_length=100, blank=True)
    weld_size = models.CharField(max_length=50, blank=True, default='')
    wps_number = models.CharField(max_length=100, default='DWPS-SM-Special-B-3-N Rev 0')
    inspection_utsw = models.CharField(max_length=50, blank=True)
    inspection_mt = models.CharField(max_length=50, blank=True)
    inspector = models.CharField(max_length=200, blank=True)
    date = models.DateField(null=True, blank=True)
    pass_fail = models.CharField(max_length=20, blank=True)
    corrective_action_taken = models.CharField(max_length=20, blank=True)
    repair_welder = models.CharField(max_length=200, blank=True)
    repair_inspection_date = models.DateField(null=True, blank=True)
    weld_process = models.CharField(max_length=100, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['section', 'weld_id4']

    def __str__(self):
        return f"{self.section} - {self.weld_id4}"


class WeldPhoto(models.Model):
    """Model representing photos associated with weld inspections."""
    weld = models.ForeignKey(Weld, on_delete=models.CASCADE, related_name='photos')
    photo = models.ImageField(upload_to='weld_photos/%Y/%m/%d/')
    report_number = models.IntegerField()
    caption = models.CharField(max_length=500, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        import os
        filename = os.path.basename(self.photo.name) if self.photo else 'no-photo'
        return f"{self.weld.section} - {filename}"
