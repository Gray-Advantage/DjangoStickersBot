from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("bot", "0003_stable_ordering"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="sticker",
            name="bot_sticker_text_se_2c8bcc_gin",
        ),
        migrations.RemoveField(
            model_name="sticker",
            name="text_search_vector",
        ),
        migrations.AddField(
            model_name="sticker",
            name="text_search_vector",
            field=models.GeneratedField(
                db_persist=True,
                expression=django.contrib.postgres.search.SearchVector(
                    "text",
                    config="russian",
                ),
                null=True,
                output_field=django.contrib.postgres.search.SearchVectorField(),
            ),
        ),
        migrations.AddIndex(
            model_name="sticker",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["text_search_vector"],
                name="sticker_text_vector_gin",
            ),
        ),
        migrations.AlterField(
            model_name="stickerset",
            name="name",
            field=models.CharField(
                max_length=1024,
                unique=True,
                verbose_name="Имя стикер пака",
            ),
        ),
        migrations.AlterField(
            model_name="stickerset",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="sticker_sets",
                to="bot.telegramuser",
                verbose_name="Пользователь, добавивший этот стикер пак",
            ),
        ),
        migrations.AddIndex(
            model_name="sticker",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["text"],
                name="sticker_text_trigram",
                opclasses=["gin_trgm_ops"],
            ),
        ),
    ]
