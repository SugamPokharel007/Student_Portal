# Generated by Django 5.1.5 on 2025-04-07 21:29

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student_app', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='subject',
            name='image',
        ),
        migrations.AddField(
            model_name='notice',
            name='is_general',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='notice',
            name='subject',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='student_app.subject'),
        ),
        migrations.AddField(
            model_name='subject',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='subject',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='contactmessage',
            name='name',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='notice',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='subject',
            name='name',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='subject',
            name='year',
            field=models.CharField(max_length=20),
        ),
        migrations.CreateModel(
            name='QuestionBank',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('file', models.FileField(upload_to='question_banks/')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='student_app.subject')),
            ],
        ),
        migrations.CreateModel(
            name='Syllabus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('content', models.TextField()),
                ('file', models.FileField(blank=True, null=True, upload_to='syllabus/')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='student_app.subject')),
            ],
        ),
    ]
