from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectProgressSnapshot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('snapshot_date', models.DateField(default=django.utils.timezone.now)),
                ('progress_percent', models.DecimalField(decimal_places=2, max_digits=6)),
                ('spi', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ('cpi', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='progress_snapshots', to='projects.project')),
            ],
            options={'ordering': ['-snapshot_date']},
        ),
        migrations.AlterUniqueTogether(
            name='projectprogresssnapshot',
            unique_together={('project', 'snapshot_date')},
        ),
    ]






