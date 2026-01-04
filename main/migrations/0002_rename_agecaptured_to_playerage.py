from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='playermetric',
            old_name='ageCaptured',
            new_name='playerAge',
        ),
    ]
