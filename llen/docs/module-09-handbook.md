# Module 09: Dashboard Enhancement and Basic Reporting

## Student Course Handbook

This handbook explains how the staff dashboard in the existing Django Student
Registration System retrieves student records, calculates summary values,
searches the report, and presents the results. It describes the current
project implementation in:

- `registration/views.py`
- `registration/templates/registration/dashboard.html`
- `registration/static/registration/style.css`

The activity extends the existing project. It does not create a new Django
project, app, model, authentication system, or stylesheet.

## Learning outcomes

After working through this module, you should be able to:

- Explain how a Django view sends database information to a template.
- Count student records and group counts by gender.
- Calculate percentages safely when the database contains no students.
- Filter a report using a GET query and Django `Q` objects.
- Explain how the dashboard template displays values and repeats report rows.
- Describe how dashboard-specific CSS extends the existing stylesheet.
- Test dashboard access, counts, search, navigation, and logout behavior.

## 1. Dashboard and report overview

A dashboard brings useful information together on one page. This dashboard
shows:

| Component | Purpose |
| --- | --- |
| Total Students | Count of all `Student` records |
| Male Students | Count of records with a male gender value |
| Female Students | Count of records with a female gender value |
| Gender overview | The male and female counts as percentages of all records |
| Student Report | An ordered table, optionally filtered by student ID or name |

The summary counts are calculated independently from the search. Searching
changes only the report table; it does not change the summary cards or gender
percentages.

### Gender values in this project

The current `Student` model defines gender choices as `"Male"` and `"Female"`.
The dashboard also accepts the handbook's abbreviated values `"M"` and `"F"`.
It counts either value for the corresponding group. These are exact stored
values; Django does not treat `"M"` as equivalent to `"Male"` automatically.

## 2. How the dashboard works

The dashboard follows a common Django data flow:

1. A browser requests a dashboard URL.
2. The staff access check runs before the view.
3. The view queries `Student` records and calculates its summary values.
4. The view reads an optional search term and prepares the report queryset.
5. A context dictionary passes the results to the dashboard template.
6. Django renders the template as the HTTP response.

The view prepares data; the template describes the HTML; the stylesheet
controls the page's appearance.

## 3. Understanding the dashboard view

### 3.1 Staff-only access

The dashboard keeps the existing helper and decorator:

```python
def staff_check(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(staff_check, login_url="login")
def staff_dashboard(request):
    ...
```

Both conditions must be true: the user must be authenticated and have
Django's `is_staff` flag enabled. The decorator redirects users who fail the
check to the existing login route. Do not remove the helper or decorator.

### 3.2 Counting students

```python
total_students = Student.objects.count()
male_students = Student.objects.filter(gender__in=("M", "Male")).count()
female_students = Student.objects.filter(gender__in=("F", "Female")).count()
```

- `Student` is the model for student records.
- `objects` is its manager for database queries.
- `count()` returns the number of records in the queryset.
- `filter()` narrows a queryset to records matching a condition.
- `gender__in` matches any of the listed exact values.

The total and gender counts are computed before the report search is applied,
so they always describe the whole database.

### 3.3 Calculating percentages safely

```python
male_percent = male_students / total_students * 100 if total_students else 0
female_percent = (
    female_students / total_students * 100 if total_students else 0
)
```

The general formula is:

```text
percentage = (part / whole) * 100
```

The conditional expression calculates a percentage only when the total is
nonzero. With no student records, each percentage is `0`, avoiding division
by zero.

### 3.4 Reading and applying a search

```python
query = request.GET.get("q", "").strip()
students = Student.objects.all().order_by("last_name", "first_name")

if query:
    students = students.filter(
        Q(student_id__icontains=query)
        | Q(first_name__icontains=query)
        | Q(last_name__icontains=query)
    )
```

- `request.GET` contains parameters submitted in the URL.
- `get("q", "")` reads the `q` parameter or returns an empty string.
- `strip()` removes leading and trailing spaces.
- `all()` starts with all students.
- `order_by()` sorts by last name, then first name.
- `Q` objects allow conditions to be combined with `|`, meaning OR.
- `__icontains` is a case-insensitive partial match.

For example, a search can match a student ID, first name, or last name.
An empty search leaves the report unfiltered.

### 3.5 Passing data to the template

The view puts its results into a context dictionary:

```python
context = {
    "total_students": total_students,
    "male_students": male_students,
    "female_students": female_students,
    "male_percent": male_percent,
    "female_percent": female_percent,
    "students": students,
    "query": query,
}
return render(request, "registration/dashboard.html", context)
```

Each dictionary key is available to the template. The key must match the
template variable spelling. For example, `"male_students"` is displayed with
`{{ male_students }}`.

## 4. Understanding the dashboard template

### 4.1 Loading static files

```django
{% load static %}
<link rel="stylesheet" href="{% static 'registration/style.css' %}">
```

`{% load static %}` enables the static-file template tag. The path resolves
to the existing stylesheet at
`registration/static/registration/style.css`.

### 4.2 Displaying values and percentages

```django
<p class="summary-number">{{ total_students }}</p>
<strong>{{ male_students }} ({{ male_percent|floatformat:1 }}%)</strong>
```

Double curly braces display values passed in the view context. The
`floatformat:1` filter formats a percentage to one decimal place.

The bar width is dynamic:

```django
<div class="bar-fill male-bar" style="width: {{ male_percent }}%;"></div>
```

The template supplies the percentage; CSS supplies the bar's color, height,
shape, and background track.

