# Generated by Django 4.2.4 on 2023-09-24 03:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0003_alter_team_data_modes_mode'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlayerInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Player', models.CharField(max_length=255)),
                ('Country', models.CharField(max_length=100)),
                ('Position', models.CharField(max_length=100)),
                ('Born', models.DateField()),
                ('Club', models.CharField(max_length=255)),
            ],
        ),
    ]
