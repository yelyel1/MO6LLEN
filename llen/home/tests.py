from django.test import TestCase
from django.urls import reverse


class HomePageTests(TestCase):
    def test_home_routes_match_checkpoint_paths(self):
        self.assertEqual(reverse("landing"), "/")
        self.assertEqual(reverse("home"), "/Home/")

    def test_home_page_renders_home_template_with_context(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home/home.html")
        self.assertContains(response, "<title>My Home Page</title>")
        self.assertContains(response, "Welcome to my first Django application!")
        self.assertContains(response, reverse("landing"))

    def test_landing_page_renders_landing_template(self):
        response = self.client.get(reverse("landing"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home/landing.html")
        self.assertContains(response, "Welcome to My Django Application")
        self.assertContains(response, reverse("home"))
