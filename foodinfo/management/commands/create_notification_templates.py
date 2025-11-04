from django.core.management.base import BaseCommand
from foodinfo.models import NotificationTemplate

class Command(BaseCommand):
    help = 'Create default notification templates'

    def handle(self, *args, **options):
        templates = [
            {
                'notification_type': 'welcome',
                'title': 'Welcome to IngredientIQ! 🎉',
                'body': 'Hi {user_name}! Start scanning food labels to get personalized health insights and make informed choices.',
                'action_url': '/scan'
            },
            {
                'notification_type': 'subscription_new',
                'title': 'Welcome to {plan_type}! 🚀',
                'body': 'Hi {user_name}! Your {plan_type} subscription is now active. Enjoy unlimited scans and premium features!',
                'action_url': '/scan'
            },
            {
                'notification_type': 'subscription_expiring',
                'title': 'Subscription Expiring in {days_left} Days ⏰',
                'body': 'Hi {user_name}! Your premium subscription expires in {days_left} days. Renew now to continue enjoying unlimited scans.',
                'action_url': '/subscription'
            },
            {
                'notification_type': 'subscription_expired',
                'title': 'Subscription Expired 😔',
                'body': 'Hi {user_name}! Your premium subscription has expired. Renew now to regain access to unlimited scans and premium features.',
                'action_url': '/subscription'
            },
            {
                'notification_type': 'subscription_renewed',
                'title': 'Subscription Renewed! 🎉',
                'body': 'Hi {user_name}! Your {plan_type} subscription has been renewed. Continue enjoying unlimited scans!',
                'action_url': '/scan'
            },
            {
                'notification_type': 'scan_limit_reached',
                'title': 'Scan Limit Alert! 📊',
                'body': 'Hi {user_name}! You have {remaining_scans} scans remaining this month. Upgrade to Premium for unlimited scans!',
                'action_url': '/subscription'
            },
            {
                'notification_type': 'app_update',
                'title': 'New App Update Available! 🚀',
                'body': 'Update to version {version} for the latest features, improvements, and bug fixes!',
                'action_url': None
            }
        ]

        created_count = 0
        updated_count = 0

        for template_data in templates:
            template, created = NotificationTemplate.objects.update_or_create(
                notification_type=template_data['notification_type'],
                defaults={
                    'title': template_data['title'],
                    'body': template_data['body'],
                    'action_url': template_data['action_url'],
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created template: {template.notification_type}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated template: {template.notification_type}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {created_count + updated_count} templates '
                f'({created_count} created, {updated_count} updated)'
            )
        )