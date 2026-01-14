from django.db import migrations, models


def normalize_subscription_plan_labels(apps, schema_editor):
    User = apps.get_model('foodinfo', 'User')

    # Legacy "Freemium" naming
    User.objects.filter(subscription_plan__iexact='Freemium plan').update(subscription_plan='Free')
    User.objects.filter(subscription_plan__iexact='Freemium').update(subscription_plan='Free')

    # Legacy premium variants (e.g., "Monthly Premium", "Yearly Premium")
    User.objects.filter(subscription_plan__icontains='premium').exclude(
        subscription_plan__in=['Premium', 'Family/Team', 'Enterprise']
    ).update(subscription_plan='Premium')


class Migration(migrations.Migration):

    dependencies = [
        ('foodinfo', '0053_alter_user_created_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='subscription_plan',
            field=models.CharField(default='Free', max_length=100),
        ),
        migrations.RunPython(normalize_subscription_plan_labels, migrations.RunPython.noop),
    ]
