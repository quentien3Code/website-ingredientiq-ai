from django.db import migrations, models


DEFAULT_FAQ_CATEGORIES = [
    (10, 'Getting started'),
    (20, 'Results & personalization'),
    (30, 'Data sources & accuracy'),
    (40, 'Safety, privacy & ethics'),
    (50, 'Plans, pricing & limits'),
    (60, 'Compliance & regional notes'),
    (70, 'App, account & support'),
    (80, 'Methodology & transparency'),
]


def seed_faq_categories(apps, schema_editor):
    FaqCategory = apps.get_model('Website', 'FaqCategory')

    for order, title in DEFAULT_FAQ_CATEGORIES:
        FaqCategory.objects.update_or_create(
            title=title,
            defaults={'order': order, 'is_active': True},
        )


def unseed_faq_categories(apps, schema_editor):
    FaqCategory = apps.get_model('Website', 'FaqCategory')
    titles = [title for _, title in DEFAULT_FAQ_CATEGORIES]
    FaqCategory.objects.filter(title__in=titles).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('Website', '0021_downloadpdf_pdf_alter_downloadpdf_email'),
    ]

    operations = [
        migrations.CreateModel(
            name='FaqCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, unique=True)),
                ('order', models.PositiveIntegerField(default=0, help_text='Display order in admin and APIs')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'FAQ Category',
                'verbose_name_plural': 'FAQ Categories',
                'ordering': ['order', 'title'],
            },
        ),
        migrations.AddField(
            model_name='faqs',
            name='order',
            field=models.PositiveIntegerField(default=0, help_text='Sort order within a category'),
        ),
        migrations.AddField(
            model_name='faqs',
            name='is_active',
            field=models.BooleanField(default=True, help_text='If false, this FAQ will not appear on the public /faqs page'),
        ),
        migrations.RunPython(seed_faq_categories, unseed_faq_categories),
    ]
