from django.core.management.base import BaseCommand
from properties.models import Property
from properties.location_utils import OpenStreetMapAPI
import time
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Geocode properties that don\'t have latitude/longitude coordinates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Re-geocode properties that already have coordinates',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']

        # Get properties to geocode
        if force:
            properties = Property.objects.all()
        else:
            properties = Property.objects.filter(latitude__isnull=True, longitude__isnull=True)

        if not properties:
            self.stdout.write(self.style.SUCCESS('No properties need geocoding.'))
            return

        self.stdout.write(f'Found {properties.count()} properties to geocode.')

        api = OpenStreetMapAPI()
        success_count = 0
        error_count = 0

        for property in properties:
            try:
                # Try full address first, then fall back to city/state
                full_address = ", ".join([property.address, property.city, property.state]).strip(', ')
                
                self.stdout.write(f'Geocoding: {property.title[:50]}...')
                
                # Try full address first
                lat, lng = api.get_coordinates(
                    address=property.address,
                    city=property.city,
                    state=property.state
                )
                
                # If that fails, try just city and state
                if not lat or not lng:
                    self.stdout.write('  Full address failed, trying city/state...')
                    lat, lng = api.get_coordinates(
                        address="",
                        city=property.city,
                        state=property.state
                    )
                
                # If that still fails, try just city
                if not lat or not lng and property.city:
                    self.stdout.write('  City/state failed, trying just city...')
                    lat, lng = api.get_coordinates(
                        address=property.city,
                        city="",
                        state=""
                    )

                if lat and lng:
                    if dry_run:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  Would set coordinates: {lat}, {lng} for "{property.title}"'
                            )
                        )
                    else:
                        property.latitude = lat
                        property.longitude = lng
                        property.save(update_fields=['latitude', 'longitude'])
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  Set coordinates: {lat}, {lng} for "{property.title}"'
                            )
                        )
                    success_count += 1
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f'  Failed to geocode: {full_address}'
                        )
                    )
                    error_count += 1

                # Rate limiting - be nice to the API
                time.sleep(1)

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'  Error geocoding property {property.id}: {str(e)}'
                    )
                )
                error_count += 1

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Dry run complete. Would geocode {success_count} properties, {error_count} errors.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Geocoding complete. Successfully geocoded {success_count} properties, {error_count} errors.'
                )
            )