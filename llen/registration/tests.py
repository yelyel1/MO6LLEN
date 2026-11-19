from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import StudentForm
from .models import Student


class StudentRegistrationTests(TestCase):
    def setUp(self):
        self.staff_user = get_user_model().objects.create_user(
            username="staff",
            password="test-password-123",
            is_staff=True,
        )
        self.client.force_login(self.staff_user)

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
        self.assertContains(response, reverse("student_list"))
        self.assertNotContains(response, "<table")
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
        self.client.logout()
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
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/success.html")
        self.assertContains(response, "Student Registered Successfully!")
        self.assertEqual(Student.objects.count(), 1)

    def test_registration_and_directory_pages_link_to_each_other(self):
        registration_response = self.client.get(reverse("student_registration"))
        directory_response = self.client.get(reverse("student_list"))

        self.assertContains(registration_response, reverse("student_list"))
        self.assertContains(directory_response, reverse("student_registration"))

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

    def test_staff_dashboard_counts_gender_and_searches_report(self):
        male_student = self.create_student("M123")
        male_student.gender = "Male"
        male_student.first_name = "Casey"
        male_student.save(update_fields=["gender", "first_name"])
        self.create_student("F456")

        response = self.client.get(
            reverse("staff_dashboard"),
            {"q": "m123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_students"], 2)
        self.assertEqual(response.context["male_students"], 1)
        self.assertEqual(response.context["female_students"], 1)
        self.assertEqual(response.context["male_percent"], 50)
        self.assertEqual(response.context["female_percent"], 50)
        self.assertEqual(
            list(response.context["students"].values_list("pk", flat=True)),
            [male_student.pk],
        )
        self.assertContains(response, "Student Management Dashboard")
        self.assertContains(response, "Open Student Directory")
        self.assertContains(response, 'action="/logout/"')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')

    def test_dashboard_alias_counts_both_supported_gender_values(self):
        male_standard = self.create_student("M001")
        male_standard.gender = "Male"
        male_standard.save(update_fields=["gender"])
        male_abbreviated = self.create_student("M002")
        male_abbreviated.gender = "M"
        male_abbreviated.save(update_fields=["gender"])

        female_abbreviated = self.create_student("F001")
        female_abbreviated.gender = "F"
        female_abbreviated.save(update_fields=["gender"])
        self.create_student("F002")

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/dashboard.html")
        self.assertEqual(response.context["total_students"], 4)
        self.assertEqual(response.context["male_students"], 2)
        self.assertEqual(response.context["female_students"], 2)
        self.assertEqual(response.context["male_percent"], 50)
        self.assertEqual(response.context["female_percent"], 50)

    def test_staff_dashboard_handles_empty_student_database(self):
        response = self.client.get(reverse("staff_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_students"], 0)
        self.assertEqual(response.context["male_students"], 0)
        self.assertEqual(response.context["female_students"], 0)
        self.assertEqual(response.context["male_percent"], 0)
        self.assertEqual(response.context["female_percent"], 0)
        self.assertContains(response, "No student records found.")

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

    def test_staff_login_redirects_to_dashboard(self):
        self.client.logout()

        response = self.client.post(
            reverse("login"),
            {"username": "staff", "password": "test-password-123"},
        )

        self.assertRedirects(response, reverse("dashboard"))
        response = self.client.get(response.url)
        self.assertTemplateUsed(response, "registration/dashboard.html")
        self.assertContains(response, "Welcome, staff!")
        self.assertContains(response, reverse("student_list"))
        self.assertContains(response, 'action="/logout/"')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')

    def test_invalid_staff_login_shows_error(self):
        self.client.logout()

        response = self.client.post(
            reverse("login"),
            {"username": "staff", "password": "wrong-password"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username or password")
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout_ends_session_and_redirects_to_login(self):
        response = self.client.post(reverse("logout"), follow=True)

        self.assertRedirects(response, reverse("login"))
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_anonymous_users_are_redirected_from_staff_pages(self):
        student = self.create_student()
        self.client.logout()
        protected_urls = (
            reverse("staff_dashboard"),
            reverse("student_list"),
            reverse("student_create"),
            reverse("student_detail", kwargs={"pk": student.pk}),
            reverse("student_update", kwargs={"pk": student.pk}),
            reverse("student_delete", kwargs={"pk": student.pk}),
        )

        for url in protected_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(
                    response,
                    f"{reverse('login')}?next={url}",
                )

    def test_non_staff_users_cannot_access_staff_pages(self):
        student = self.create_student()
        user = get_user_model().objects.create_user(
            username="regular",
            password="test-password-123",
            is_staff=False,
        )
        self.client.force_login(user)
        protected_urls = (
            reverse("staff_dashboard"),
            reverse("student_list"),
            reverse("student_create"),
            reverse("student_detail", kwargs={"pk": student.pk}),
            reverse("student_update", kwargs={"pk": student.pk}),
            reverse("student_delete", kwargs={"pk": student.pk}),
        )

        for url in protected_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("login"), response.url)

    def test_public_student_registration_remains_available(self):
        self.client.logout()

        response = self.client.get(reverse("student_registration"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/registration.html")

    def test_login_route_uses_project_level_template(self):
        self.client.logout()

        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "login.html")
        self.assertContains(response, "Staff Login")
