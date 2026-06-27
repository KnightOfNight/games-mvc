import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shyland', '0014_seed_origins_archetypes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='character',
            name='origin',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='characters',
                to='shyland.origin',
            ),
        ),
        migrations.AlterField(
            model_name='character',
            name='archetype',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='characters',
                to='shyland.archetype',
            ),
        ),
    ]
