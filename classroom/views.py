from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import DetailView, ListView, CreateView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm

from classroom.models import (
    StudentsInClass,
    StudentMarks,
    ClassAssignment,
    SubmitAssignment,
    Student,
    Teacher,
    ClassNotice,
    MessageToTeacher
)

from classroom.forms import (
    UserForm,
    TeacherProfileForm,
    StudentProfileForm,
    MarksForm,
    MessageForm,
    NoticeForm,
    AssignmentForm,
    SubmitForm,
    TeacherProfileUpdateForm,
    StudentProfileUpdateForm
)

# =========================================================
# AUTHENTICATION
# =========================================================

def SignUp(request):
    return render(request, "classroom/signup.html")


def TeacherSignUp(request):
    user_form = UserForm(request.POST or None)
    profile_form = TeacherProfileForm(request.POST or None)

    if request.method == "POST":
        if user_form.is_valid() and profile_form.is_valid():

            user = user_form.save(commit=False)
            user.is_teacher = True
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()

            messages.success(request, "Teacher account created successfully")
            return redirect("classroom:login")

    return render(request, "classroom/teacher_signup.html", {
        "user_form": user_form,
        "teacher_profile_form": profile_form
    })


def StudentSignUp(request):
    user_form = UserForm(request.POST or None)
    profile_form = StudentProfileForm(request.POST or None)

    if request.method == "POST":
        if user_form.is_valid() and profile_form.is_valid():

            user = user_form.save(commit=False)
            user.is_student = True
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()

            messages.success(request, "Student account created successfully")
            return redirect("classroom:login")

    return render(request, "classroom/student_signup.html", {
        "user_form": user_form,
        "student_profile_form": profile_form
    })


