from django.db import migrations

def create_default_tenant(apps, schema_editor):
    Tenant = apps.get_model('ingestion', 'Tenant')
    if not Tenant.objects.exists():
        Tenant.objects.create(name="Breathe ESG")

def remove_default_tenant(apps, schema_editor):
    Tenant = apps.get_model('ingestion', 'Tenant')
    Tenant.objects.filter(name="Breathe ESG").delete()

class Migration(migrations.Migration):

    dependencies = [
        ('ingestion', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_tenant, reverse_code=remove_default_tenant),
    ]
