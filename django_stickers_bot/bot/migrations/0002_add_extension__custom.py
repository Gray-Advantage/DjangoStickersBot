from django.contrib.postgres.operations import (
    BtreeGinExtension,
    TrigramExtension,
)
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("bot", "0001_initial"),
    ]

    operations = [
        BtreeGinExtension(),
        TrigramExtension(),
    ]
