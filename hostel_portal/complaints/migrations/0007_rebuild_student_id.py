from django.db import migrations, models
import django.db.models.deletion

def backup_student_data(apps, schema_editor):
    Complaint = apps.get_model('complaints', 'Complaint')
    # Store mappings of complaint ID to student enrollment number string
    backup = []
    for c in Complaint.objects.all():
        # Read the raw value from student_id column as a string
        # student_id might currently be a string or a number but we want it as a string
        backup.append({'id': c.id, 'student_id': str(c.student_id)})
    
    # Store in a temporary global so the restore function can access it
    # Note: This only works if operations are in the same migrate run
    global _complaint_backup
    _complaint_backup = backup

def restore_student_data(apps, schema_editor):
    Complaint = apps.get_model('complaints', 'Complaint')
    global _complaint_backup
    if not _complaint_backup:
        return
        
    for item in _complaint_backup:
        Complaint.objects.filter(id=item['id']).update(student_id=item['student_id'])

class Migration(migrations.Migration):

    dependencies = [
        ('complaints', '0006_fix_student_id_type'),
        ('accounts', '0012_remove_studentprofile_id_and_more'),
    ]

    operations = [
        # 1. Backup existing data
        migrations.RunPython(backup_student_data, reverse_code=migrations.RunPython.noop),
        
        # 2. Drop the column (this cleans out indices/types/constraints)
        migrations.RemoveField(
            model_name='complaint',
            name='student',
        ),
        
        # 3. Add it back fresh as a proper CharField ForeignKey
        migrations.AddField(
            model_name='complaint',
            name='student',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, 
                related_name='complaints', 
                to='accounts.studentprofile',
                null=True # Allow null temporarily for restoration
            ),
        ),
        
        # 4. Restore the data
        migrations.RunPython(restore_student_data, reverse_code=migrations.RunPython.noop),
        
        # 5. Lock it down (make it NOT NULL)
        migrations.AlterField(
            model_name='complaint',
            name='student',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, 
                related_name='complaints', 
                to='accounts.studentprofile'
            ),
        ),
    ]
