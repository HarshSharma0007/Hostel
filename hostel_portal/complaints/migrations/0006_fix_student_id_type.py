from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('complaints', '0005_alter_complaint_category'),
        ('accounts', '0012_remove_studentprofile_id_and_more'),
    ]

    operations = [
        # Manually alter the column type in Postgres to avoid bigint error
        migrations.RunSQL(
            sql='ALTER TABLE complaints_complaint ALTER COLUMN student_id TYPE varchar(20) USING student_id::varchar(20);',
            reverse_sql='ALTER TABLE complaints_complaint ALTER COLUMN student_id TYPE bigint USING student_id::bigint;',
        ),
        # Sync Django's internal state
        migrations.AlterField(
            model_name='complaint',
            name='student',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='complaints', to='accounts.studentprofile'),
        ),
    ]
