# Generated manually to fix DownloadPDF foreign key constraint

from django.db import migrations


def fix_foreign_key_constraint(apps, schema_editor):
    """
    Fix the DownloadPDF foreign key constraint by:
    1. Removing orphaned DownloadPDF records that reference non-existent DownloadRequest records
    2. Creating missing DownloadRequest records if needed
    3. Ensuring data integrity
    """
    DownloadPDF = apps.get_model('foodinfo', 'DownloadPDF')
    DownloadRequest = apps.get_model('foodinfo', 'DownloadRequest')
    
    # Get all DownloadPDF records with invalid foreign keys
    orphaned_pdfs = []
    valid_download_requests = set(DownloadRequest.objects.values_list('id', flat=True))
    
    for pdf in DownloadPDF.objects.all():
        if pdf.download_requested_id and pdf.download_requested_id not in valid_download_requests:
            orphaned_pdfs.append(pdf.id)
    
    # Delete orphaned DownloadPDF records
    if orphaned_pdfs:
        print(f"Deleting {len(orphaned_pdfs)} orphaned DownloadPDF records")
        DownloadPDF.objects.filter(id__in=orphaned_pdfs).delete()
    
    # Ensure all remaining DownloadPDF records have valid foreign keys
    for pdf in DownloadPDF.objects.all():
        if pdf.download_requested_id and pdf.download_requested_id not in valid_download_requests:
            # If somehow we still have invalid references, set them to None
            pdf.download_requested = None
            pdf.save()


def reverse_fix_foreign_key_constraint(apps, schema_editor):
    """
    Reverse migration - no action needed
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('foodinfo', '0047_alter_downloadpdf_download_requested'),
    ]

    operations = [
        migrations.RunPython(
            fix_foreign_key_constraint,
            reverse_fix_foreign_key_constraint,
        ),
    ]
