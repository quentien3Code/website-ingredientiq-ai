from django.core.management.base import BaseCommand
from django.utils import timezone
from foodinfo.models import AccountDeletionRequest, User
from foodinfo.helpers import safe_delete_user
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Delete accounts that have been scheduled for deletion after 30 days'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force deletion even if scheduled date is in the future',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        # Get current time
        now = timezone.now()
        
        # Find accounts scheduled for deletion
        if force:
            # Force mode: delete all pending deletion requests
            deletion_requests = AccountDeletionRequest.objects.filter(status='pending')
            self.stdout.write(
                self.style.WARNING('FORCE MODE: Deleting all pending deletion requests')
            )
        else:
            # Normal mode: only delete accounts past their scheduled deletion date
            deletion_requests = AccountDeletionRequest.objects.filter(
                status='pending',
                scheduled_deletion_date__lte=now
            )
        
        if not deletion_requests.exists():
            self.stdout.write(
                self.style.SUCCESS('No accounts scheduled for deletion at this time.')
            )
            return
        
        self.stdout.write(
            f'Found {deletion_requests.count()} account(s) scheduled for deletion:'
        )
        
        deleted_count = 0
        error_count = 0
        
        for deletion_request in deletion_requests:
            user = deletion_request.user
            days_past_due = (now - deletion_request.scheduled_deletion_date).days
            
            self.stdout.write(
                f'  - {user.email} (scheduled: {deletion_request.scheduled_deletion_date.strftime("%Y-%m-%d %H:%M")}, '
                f'{days_past_due} days past due)'
            )
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(f'    [DRY RUN] Would delete account: {user.email}')
                )
                continue
            
            try:
                # Log the deletion
                logger.info(f'Automatically deleting account: {user.email} (scheduled deletion)')
                
                # Update deletion request status before deleting user
                deletion_request.status = 'completed'
                deletion_request.save()
                
                # Use safe deletion function to handle foreign key constraints
                success, message = safe_delete_user(user)
                
                if success:
                    deleted_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'    ✓ Deleted account: {user.email}')
                    )
                else:
                    raise Exception(message)
                
            except Exception as e:
                error_count += 1
                logger.error(f'Error deleting account {user.email}: {str(e)}')
                self.stdout.write(
                    self.style.ERROR(f'    ✗ Error deleting {user.email}: {str(e)}')
                )
        
        # Summary
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'\n[DRY RUN] Would have deleted {deletion_requests.count()} account(s)')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\nDeletion completed:')
            )
            self.stdout.write(f'  - Successfully deleted: {deleted_count} account(s)')
            if error_count > 0:
                self.stdout.write(
                    self.style.ERROR(f'  - Errors: {error_count} account(s)')
                )
        
        # Log summary
        logger.info(f'Account deletion job completed: {deleted_count} deleted, {error_count} errors')
