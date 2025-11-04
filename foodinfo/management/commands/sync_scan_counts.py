from django.core.management.base import BaseCommand
from foodinfo.models import User, FoodLabelScan, MonthlyScanUsage


class Command(BaseCommand):
    help = 'Sync all users scan counts in MonthlyScanUsage with actual FoodLabelScan objects'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Sync scan counts for a specific user by email',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without making changes',
        )

    def handle(self, *args, **options):
        user_email = options.get('user')
        dry_run = options.get('dry_run', False)
        
        if user_email:
            try:
                user = User.objects.get(email=user_email)
                self.sync_user_scan_count(user, dry_run)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User with email {user_email} not found')
                )
        else:
            # Sync all users
            users = User.objects.all()
            synced_count = 0
            
            for user in users:
                if self.sync_user_scan_count(user, dry_run):
                    synced_count += 1
            
            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(f'Would sync scan counts for {synced_count} users')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully synced scan counts for {synced_count} users')
                )

    def sync_user_scan_count(self, user, dry_run=False):
        """Sync scan count for a specific user"""
        try:
            actual_count = FoodLabelScan.objects.filter(user=user).count()
            usage = MonthlyScanUsage.get_or_create_current_month(user)
            
            if usage.scan_count != actual_count:
                if dry_run:
                    self.stdout.write(
                        f'Would sync user {user.email}: {usage.scan_count} -> {actual_count}'
                    )
                else:
                    old_count = usage.scan_count
                    usage.scan_count = actual_count
                    usage.save()
                    self.stdout.write(
                        f'Synced user {user.email}: {old_count} -> {actual_count}'
                    )
                return True
            else:
                if dry_run:
                    self.stdout.write(f'User {user.email}: already in sync ({actual_count})')
                return False
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error syncing scan count for user {user.email}: {e}')
            )
            return False 