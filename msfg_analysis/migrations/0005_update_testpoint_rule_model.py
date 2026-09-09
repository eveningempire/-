# Generated manually for updating TestPointRule model

from django.db import migrations, models
import django.db.models.deletion


def migrate_testpoint_rules_forward(apps, schema_editor):
    """将现有的TestPointRule关联到对应的活跃MSFG定义"""
    TestPointRule = apps.get_model('msfg_analysis', 'TestPointRule')
    MSFGDefinition = apps.get_model('msfg_analysis', 'MSFGDefinition')
    
    # 对于每个现有的TestPointRule，找到对应CMGModel的活跃MSFG定义
    for rule in TestPointRule.objects.all():
        active_msfg = MSFGDefinition.objects.filter(
            cmg_model=rule.cmg_model,
            is_active=True
        ).order_by('-updated_at').first()
        
        if active_msfg:
            rule.msfg_definition = active_msfg
            rule.save()


def migrate_testpoint_rules_reverse(apps, schema_editor):
    """逆向迁移：不需要特别处理，字段会被删除"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('msfg_analysis', '0004_msfganalysisresult_component_results_and_more'),
    ]

    operations = [
        # 添加新的模型
        migrations.CreateModel(
            name='TestPointComponentMapping',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('test_point_name', models.CharField(help_text='测试点名称', max_length=128)),
                ('component_name', models.CharField(help_text='部件名称', max_length=128)),
                ('component_type', models.CharField(choices=[('motor', '电机系统'), ('bearing', '轴承系统'), ('gear', '传动系统'), ('sensor', '传感器系统'), ('control', '控制系统'), ('power', '电源系统'), ('structural', '结构系统'), ('thermal', '热管理系统'), ('other', '其他部件')], default='other', help_text='部件类型', max_length=64)),
                ('importance_weight', models.FloatField(default=1.0, help_text='重要度权重（0.1-10）')),
                ('is_critical', models.BooleanField(default=False, help_text='是否为关键部件')),
                ('description', models.TextField(blank=True, help_text='映射描述')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('msfg_definition', models.ForeignKey(help_text='关联的MSFG定义', on_delete=django.db.models.deletion.CASCADE, related_name='testpoint_component_mappings', to='msfg_analysis.msfgdefinition')),
            ],
            options={
                'verbose_name': '测试点-部件映射',
                'verbose_name_plural': '测试点-部件映射',
            },
        ),
        
        # 为TestPointRule添加msfg_definition字段（允许NULL）
        migrations.AddField(
            model_name='testpointrule',
            name='msfg_definition',
            field=models.ForeignKey(null=True, help_text='关联的MSFG定义', on_delete=django.db.models.deletion.CASCADE, related_name='testpoint_rules', to='msfg_analysis.msfgdefinition'),
        ),
        
        # 数据迁移：为现有记录设置msfg_definition
        migrations.RunPython(migrate_testpoint_rules_forward, migrate_testpoint_rules_reverse),
        
        # 将字段改为非空
        migrations.AlterField(
            model_name='testpointrule',
            name='msfg_definition',
            field=models.ForeignKey(help_text='关联的MSFG定义', on_delete=django.db.models.deletion.CASCADE, related_name='testpoint_rules', to='msfg_analysis.msfgdefinition'),
        ),
        
        # 更新unique_together约束
        migrations.AlterUniqueTogether(
            name='testpointrule',
            unique_together={('msfg_definition', 'test_name', 'rule_id')},
        ),
        
        # 为TestPointComponentMapping添加unique_together约束
        migrations.AlterUniqueTogether(
            name='testpointcomponentmapping',
            unique_together={('msfg_definition', 'test_point_name')},
        ),
    ]
