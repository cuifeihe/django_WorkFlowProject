# Generated by Django 4.2.1 on 2023-06-30 01:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_ticket', '0005_alter_ticket_results_of_all_nodes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticket',
            name='results_of_all_nodes',
            field=models.JSONField(default=dict, verbose_name='所有节点的处理结果'),
        ),
    ]
