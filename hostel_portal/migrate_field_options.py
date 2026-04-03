import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hostel_portal.settings')
django.setup()

from complaints.models import CategoryField, FieldOption

def migrate_options():
    print("📍 Migrating comma-separated options to FieldOption model...")
    fields = CategoryField.objects.filter(field_type='dropdown')
    
    for field in fields:
        if field.options:
            option_texts = [o.strip() for o in field.options.split(',') if o.strip()]
            for text in option_texts:
                # Avoid duplicates if script is re-run
                FieldOption.objects.get_or_create(field=field, text=text)
                print(f"Added option '{text}' to field '{field.label}'")
                
    print("✅ Option migration successful!")

if __name__ == "__main__":
    migrate_options()
