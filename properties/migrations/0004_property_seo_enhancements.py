# Generated manually for SEO enhancements

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0003_userprofile_usersearch_userview'),
    ]

    operations = [
        migrations.AddField(
            model_name='property',
            name='seo_keywords',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='property',
            name='seo_score',
            field=models.PositiveIntegerField(blank=True, default=0),
        ),
    ]
