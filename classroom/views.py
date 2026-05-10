from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import DetailView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.http import HttpResponseRedirect, HttpResponse
from django.db.models import Q

from classroom import models
from classroom.models import (
    StudentsInClass,
    StudentMarks,
    ClassAssignment,
    SubmitAssignment,
    Student,
    Teacher
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

from django.contrib.auth.forms import PasswordChangeForm


# =========================
# AUTH
# =========================

def TeacherSignUp(request):
    user_type = 'teacher'
    registered = False

    if request.method == "POST":
        user_form = UserForm(request.POST)
        teacher_profile_form = TeacherProfileForm(request.POST)

        if user_form.is_valid() and teacher_profile_form.is_valid():
            user = user_form.save()
            user.is_teacher = True
            user.save()

            profile = teacher_profile_form.save(commit=False)
            profile.user = user
            profile.save()

            registered = True
    else:
        user_form = UserForm()
        teacher_profile_form = TeacherProfileForm()

    return render(request, 'classroom/teacher_signup.html', {
        'user_form': user_form,
        'teacher_profile_form': teacher_profile_form,
        'registered': registered,
        'user_type': user_type
    })


def StudentSignUp(request):
    user_type = 'student'
    registered = False

    if request.method == "POST":
        user_form = UserForm(request.POST)
        student_profile_form = StudentProfileForm(request.POST)

        if user_form.is_valid() and student_profile_form.is_valid():
            user = user_form.save()
            user.is_student = True
            user.save()

            profile = student_profile_form.save(commit=False)
            profile.user = user
            profile.save()

            registered = True
    else:
        user_form = UserForm()
        student_profile_form = StudentProfileForm()

    return render(request, 'classroom/student_signup.html', {
        'user_form': user_form,
        'student_profile_form': student_profile_form,
        'registered': registered,
        'user_type': user_type
    })


def SignUp(request):
    return render(request, 'classroom/signup.html', {})


def user_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user:
            login(request, user)
            return HttpResponseRedirect(reverse('home'))
        else:
            messages.error(request, "Invalid Details")
            return redirect('classroom:login')

    return render(request, 'classroom/login.html', {})


@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('home'))


# =========================
# CLASS-BASED VIEWS (FIXED MISSING ERROR)
# =========================

class StudentDetailView(LoginRequiredMixin, DetailView):
    model = Student
    context_object_name = "student"
    template_name = "classroom/student_detail_page.html"


class TeacherDetailView(LoginRequiredMixin, DetailView):
    model = Teacher
    context_object_name = "teacher"
    template_name = "classroom/teacher_detail_page.html"


# =========================
# ASSIGNMENTS (FIXED)
# =========================

@login_required
def upload_assignment(request):
    assignment_uploaded = False
    teacher = request.user.Teacher

    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES)

        if form.is_valid():
            upload = form.save(commit=False)
            upload.teacher = teacher
            upload.save()

            students = Student.objects.filter(user_student_name__teacher=teacher)
            upload.student.add(*students)

            assignment_uploaded = True
    else:
        form = AssignmentForm()

    return render(request, 'classroom/upload_assignment.html', {
        'form': form,
        'assignment_uploaded': assignment_uploaded
    })


# ✅ FIXED: Student sees actual assignments
@login_required
def class_assignment(request):
    student = request.user.Student

    assignment_list = ClassAssignment.objects.filter(student=student)

    return render(request, 'classroom/class_assignment.html', {
        'student': student,
        'assignment_list': assignment_list
    })


# ✅ FIXED: Teacher sees their assignments
@login_required
def assignment_list(request):
    teacher = request.user.Teacher

    assignments = ClassAssignment.objects.filter(teacher=teacher)

    return render(request, 'classroom/assignment_list.html', {
        'teacher': teacher,
        'assignments': assignments
    })


@login_required
def update_assignment(request, id):
    obj = get_object_or_404(ClassAssignment, id=id)
    form = AssignmentForm(request.POST or None, request.FILES or None, instance=obj)

    if form.is_valid():
        form.save()
        messages.success(request, "Assignment Updated")
        return redirect('classroom:assignment_list')

    return render(request, "classroom/update_assignment.html", {"form": form})


@login_required
def assignment_delete(request, id):
    obj = get_object_or_404(ClassAssignment, id=id)

    if request.method == "POST":
        obj.delete()
        messages.success(request, "Assignment Removed")
        return redirect('classroom:assignment_list')

    return render(request, "classroom/assignment_delete.html", {"object": obj})


# =========================
# SUBMISSION
# =========================

@login_required
def submit_assignment(request, id):
    student = request.user.Student
    assignment = get_object_or_404(ClassAssignment, id=id)
    teacher = assignment.teacher

    if request.method == 'POST':
        form = SubmitForm(request.POST, request.FILES)

        if form.is_valid():
            upload = form.save(commit=False)
            upload.teacher = teacher
            upload.student = student
            upload.submitted_assignment = assignment
            upload.save()

            return redirect('classroom:class_assignment')
    else:
        form = SubmitForm()

    return render(request, 'classroom/submit_assignment.html', {
        'form': form,
        'assignment': assignment
    })


@login_required
def submit_list(request):
    teacher = request.user.Teacher
    return render(request, 'classroom/submit_list.html', {'teacher': teacher})


# =========================
# PASSWORD
# =========================

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)

        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Password changed")
            return redirect('home')

    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'classroom/change_password.html', {'form': form})