def user_login(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(username=username, password=password)

        if user:
            login(request, user)
            return redirect("home")

        messages.error(request, "Invalid username or password")

    return render(request, "classroom/login.html")


@login_required
def user_logout(request):
    logout(request)
    return redirect("home")


# =========================================================
# DETAIL VIEWS
# =========================================================

class StudentDetailView(DetailView):
    model = Student
    template_name = "classroom/student_detail_page.html"


class TeacherDetailView(DetailView):
    model = Teacher
    template_name = "classroom/teacher_detail_page.html"


# =========================================================
# UPDATE PROFILE
# =========================================================

@login_required
def StudentUpdateView(request, pk):

    student = get_object_or_404(Student, pk=pk)

    form = StudentProfileUpdateForm(
        request.POST or None,
        request.FILES or None,
        instance=student
    )

    if form.is_valid():
        form.save()
        messages.success(request, "Student profile updated")
        return redirect("classroom:student_detail", pk=pk)

    return render(request, "classroom/student_update_page.html", {
        "form": form
    })


@login_required
def TeacherUpdateView(request, pk):

    teacher = get_object_or_404(Teacher, pk=pk)

    form = TeacherProfileUpdateForm(
        request.POST or None,
        request.FILES or None,
        instance=teacher
    )

    if form.is_valid():
        form.save()
        messages.success(request, "Teacher profile updated")
        return redirect("classroom:teacher_detail", pk=pk)

    return render(request, "classroom/teacher_update_page.html", {
        "form": form
    })


# =========================================================
# STUDENT & TEACHER LISTS
# =========================================================

@login_required
def students_list(request):

    students = Student.objects.all()

    return render(request, "classroom/students_list.html", {
        "students_list": students
    })


@login_required
def teachers_list(request):

    teachers = Teacher.objects.all()

    return render(request, "classroom/teachers_list.html", {
        "teachers_list": teachers
    })


@login_required
def class_students_list(request):

    teacher = get_object_or_404(Teacher, user=request.user)

    student_ids = StudentsInClass.objects.filter(
        teacher=teacher
    ).values_list("student_id", flat=True)

    students = Student.objects.filter(user_id__in=student_ids)

    return render(request, "classroom/class_students_list.html", {
        "class_students_list": students
    })


# =========================================================
# ADD STUDENT TO CLASS
# =========================================================

class add_student(CreateView):
    model = StudentsInClass
    fields = ["teacher", "student"]
    template_name = "classroom/add_student.html"

    def get_success_url(self):
        return "/classroom/student_added/"


def student_added(request):
    return render(request, "classroom/student_added.html")


# =========================================================
# MARKS
# =========================================================

@login_required
def add_marks(request, pk):

    student = get_object_or_404(Student, pk=pk)

    form = MarksForm(request.POST or None)

    if form.is_valid():

        marks = form.save(commit=False)
        marks.student = student
        marks.save()

        messages.success(request, "Marks added successfully")

        return redirect("classroom:student_marks_list", pk=pk)

    return render(request, "classroom/add_marks.html", {
        "form": form,
        "student": student
    })


@login_required
def student_marks_list(request, pk):

    student = get_object_or_404(Student, pk=pk)

    marks = StudentMarks.objects.filter(student=student)

    return render(request, "classroom/student_marks_list.html", {
        "student": student,
        "marks": marks
    })


@login_required
def update_marks(request, pk):

    marks = get_object_or_404(StudentMarks, pk=pk)

    form = MarksForm(
        request.POST or None,
        instance=marks
    )

    if form.is_valid():
        form.save()

        messages.success(request, "Marks updated successfully")

        return redirect(
            "classroom:student_marks_list",
            pk=marks.student.pk
        )

    return render(request, "classroom/update_marks.html", {
        "form": form
    })


class StudentAllMarksList(ListView):

    model = StudentMarks
    template_name = "classroom/all_marks_list.html"
    context_object_name = "marks"

    def get_queryset(self):
        return StudentMarks.objects.filter(
            student_id=self.kwargs["pk"]
        )


# =========================================================
# MESSAGES
# =========================================================

@login_required
def write_message(request, pk):

    teacher = get_object_or_404(Teacher, pk=pk)

    form = MessageForm(request.POST or None)

    if form.is_valid():

        message = form.save(commit=False)
        message.teacher = teacher
        message.save()

        messages.success(request, "Message sent successfully")

        return redirect("classroom:teacher_detail", pk=pk)

    return render(request, "classroom/write_message.html", {
        "form": form,
        "teacher": teacher
    })


@login_required
def messages_list(request, pk):

    teacher = get_object_or_404(Teacher, pk=pk)

    messages_data = MessageToTeacher.objects.filter(
        teacher=teacher
    )

    return render(request, "classroom/messages_list.html", {
        "messages_list": messages_data
    })


# =========================================================
# CLASS NOTICE
# =========================================================

@login_required
def add_notice(request):

    form = NoticeForm(request.POST or None)

    if form.is_valid():
        form.save()

        messages.success(request, "Notice added successfully")

        return redirect("home")

    return render(request, "classroom/add_notice.html", {
        "form": form
    })


@login_required
def class_notice(request, pk):

    student = get_object_or_404(Student, pk=pk)

    notices = ClassNotice.objects.all().order_by("-id")

    return render(request, "classroom/class_notice.html", {
        "student": student,
        "notice_list": notices
    })


# =========================================================
# ASSIGNMENTS
# =========================================================

@login_required
def upload_assignment(request):

    teacher = get_object_or_404(
        Teacher,
        user=request.user
    )

    form = AssignmentForm(
        request.POST or None,
        request.FILES or None
    )

    if form.is_valid():

        assignment = form.save(commit=False)

        assignment.teacher = teacher

        assignment.save()

        form.save_m2m()

        messages.success(
            request,
            "Assignment uploaded successfully"
        )

        return redirect("classroom:assignment_list")

    return render(
        request,
        "classroom/upload_assignment.html",
        {
            "form": form
        }
    )

@login_required
def class_assignment(request):

    assignments = ClassAssignment.objects.all()

    return render(request, "classroom/class_assignment.html", {
        "assignment_list": assignments
    })


@login_required
def assignment_list(request):

    assignments = ClassAssignment.objects.all()

    return render(request, "classroom/assignment_list.html", {
        "assignment_list": assignments
    })


@login_required
def update_assignment(request, id):

    assignment = get_object_or_404(ClassAssignment, id=id)

    form = AssignmentForm(
        request.POST or None,
        request.FILES or None,
        instance=assignment
    )

    if form.is_valid():
        form.save()

        messages.success(request, "Assignment updated successfully")

        return redirect("classroom:assignment_list")

    return render(request, "classroom/update_assignment.html", {
        "form": form
    })


@login_required
def assignment_delete(request, id):

    assignment = get_object_or_404(ClassAssignment, id=id)

    assignment.delete()

    messages.success(request, "Assignment deleted successfully")

    return redirect("classroom:assignment_list")


@login_required
def submit_assignment(request, id):

    assignment = get_object_or_404(ClassAssignment, id=id)

    form = SubmitForm(
        request.POST or None,
        request.FILES or None
    )

    if form.is_valid():

        submit = form.save(commit=False)
        submit.assignment = assignment
        submit.save()

        messages.success(request, "Assignment submitted successfully")

        return redirect("classroom:class_assignment")

    return render(request, "classroom/submit_assignment.html", {
        "form": form,
        "assignment": assignment
    })


@login_required
def submit_list(request):

    submissions = SubmitAssignment.objects.all()

    return render(request, "classroom/submit_list.html", {
        "submit_list": submissions
    })


# =========================================================
# PASSWORD CHANGE
# =========================================================

@login_required
def change_password(request):

    if request.method == "POST":

        form = PasswordChangeForm(request.user, request.POST)

        if form.is_valid():

            user = form.save()

            update_session_auth_hash(request, user)

            messages.success(request, "Password changed successfully")

            return redirect("home")

    else:
        form = PasswordChangeForm(request.user)

    return render(request, "classroom/change_password.html", {
        "form": form
    })
