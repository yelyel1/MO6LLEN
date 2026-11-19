from django.test import TestCase
from django.urls import reverse

from .forms import StudentForm
from .models import Student


class StudentRegistrationTests(TestCase):
    def test_student_form_uses_existing_model_fields(self):
        self.assertIs(StudentForm._meta.model, Student)
        self.assertEqual(
            list(StudentForm._meta.fields),
            [
                "student_id",
                "first_name",
                "last_name",
                "gender",
                "date_of_birth",
                "contact_no",
            ],
        )
        self.assertEqual(
            StudentForm().fields["date_of_birth"].widget.input_type,
            "date",
        )

    def test_registration_page_loads(self):
        response = self.client.get(reverse("student_registration"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/registration.html")
        self.assertContains(response, "Student Registration")
        for field_name in (
            "student_id",
            "first_name",
            "last_name",
            "gender",
            "date_of_birth",
            "contact_no",
        ):
            self.assertContains(response, f'name="{field_name}"')

    def test_valid_submission_saves_student_and_shows_success(self):
        response = self.client.post(
            reverse("student_registration"),
            {
                "student_id": "S123",
                "first_name": "Ada",
                "last_name": "Lovelace",
                "gender": "Female",
                "date_of_birth": "1815-12-10",
                "contact_no": "555-0100",
            },
        )

        self.assertRedirects(response, reverse("registration_success"))
        response = self.client.get(response.url)
        self.assertTemplateUsed(response, "registration/success.html")
        self.assertContains(response, "Student Registered Successfully!")
        self.assertContains(response, "The registration has been completed.")
        self.assertContains(response, reverse("student_registration"))
        self.assertContains(response, reverse("home"))
        self.assertEqual(Student.objects.count(), 1)

    def test_invalid_submission_is_not_saved(self):
        response = self.client.post(
            reverse("student_registration"),
            {
                "student_id": "S123",
                "first_name": "Ada",
                "last_name": "Lovelace",
                "gender": "Other",
                "date_of_birth": "not-a-date",
                "contact_no": "555-0100",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/registration.html")
        self.assertEqual(Student.objects.count(), 0)

    def test_student_list_displays_students_in_name_order(self):
        Student.objects.create(
            student_id="S002",
            first_name="Grace",
            last_name="Hopper",
            gender="Female",
            date_of_birth="1906-12-09",
            contact_no="555-0102",
        )
        Student.objects.create(
            student_id="S001",
            first_name="Ada",
            last_name="Lovelace",
            gender="Female",
            date_of_birth="1815-12-10",
            contact_no="555-0101",
        )

        response = self.client.get(reverse("student_list"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/student_list.html")
        self.assertEqual(
            list(response.context["students"].values_list("student_id", flat=True)),
            ["S002", "S001"],
        )
        self.assertContains(response, "Student Directory")
        self.assertContains(response, "Ada")
        self.assertContains(response, "Grace")

    def test_student_list_searches_student_id_and_names_case_insensitively(self):
        Student.objects.create(
            student_id="S123",
            first_name="Ada",
            last_name="Lovelace",
            gender="Female",
            date_of_birth="1815-12-10",
            contact_no="555-0100",
        )
        Student.objects.create(
            student_id="S456",
            first_name="Grace",
            last_name="Hopper",
            gender="Female",
            date_of_birth="1906-12-09",
            contact_no="555-0101",
        )

        for query in ("s123", "ADA", "hopper"):
            with self.subTest(query=query):
                response = self.client.get(reverse("student_list"), {"q": query})
                self.assertEqual(
                    list(
                        response.context["students"].values_list(
                            "student_id", flat=True
                        )
                    ),
                    ["S123"] if query != "hopper" else ["S456"],
                )

    def create_student(self, student_id="S123"):
        return Student.objects.create(
            student_id=student_id,
            first_name="Ada",
            last_name="Lovelace",
            gender="Female",
            date_of_birth="1815-12-10",
            contact_no="555-0100",
        )

    def test_student_detail_displays_record_and_returns_404_for_missing_record(self):
        student = self.create_student()

        response = self.client.get(
            reverse("student_detail", kwargs={"pk": student.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/student_detail.html")
        self.assertContains(response, "Ada")
        self.assertContains(response, "Lovelace")
        self.assertContains(response, "Dec. 10, 1815")
        self.assertContains(response, "/static/registration/style.css")

        response = self.client.get(
            reverse("student_detail", kwargs={"pk": student.pk + 1})
        )
        self.assertEqual(response.status_code, 404)

    def test_student_create_saves_valid_form_and_reports_success(self):
        response = self.client.post(
            reverse("student_create"),
            {
                "student_id": "S123",
                "first_name": "Ada",
                "last_name": "Lovelace",
                "gender": "Female",
                "date_of_birth": "1815-12-10",
                "contact_no": "555-0100",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/student_list.html")
        self.assertContains(response, "Student record created successfully.")
        self.assertEqual(Student.objects.count(), 1)

    def test_student_create_displays_validation_errors_without_saving(self):
        response = self.client.post(
            reverse("student_create"),
            {
                "student_id": "S123",
                "first_name": "Ada",
                "last_name": "Lovelace",
                "gender": "Other",
                "date_of_birth": "not-a-date",
                "contact_no": "555-0100",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/student_form.html")
        self.assertContains(response, "Select a valid choice")
        self.assertContains(response, "Enter a valid date")
        self.assertEqual(Student.objects.count(), 0)

    def test_student_update_changes_record_and_reports_success(self):
        student = self.create_student()

        response = self.client.post(
            reverse("student_update", kwargs={"pk": student.pk}),
            {
                "student_id": "S123",
                "first_name": "Augusta",
                "last_name": "Lovelace",
                "gender": "Female",
                "date_of_birth": "1815-12-10",
                "contact_no": "555-0100",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/student_detail.html")
        self.assertContains(response, "Student record updated successfully.")
        student.refresh_from_db()
        self.assertEqual(student.first_name, "Augusta")

    def test_student_delete_requires_confirmation_and_post(self):
        student = self.create_student()

        response = self.client.get(
            reverse("student_delete", kwargs={"pk": student.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "registration/student_confirm_delete.html"
        )
        self.assertContains(response, "csrfmiddlewaretoken")
        self.assertEqual(Student.objects.count(), 1)

        response = self.client.post(
            reverse("student_delete", kwargs={"pk": student.pk}),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/student_list.html")
        self.assertContains(response, "Student record deleted successfully.")
        self.assertEqual(Student.objects.count(), 0)
