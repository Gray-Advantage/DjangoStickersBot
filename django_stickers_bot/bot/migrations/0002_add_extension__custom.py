from django.db import migrations
from django.contrib.postgres.operations import (
    BtreeGinExtension,
    TrigramExtension,
)

class Migration(migrations.Migration):
    dependencies = [
        ("bot", "0001_initial"),
    ]

    operations = [
        BtreeGinExtension(),
        TrigramExtension(),
    ]
