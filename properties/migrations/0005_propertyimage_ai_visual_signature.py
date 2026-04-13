from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("properties", "0004_property_nearby_other_places"),
    ]

    operations = [
        migrations.AddField(
            model_name="propertyimage",
            name="ai_visual_signature",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text="Compact visual signature used for image similarity search",
            ),
        ),
    ]
