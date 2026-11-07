from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0003_alter_notification_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='evenement',
            name='type_evt',
            field=models.CharField(
                choices=[
                    ('MARIAGE', 'Mariage'),
                    ('SOIREE', 'Soirée'),
                    ('PROFESSIONNEL', 'Professionnel'),
                    ('SPORT', 'Sport'),
                    ('TRADITIONNEL', 'Traditionnel / cérémonie'),
                    ('CASUAL', 'Décontracté'),
                    ('AUTRE', 'Autre'),
                ],
                db_column='type_evt',
                default='AUTRE',
                max_length=20,
            ),
        ),
    ]
