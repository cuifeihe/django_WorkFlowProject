# Generated by Django 4.2.1 on 2023-06-30 01:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_ticket', '0003_alter_ticket_now_handler'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ticket',
            options={'ordering': ['id', 'workflow', 'title']},
        ),
        migrations.AlterField(
            model_name='ticket',
            name='results_of_all_nodes',
            field=models.JSONField(default='', verbose_name='所有节点的处理结果'),
        ),
    ]
