# Generated manually to fix DownloadPDF constraint issue

from django.db import migrations, models
import django.db.models.deletion


def cleanup_before_field_change(apps, schema_editor):
    """
    Clean up data before changing the field type to avoid UNIQUE constraint errors
    """
    DownloadPDF = apps.get_model('foodinfo', 'DownloadPDF')
    
    # Remove any records that might cause UNIQUE constraint violations
    # by keeping only the first record for each unique combination
    seen_combinations = set()
    duplicates = []
    
    for pdf in DownloadPDF.objects.all():
        key = (pdf.email, pdf.name)
        if key in seen_combinations:
            duplicates.append(pdf.id)
        else:
            seen_combinations.add(key)
    
    # Delete duplicate records
    if duplicates:
        DownloadPDF.objects.filter(id__in=duplicates).delete()
        print(f"Removed {len(duplicates)} duplicate records before field change")


def reverse_cleanup_before_field_change(apps, schema_editor):
    """
    Reverse migration - no action needed
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('foodinfo', '0046_fix_downloadpdf_constraint'),
    ]

    operations = [
        migrations.RunPython(
            cleanup_before_field_change,
            reverse_cleanup_before_field_change,
        ),
        migrations.AlterField(
            model_name='downloadpdf',
            name='download_requested',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='download_pdfs', to='foodinfo.downloadrequest'),
        ),
    ]
