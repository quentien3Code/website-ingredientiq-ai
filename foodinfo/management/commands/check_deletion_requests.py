from django.core.management.base import BaseCommand
from django.utils import timezone
from foodinfo.models import AccountDeletionRequest
from datetime import timedelta


class Command(BaseCommand):
    help = 'Check the status of pending account deletion requests'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Show requests scheduled for deletion within the next N days (default: 7)',
        )

    def handle(self, *args, **options):
        days_ahead = options['days']
        now = timezone.now()
        future_date = now + timedelta(days=days_ahead)
        
        # Get all pending deletion requests
        pending_requests = AccountDeletionRequest.objects.filter(status='pending').order_by('scheduled_deletion_date')
        
        if not pending_requests.exists():
            self.stdout.write(
                self.style.SUCCESS('No pending account deletion requests found.')
            )
            return
        
        self.stdout.write(f'Found {pending_requests.count()} pending deletion request(s):\n')
        
        # Categorize requests
        overdue_requests = []
        upcoming_requests = []
        future_requests = []
        
        for request in pending_requests:
            days_remaining = request.days_remaining
            
            if days_remaining <= 0:
                overdue_requests.append(request)
            elif days_remaining <= days_ahead:
                upcoming_requests.append(request)
            else:
                future_requests.append(request)
        
        # Display overdue requests
        if overdue_requests:
            self.stdout.write(
                self.style.ERROR(f'🚨 OVERDUE ({len(overdue_requests)} account(s)):')
            )
            for request in overdue_requests:
                days_overdue = abs(request.days_remaining)
                self.stdout.write(
                    f'  - {request.user.email} ({days_overdue} days overdue)'
                )
            self.stdout.write('')
        
        # Display upcoming requests
        if upcoming_requests:
            self.stdout.write(
                self.style.WARNING(f'⏰ UPCOMING ({len(upcoming_requests)} account(s) in next {days_ahead} days):')
            )
            for request in upcoming_requests:
                self.stdout.write(
                    f'  - {request.user.email} ({request.days_remaining} days remaining)'
                )
            self.stdout.write('')
        
        # Display future requests
        if future_requests:
            self.stdout.write(
                self.style.SUCCESS(f'📅 FUTURE ({len(future_requests)} account(s) beyond {days_ahead} days):')
            )
            for request in future_requests:
                self.stdout.write(
                    f'  - {request.user.email} ({request.days_remaining} days remaining)'
                )
            self.stdout.write('')
        
        # Summary
        total_overdue = len(overdue_requests)
        if total_overdue > 0:
            self.stdout.write(
                self.style.ERROR(f'⚠️  {total_overdue} account(s) are overdue for deletion!')
            )
            self.stdout.write(
                self.style.WARNING('Run: python manage.py delete_scheduled_accounts')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('✅ No accounts are overdue for deletion.')
            )
