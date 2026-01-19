"""Allow NULL for Interaction.department field.

Generated migration to alter the `department` foreign key on `Interaction`
to allow null values (null=True, blank=True) so database rows may have no
associated department.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("onboarding", "0002_allow_null_client_on_interaction"),
    ]

    operations = [
        migrations.AlterField(
            model_name="interaction",
            name="department",
            field=models.ForeignKey(
                to="onboarding.department",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="interactions",
                null=True,
                blank=True,
            ),
        ),
    ]
