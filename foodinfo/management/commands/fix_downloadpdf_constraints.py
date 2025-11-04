"""
Management command to fix DownloadPDF foreign key constraints
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from foodinfo.models import DownloadPDF, DownloadRequest


class Command(BaseCommand):
    help = 'Fix DownloadPDF foreign key constraints'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        with transaction.atomic():
            # Get all DownloadRequest IDs that exist
            valid_download_request_ids = set(DownloadRequest.objects.values_list('id', flat=True))
            
            # Find orphaned DownloadPDF records
            orphaned_pdfs = []
            invalid_foreign_keys = []
            
            for pdf in DownloadPDF.objects.all():
                if pdf.download_requested_id:
                    if pdf.download_requested_id not in valid_download_request_ids:
                        orphaned_pdfs.append(pdf)
                        invalid_foreign_keys.append(pdf.download_requested_id)
            
            self.stdout.write(f"Found {len(orphaned_pdfs)} orphaned DownloadPDF records")
            self.stdout.write(f"Invalid foreign key IDs: {invalid_foreign_keys}")
            
            if orphaned_pdfs:
                if dry_run:
                    self.stdout.write(self.style.WARNING(
                        f"Would delete {len(orphaned_pdfs)} orphaned DownloadPDF records"
                    ))
                    for pdf in orphaned_pdfs:
                        self.stdout.write(f"  - PDF ID {pdf.id}: {pdf.email} -> DownloadRequest ID {pdf.download_requested_id}")
                else:
                    # Delete orphaned records
                    deleted_count = DownloadPDF.objects.filter(
                        id__in=[pdf.id for pdf in orphaned_pdfs]
                    ).delete()[0]
                    
                    self.stdout.write(
                        self.style.SUCCESS(f"Deleted {deleted_count} orphaned DownloadPDF records")
                    )
            else:
                self.stdout.write(self.style.SUCCESS("No orphaned DownloadPDF records found"))
            
            # Check for any remaining invalid foreign keys
            remaining_invalid = DownloadPDF.objects.filter(
                download_requested_id__isnull=False
            ).exclude(
                download_requested_id__in=valid_download_request_ids
            )
            
            if remaining_invalid.exists():
                self.stdout.write(self.style.WARNING(
                    f"Found {remaining_invalid.count()} records with invalid foreign keys"
                ))
                
                if not dry_run:
                    # Set invalid foreign keys to None
                    updated_count = remaining_invalid.update(download_requested=None)
                    self.stdout.write(
                        self.style.SUCCESS(f"Set {updated_count} invalid foreign keys to None")
                    )
            else:
                self.stdout.write(self.style.SUCCESS("All foreign key constraints are valid"))
        
        if not dry_run:
            self.stdout.write(self.style.SUCCESS("Foreign key constraints fixed successfully"))
