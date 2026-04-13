from django.core.management.base import BaseCommand
from properties.models import PropertyImage
from properties.ai_utils import image_analyzer


class Command(BaseCommand):
    help = 'Analyze existing property images for AI features'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Number of images to process per batch',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without making changes',
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        dry_run = options['dry_run']

        # Get images that haven't been analyzed yet
        images_to_analyze = PropertyImage.objects.filter(
            ai_detected_features__isnull=True
        ) | PropertyImage.objects.filter(
            ai_detected_features=[]
        )

        total_images = images_to_analyze.count()
        self.stdout.write(f'Found {total_images} images to analyze')

        if dry_run:
            self.stdout.write('Dry run mode - no changes will be made')
            return

        processed = 0
        for image in images_to_analyze.iterator():
            try:
                self.stdout.write(f'Analyzing image {image.id} for property {image.property.title}')
                analysis = image_analyzer.analyze_image(image.image.path)
                image.ai_detected_features = analysis.get('detected_features', [])
                image.ai_description = analysis.get('description', '')
                image.ai_visual_signature = analysis.get('visual_signature', {})
                image.save(update_fields=['ai_detected_features', 'ai_description', 'ai_visual_signature'])

                # Update property tags
                property_obj = image.property
                existing_tags = set(property_obj.ai_tags or [])
                existing_tags.update(image.ai_detected_features or [])
                if existing_tags:
                    property_obj.ai_tags = sorted(existing_tags)
                    property_obj.save(update_fields=['ai_tags'])

                processed += 1
                if processed % batch_size == 0:
                    self.stdout.write(f'Processed {processed}/{total_images} images')

            except Exception as e:
                self.stderr.write(f'Error analyzing image {image.id}: {str(e)}')

        self.stdout.write(f'Successfully analyzed {processed} images')