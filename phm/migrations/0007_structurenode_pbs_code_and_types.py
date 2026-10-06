from django.db import migrations, models


def fill_pbs(apps, schema_editor):
    StructureNode = apps.get_model("phm", "StructureNode")
    for node in StructureNode.objects.all():
        node.pbs_code = node.properties.get("pbs_code") or f"PBS-{node.pk:04d}"
        node.save(update_fields=["pbs_code"])


class Migration(migrations.Migration):
    dependencies = [("phm", "0006_releaseassessment")]
    operations = [
        migrations.AddField(
            model_name="structurenode",
            name="pbs_code",
            field=models.CharField(blank=True, db_index=True, max_length=100, null=True),
        ),
        migrations.RunPython(fill_pbs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="structurenode", name="pbs_code",
            field=models.CharField(db_index=True, max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name="structurenode", name="node_type",
            field=models.CharField(choices=[("vehicle", "运载器"), ("system", "分系统"), ("subsystem", "子系统"), ("product", "单机产品")], default="product", max_length=50),
        ),
    ]
