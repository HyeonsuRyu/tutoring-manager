from django.contrib.auth.hashers import identify_hasher, make_password
from django.db import migrations, models


def hash_existing_plain_codes(apps, schema_editor):
    BackupCode = apps.get_model("accounts", "BackupCode")
    for row in BackupCode.objects.all():
        value = row.code_hash
        if not value:
            continue
        try:
            identify_hasher(value)
        except ValueError:
            row.code_hash = make_password(value)
            row.save(update_fields=["code_hash"])


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_add_username_compat"),
    ]

    operations = [
        migrations.RenameField(
            model_name="backupcode",
            old_name="code",
            new_name="code_hash",
        ),
        migrations.AlterField(
            model_name="backupcode",
            name="code_hash",
            field=models.CharField(max_length=128),
        ),
        migrations.RunPython(hash_existing_plain_codes, migrations.RunPython.noop),
    ]