### 4.3 Searching and clearing the report

The report search uses a GET form targeting the project's root-level
`dashboard` URL name:

```django
<form method="get" action="{% url 'dashboard' %}" class="search-form">
    <label for="student-search">Search by student ID or name</label>
    <input id="student-search" name="q" value="{{ query }}" type="text">
    <button type="submit">Search</button>
    <a class="clear-search" href="{% url 'dashboard' %}">Clear</a>
</form>
```

The `name="q"` parameter matches `request.GET.get("q")` in the view.
`value="{{ query }}"` keeps the current search text in the input. The Clear
link opens the same dashboard without a query parameter.

### 4.4 Rendering report rows and empty results

```django
{% for student in students %}
<tr>
    <td>{{ student.student_id }}</td>
    <td>{{ student.first_name }}</td>
    <td>{{ student.last_name }}</td>
    <td>{{ student.gender }}</td>
    <td>{{ student.date_of_birth }}</td>
    <td>{{ student.contact_no }}</td>
</tr>
{% empty %}
<tr>
    <td colspan="6" class="empty-message">No student records found.</td>
</tr>
{% endfor %}
```

The loop creates one row for each matching student. The `{% empty %}` branch
is used when the database or search result contains no records.

### 4.5 Preserving navigation and logout

The Student Directory link uses the existing `student_list` route name.
Logout remains a POST form with a CSRF token:

```django
<form method="post" action="{% url 'logout' %}">
    {% csrf_token %}
    <button type="submit">Log Out</button>
</form>
```

The method and CSRF token are part of the existing logout behavior and should
be preserved.

## 5. Dashboard URLs

The project exposes the same protected dashboard view at two URLs:

| URL | Route name | Defined in |
| --- | --- | --- |
| `/registration/dashboard/` | `staff_dashboard` | `registration/urls.py` |
| `/dashboard/` | `dashboard` | `student_registration/urls.py` (default after login) |

The template's search and Clear actions use the root-level `dashboard` name.
Successful login also redirects to `/dashboard/`. The
`/registration/dashboard/` route remains available as an alternate URL to the
same view and access protection. No duplicate dashboard view or
authentication workflow is needed.

## 6. Understanding the stylesheet

The existing `style.css` contains general rules used across registration
pages, including rules for the body, headings, links, tables, buttons, and
form controls. Dashboard-specific selectors are added without removing those
rules.

| Selector | Dashboard role |
| --- | --- |
| `.dashboard-container` | Centers content and limits its width |
| `.dashboard-header` | Lays out the title, welcome message, and logout form |
| `.summary-grid` and `.summary-card` | Arrange and style the summary cards |
| `.gender-row`, `.bar-track`, `.bar-fill` | Present the gender comparison |
| `.search-form` | Arranges the report search controls |
| `.table-wrapper` | Allows horizontal scrolling for a wide table |
| `.empty-message` | Styles the no-results message |

The `@media (max-width: 700px)` rule stacks the header and cards on smaller
screens. Keep dashboard styling in the external stylesheet; the inline bar
width is dynamic data from the view.

## 7. Testing the dashboard

From the folder containing `manage.py`, run:

```text
python manage.py runserver
```

Sign in using an account whose `is_staff` property is true. The dashboard
routes are:

```text
http://127.0.0.1:8000/dashboard/
http://127.0.0.1:8000/registration/dashboard/
```

Check the following:

- The total count matches the number of `Student` records.
- Male and female counts include the exact supported values for each group.
- With no students, the counts and percentages are zero and the page loads.
- Search works for complete or partial student IDs and names, regardless of
  letter case.
- Search results do not change the summary counts.
- A nonmatching search displays the empty-state message; Clear restores the
  full report.
- The Student Directory link opens the existing directory.
- The logout form submits as POST and includes its CSRF token.
- Anonymous and non-staff users cannot view the dashboard.

Automated checks:

```text
python manage.py check
python manage.py test
```

## 8. Common issues

| Symptom | What to check |
| --- | --- |
| `/dashboard/` returns 404 | Confirm `path('dashboard/', staff_dashboard, name='dashboard')` exists in the project URL configuration and restart the server if needed. |
| `/registration/dashboard/` returns 404 | Confirm the `registration/` include and the `dashboard/` route in `registration/urls.py`. |
| Dashboard redirects to login | This is expected for anonymous users. Sign in with an authorized staff account. |
| Gender count is unexpected | Check the stored `gender` value. The dashboard counts `"M"`/`"Male"` and `"F"`/`"Female"` exactly. |
| Search returns no matches | Check that the form uses `name="q"` and that the model fields are spelled correctly. |
| A template variable is blank | Match its spelling to the corresponding context key in the view. |
| `NoReverseMatch` appears | Use the actual existing URL name. The report form uses `staff_dashboard`; the project alias is named `dashboard`. |
| Styles do not appear | Check `{% load static %}`, the static path, and the stylesheet file location; then refresh the page. |
| Division by zero occurs | Keep the zero-total conditional in both percentage calculations. |

## 9. Reflection questions

1. Why are the summary counts calculated before the search is applied?
2. What does the conditional expression protect against?
3. Why are `Q` objects and the OR operator useful for searching multiple fields?
4. How does a GET search differ from the POST logout form?
5. Why should the staff access helper and decorator remain in place?
6. Why should dashboard CSS be appended instead of replacing existing rules?
7. Why can a dashboard have more than one URL without duplicating its view?
