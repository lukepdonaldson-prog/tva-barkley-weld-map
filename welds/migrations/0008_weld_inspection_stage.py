from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('welds', '0007_weld_validation_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='weld',
            name='inspection_stage',
            field=models.CharField(
                blank=True,
                choices=[
                    ('Initial Inspection', 'Initial Inspection'),
                    ('Prior To Welding', 'Prior To Welding'),
                    ('Finished Weld', 'Finished Weld'),
                    (
                        'Provided support was not clear enough for the aspects missing',
                        'Provided support was not clear enough for the aspects missing',
                    ),
                    ('N/A', 'N/A'),
                ],
                default='',
                max_length=100,
            ),
        ),
        migrations.AlterUniqueTogether(
            name='weld',
            unique_together=set(),
        ),
    ]
