# Generated manually to fix DownloadPDF constraint issue

from django.db import migrations


def fix_downloadpdf_constraint(apps, schema_editor):
    """
    Fix the DownloadPDF constraint by removing duplicate records
    or handling existing data properly
    """
    DownloadPDF = apps.get_model('foodinfo', 'DownloadPDF')
    DownloadRequest = apps.get_model('foodinfo', 'DownloadRequest')
    
    # Remove any duplicate DownloadPDF records
    # Keep only the first record for each unique combination
    seen_combinations = set()
    duplicates = []
    
    for pdf in DownloadPDF.objects.all():
        key = (pdf.email, pdf.name)
        if key in seen_combinations:
            duplicates.append(pdf.id)
        else:
            seen_combinations.add(key)
    
    # Delete duplicate records
    DownloadPDF.objects.filter(id__in=duplicates).delete()


def reverse_fix_downloadpdf_constraint(apps, schema_editor):
    """
    Reverse migration - no action needed
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('foodinfo', '0045_add_download_requested_field'),
    ]

    operations = [
        migrations.RunPython(
            fix_downloadpdf_constraint,
            reverse_fix_downloadpdf_constraint,
        ),
    ]
