"""
Management command to generate SEO content for properties.
Usage:
    python manage.py generate_property_seo
    python manage.py generate_property_seo --property-id 5
    python manage.py generate_property_seo --limit 10
"""
from django.core.management.base import BaseCommand, CommandError
from properties.models import Property
from properties.ai_services import generate_comprehensive_seo_data


class Command(BaseCommand):
    help = 'Generate or regenerate AI-powered SEO content for properties'

    def add_arguments(self, parser):
        parser.add_argument(
            '--property-id',
            type=int,
            help='Generate SEO for a specific property ID'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit the number of properties to process'
        )
        parser.add_argument(
            '--regenerate',
            action='store_true',
            help='Regenerate even if description already exists'
        )

    def handle(self, *args, **options):
        property_id = options.get('property_id')
        limit = options.get('limit')
        regenerate = options.get('regenerate', False)

        # Get queryset of properties to process
        if property_id:
            qs = Property.objects.filter(pk=property_id)
            if not qs.exists():
                raise CommandError(f'Property with ID {property_id} not found')
        else:
            qs = Property.objects.all()
            if not regenerate:
                # Only process properties without AI descriptions
                qs = qs.filter(ai_generated_description__isnull=True) | qs.filter(ai_generated_description='')

        if limit:
            qs = qs[:limit]

        total = qs.count()
        self.stdout.write(f'Processing {total} properties...\n')

        success_count = 0
        error_count = 0
        skip_count = 0

        for idx, prop in enumerate(qs, 1):
            try:
                self.stdout.write(f'[{idx}/{total}] Processing: {prop.title}... ', ending='')

                # Generate comprehensive SEO data
                seo_data = generate_comprehensive_seo_data(prop)

                # Update the property
                prop.ai_generated_description = seo_data["ai_generated_description"]
                prop.seo_meta_description = seo_data["seo_meta_description"]
                prop.seo_keywords = seo_data["seo_keywords"]
                prop.seo_score = seo_data["seo_score"]
                prop.save(update_fields=[
                    'ai_generated_description',
                    'seo_meta_description',
                    'seo_keywords',
                    'seo_score'
                ])

                self.stdout.write(
                    self.style.SUCCESS(f'✓ (Score: {seo_data["seo_score"]})')
                )
                success_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error: {str(e)[:50]}')
                )
                error_count += 1

        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS(f'Success: {success_count}'))
        self.stdout.write(self.style.ERROR(f'Errors: {error_count}'))
        self.stdout.write(f'Total: {success_count + error_count}')
        self.stdout.write('=' * 60)
