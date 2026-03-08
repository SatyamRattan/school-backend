# Generated manually
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0001_initial'),
        ('management', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='classroom',
            name='school',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='classrooms', to='management.school'),
        ),
        migrations.AddField(
            model_name='subject',
            name='school',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subjects', to='management.school'),
        ),
        migrations.AddField(
            model_name='timetable',
            name='school',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='timetables', to='management.school'),
        ),
    ]
