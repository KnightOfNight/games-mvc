from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shyship', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='shyshipgame',
            name='winner',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
