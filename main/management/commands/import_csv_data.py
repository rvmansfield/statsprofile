import csv
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from main.models import MetricsHistory


class Command(BaseCommand):
    help = 'Import player metrics data from merge.csv file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='merge.csv',
            help='Path to the CSV file (default: merge.csv)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before importing'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        clear_existing = options['clear']
        
        # Construct full path to CSV file
        if not os.path.isabs(file_path):
            file_path = os.path.join(settings.BASE_DIR, file_path)
        
        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f'File not found: {file_path}')
            )
            return
        
        # Clear existing data if requested
        if clear_existing:
            MetricsHistory.objects.all().delete()
            self.stdout.write(
                self.style.WARNING('Cleared existing MetricsHistory data')
            )
        
        # Import data
        imported_count = 0
        skipped_count = 0
        
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                try:
                    # Parse date
                    event_date_str = row.get('events.date', '').strip()
                    if event_date_str:
                        try:
                            event_date = datetime.strptime(event_date_str, '%m/%d/%Y %H:%M')
                            event_date = timezone.make_aware(event_date)
                        except ValueError:
                            try:
                                event_date = datetime.strptime(event_date_str, '%m/%d/%Y')
                                event_date = timezone.make_aware(event_date)
                            except ValueError:
                                self.stdout.write(
                                    self.style.WARNING(f'Invalid date format: {event_date_str}')
                                )
                                skipped_count += 1
                                continue
                    else:
                        event_date = timezone.now()
                    
                    # Create MetricsHistory object
                    metrics_history = MetricsHistory(
                        height=self._parse_int(row.get('height')),
                        weight=self._parse_int(row.get('weight')),
                        ifVelo=self._parse_int(row.get('ifVelo')),
                        ofVelo=self._parse_int(row.get('ofVelo')),
                        cVelo=self._parse_int(row.get('cVelo')),
                        exitVelo=self._parse_int(row.get('exitVelo')),
                        maxFB=self._parse_int(row.get('maxFB')),
                        popTime=self._parse_decimal(row.get('popTime')),
                        sixtyyard=self._parse_decimal(row.get('sixtyyard')),
                        changeUp=self._parse_int(row.get('changeUp')),
                        curve=self._parse_int(row.get('curve')),
                        slider=self._parse_int(row.get('slider')),
                        event_id=self._parse_int(row.get('event_id')),
                        player_id=self._parse_int(row.get('player_id')),
                        gradYear=self._parse_int(row.get('players.gradYear')),
                        event_date=event_date,
                    )
                    
                    metrics_history.save()
                    imported_count += 1
                    
                    if imported_count % 100 == 0:
                        self.stdout.write(f'Imported {imported_count} records...')
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error importing row: {e}')
                    )
                    skipped_count += 1
                    continue
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully imported {imported_count} records. '
                f'Skipped {skipped_count} records.'
            )
        )
    
    def _parse_int(self, value):
        """Parse integer value, return None if empty or invalid"""
        if not value or value.strip() == '':
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None
    
    def _parse_decimal(self, value):
        """Parse decimal value, return None if empty or invalid"""
        if not value or value.strip() == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
