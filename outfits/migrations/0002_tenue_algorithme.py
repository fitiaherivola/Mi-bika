from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('outfits', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='tenue',
            name='algorithme',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Algorithme ayant généré la tenue (baseline, optimise, dijkstra, …)',
                max_length=32,
            ),
        ),
    ]
