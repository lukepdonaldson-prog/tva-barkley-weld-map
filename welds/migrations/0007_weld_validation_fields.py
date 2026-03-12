from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('welds', '0006_seed_weldidkey_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='weld',
            name='validation_note',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='weld',
            name='validation_cleared',
            field=models.BooleanField(default=False),
        ),
    ]
