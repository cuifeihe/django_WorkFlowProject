# Generated by Django 4.2.1 on 2023-07-04 12:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_workflow', '0002_alter_workflow_creator_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workflow',
            name='limit_expression',
            field=models.JSONField(default=dict, verbose_name='限制工单提交的策略表达式'),
        ),
    ]
