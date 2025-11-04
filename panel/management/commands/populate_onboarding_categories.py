from django.core.management.base import BaseCommand
from panel.models import OnboardingCategory


class Command(BaseCommand):
    help = 'Populate the static onboarding categories as per client requirements'

    def handle(self, *args, **options):
        categories_data = [
            {
                'category_key': 'profile_demographics',
                'category_name': 'Profile & Demographics',
                'description': 'Establish baseline (age, sex, height, region). Feeds all downstream layers with physiological constants.',
                'purpose': 'Provides foundational user data that informs all AI recommendations and analysis.',
                'order': 1
            },
            {
                'category_key': 'motivation_cognitive',
                'category_name': 'Motivation & Cognitive Profile',
                'description': 'Determines AI\'s tone, reasoning depth, and motivational triggers.',
                'purpose': 'Shapes how the AI communicates and motivates users based on their cognitive preferences.',
                'order': 2
            },
            {
                'category_key': 'medical_clinical',
                'category_name': 'Medical & Clinical History',
                'description': 'Core safety mapping — enables deterministic risk recognition across all ingredient databases.',
                'purpose': 'Ensures safe recommendations by identifying medical conditions that affect food choices.',
                'order': 3
            },
            {
                'category_key': 'medications_supplements',
                'category_name': 'Medications & Supplements',
                'description': 'Adds pharmaceutical and supplement cross-interaction intelligence.',
                'purpose': 'Prevents harmful interactions between medications/supplements and food ingredients.',
                'order': 4
            },
            {
                'category_key': 'allergies_sensitivities',
                'category_name': 'Allergies & Sensitivities',
                'description': 'Enforces hard constraints (non-negotiable No-Go flags).',
                'purpose': 'Creates absolute safety boundaries for users with allergies or sensitivities.',
                'order': 5
            },
            {
                'category_key': 'lifestyle_dietary',
                'category_name': 'Lifestyle & Dietary Preferences',
                'description': 'Applies user value filters (ethical, cultural, environmental).',
                'purpose': 'Personalizes recommendations based on user values, culture, and lifestyle choices.',
                'order': 6
            },
            {
                'category_key': 'behavioral_rhythm',
                'category_name': 'Behavioral Rhythm & Feedback Cadence',
                'description': 'Times AI interactions and check-ins according to circadian and behavioral data.',
                'purpose': 'Optimizes engagement timing and frequency based on user behavior patterns.',
                'order': 7
            }
        ]

        created_count = 0
        updated_count = 0

        for category_data in categories_data:
            category, created = OnboardingCategory.objects.get_or_create(
                category_key=category_data['category_key'],
                defaults=category_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created category: {category.category_name}')
                )
            else:
                # Update existing category with new data
                for key, value in category_data.items():
                    setattr(category, key, value)
                category.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated category: {category.category_name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {len(categories_data)} categories. '
                f'Created: {created_count}, Updated: {updated_count}'
            )
        )
