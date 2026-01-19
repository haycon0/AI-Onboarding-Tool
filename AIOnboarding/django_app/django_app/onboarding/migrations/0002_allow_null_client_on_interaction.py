"""Allow NULL for Interaction.client field.

Generated migration to alter the `client` foreign key on `Interaction` to
allow null values (null=True, blank=True) so database rows may have no
associated client.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("onboarding", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="interaction",
            name="client",
            field=models.ForeignKey(
                to="onboarding.client",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="interactions",
                null=True,
                blank=True,
            ),
        ),
    ]
