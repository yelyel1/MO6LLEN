from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0001_initial"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="StudentRegistration",
            new_name="Student",
        ),
        migrations.AlterField(
            model_name="student",
            name="student_id",
            field=models.CharField(max_length=20, unique=True),
        ),
        migrations.AlterField(
            model_name="student",
            name="gender",
            field=models.CharField(
                choices=[("Male", "Male"), ("Female", "Female")],
                max_length=10,
            ),
        ),
        migrations.AlterField(
            model_name="student",
            name="contact_no",
            field=models.CharField(max_length=20),
        ),
    ]
