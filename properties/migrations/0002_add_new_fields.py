"""
Migration for properties app - add new models and fields
"""
from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('properties', '0001_initial'),
    ]

    operations = [
        # Add new fields to Property model
        migrations.AddField(
            model_name='property',
            name='state',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='property',
            name='latitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='property',
            name='longitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='property',
            name='pincode',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='property',
            name='bedrooms',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='property',
            name='bathrooms',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='property',
            name='area_sqft',
            field=models.PositiveIntegerField(blank=True, help_text='Area in sq ft', null=True),
        ),
        migrations.AddField(
            model_name='property',
            name='furnishing',
            field=models.CharField(choices=[('unfurnished', 'Unfurnished'), ('semi-furnished', 'Semi-Furnished'), ('furnished', 'Furnished')], default='unfurnished', max_length=20),
        ),
        migrations.AddField(
            model_name='property',
            name='status',
            field=models.CharField(choices=[('available', 'Available'), ('sold', 'Sold'), ('rented', 'Rented')], default='available', max_length=20),
        ),
        migrations.AddField(
            model_name='property',
            name='rating',
            field=models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(5)]),
        ),
        migrations.AddField(
            model_name='property',
            name='total_reviews',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='property',
            name='amenities',
            field=models.JSONField(blank=True, default=list, help_text='List of amenities: parking, pool, gym, etc'),
        ),
        migrations.AddField(
            model_name='property',
            name='ai_generated_description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='property',
            name='ai_tags',
            field=models.JSONField(blank=True, default=list, help_text='AI-generated tags for search'),
        ),
        migrations.AddField(
            model_name='property',
            name='is_promoted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='property',
            name='promotion_until',
            field=models.DateTimeField(blank=True, null=True),
        ),
        # Update nearby location fields to JSON
        migrations.AlterField(
            model_name='property',
            name='nearby_hospital',
            field=models.JSONField(blank=True, default=list, help_text='List of nearby hospitals with distance'),
        ),
        migrations.AlterField(
            model_name='property',
            name='nearby_railway_station',
            field=models.JSONField(blank=True, default=list, help_text='List of nearby railway stations'),
        ),
        migrations.AlterField(
            model_name='property',
            name='nearby_shopping_mall',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AlterField(
            model_name='property',
            name='nearby_bus_stand',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AlterField(
            model_name='property',
            name='nearby_school',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AlterField(
            model_name='property',
            name='nearby_airport',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AlterField(
            model_name='property',
            name='nearby_park',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AlterField(
            model_name='property',
            name='nearby_supermarket',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AlterField(
            model_name='property',
            name='nearby_restaurant',
            field=models.JSONField(blank=True, default=list),
        ),
        # Add new nearby location fields
        migrations.AddField(
            model_name='property',
            name='nearby_gym',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='property',
            name='nearby_hospital_emergency',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='property',
            name='nearby_bank',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='property',
            name='nearby_atm',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='property',
            name='nearby_pharmacy',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='property',
            name='nearby_metro',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='property',
            name='nearby_university',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='property',
            name='nearby_theater',
            field=models.JSONField(blank=True, default=list),
        ),
        # Add more property types
        migrations.AlterField(
            model_name='property',
            name='property_type',
            field=models.CharField(
                choices=[
                    ('apartment', 'Apartment'),
                    ('house', 'House'),
                    ('villa', 'Villa'),
                    ('plot', 'Plot'),
                    ('commercial', 'Commercial'),
                    ('office', 'Office'),
                    ('shop', 'Shop'),
                    ('farmland', 'Farmland'),
                ],
                db_index=True,
                max_length=20
            ),
        ),
        # Update PropertyImage model
        migrations.AddField(
            model_name='propertyimage',
            name='alt_text',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='propertyimage',
            name='ai_detected_features',
            field=models.JSONField(blank=True, default=list, help_text='Features detected by AI'),
        ),
        migrations.AddField(
            model_name='propertyimage',
            name='ai_description',
            field=models.TextField(blank=True, null=True, help_text='AI-generated image description'),
        ),
        # Create PropertyReview model
        migrations.CreateModel(
            name='PropertyReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('title', models.CharField(blank=True, max_length=100)),
                ('comment', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('property', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='properties.property')),
                ('reviewer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        # Create PropertyComparison model
        migrations.CreateModel(
            name='PropertyComparison',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('properties', models.ManyToManyField(to='properties.property')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='property_comparisons', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        # Add unique constraint to PropertyReview
        migrations.AlterUniqueTogether(
            name='propertyreview',
            unique_together={('property', 'reviewer')},
        ),
    ]
