from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Course, UserProgress
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Quiz, Question, Answer, UserProgress
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.shortcuts import render, redirect
from django.views import View
from .forms import RegisterForm
from django.shortcuts import render
import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import requests
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from graphql_auth.utils import get_token_paylod
from graphql_auth.constants import TokenAction
from graphql_auth.models import UserStatus
from django.http import HttpResponse
from .models import Student

User = get_user_model()


@login_required
def enroll_in_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    student = request.user.student
    progress, created = UserProgress.objects.get_or_create(student=student, course=course)
    
    if created:
        # Logic for new enrollment
        pass

    return redirect('course_detail', course_id=course.id)

def update_progress(student, course, lessons_completed):
    progress, created = UserProgress.objects.get_or_create(student=student, course=course)
    progress.completed_lessons = lessons_completed

    # Check if it's time to add a quiz
    if not progress.quiz_50_percent_done and progress.progress_percentage >= 50:
        progress.quiz_50_percent_done = True
        # Add logic to unlock the 50% quiz for the student

    if progress.progress_percentage == 100 and not progress.quiz_completed:
        progress.quiz_completed = True
        # Add logic to unlock the final quiz for the student

    progress.save()



@login_required
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.question_set.all()

    if request.method == 'POST':
        score = 0
        for question in questions:
            selected_answer = request.POST.get(f'question_{question.id}')
            if selected_answer:
                answer = Answer.objects.get(id=selected_answer)
                if answer.is_correct:
                    score += 1
        if score >= (len(questions) / 2):  # Adjust passing score as needed
            # Mark quiz as passed
            progress = UserProgress.objects.get(student=request.user.student, course=quiz.course)
            progress.passed_quiz = True
            progress.save()
            # Trigger certificate generation and sending
            send_certificate(request.user, quiz.course)
            return redirect('quiz_success_page')  # Redirect to a success page
        else:
            return redirect('quiz_failure_page')  # Redirect to a failure page

    return render(request, 'take_quiz.html', {'quiz': quiz, 'questions': questions})

from .models import Course

def course_detail(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    return render(request, 'course_detail.html', {'course': course})



def generate_certificate(user, course):
    certificate_name = f"{user.username}_certificate_{course.title}.pdf"
    file_path = f"/path/to/save/{certificate_name}"

    c = canvas.Canvas(file_path, pagesize=letter)
    c.drawString(100, 750, f"Certificate of Completion")
    c.drawString(100, 700, f"This certifies that {user.username}")
    c.drawString(100, 650, f"has successfully completed the course {course.title}")
    c.save()

    return file_path

from django.core.mail import EmailMessage

def send_certificate(user, course):
    certificate_path = generate_certificate(user, course)
    email = EmailMessage(
        'Your Certificate of Completion',
        f'Congratulations {user.username}, you have completed the course {course.title}.',
        'from@example.com',
        [user.email],
    )
    email.attach_file(certificate_path)
    email.send()


class RegisterView(View):
    def get(self, request):
        form = RegisterForm()
        return render(request, 'register.html', {'form': form})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # GraphQL mutation query
            query = '''
            mutation {
              register(
                username: "%s",
                first_name: "%s",
                last_name: "%s",
                email: "%s",
                password1: "%s",
                password2: "%s"
              ) {
                success,
                errors
              }
            }
            ''' % (email, first_name, last_name, username, password, password)

            headers = {
                'Content-Type': 'application/json',
            }

            data = json.dumps({'query': query}).encode('utf-8')
            req = Request('/graphql/', data=data, headers=headers)

            try:
                response = urlopen(req)
                response_content = response.read().decode('utf-8')
                print(response_content)  # Log the raw response content
                result = json.loads(response_content)

                if result.get('data', {}).get('register', {}).get('success'):
                    return redirect('success')  # Redirect to a success page
                else:
                    errors = result.get('data', {}).get('register', {}).get('errors')
                    form.add_error(None, errors)
            except HTTPError as e:
                form.add_error(None, f'HTTPError: {e.code}')
            except URLError as e:
                form.add_error(None, f'URLError: {e.reason}')
            except json.JSONDecodeError as e:
                form.add_error(None, f'JSONDecodeError: {str(e)}')
                print(response_content)  # Log the raw response content for debugging

        return render(request, 'register.html', {'form': form})
    
@csrf_exempt
def login_view(request):
    if request.method == 'GET':
        return render(request, 'login.html')
    elif request.method == 'POST':
        data = request.POST
        query = """
            mutation tokenAuth($username: String!, $password: String!) {
                tokenAuth(username: $username, password: $password) {
                    token
                    payload
                    refreshToken
                }
            }
        """
        variables = {
            "username": data.get('username'),
            "password": data.get('password')
        }
        response = requests.post(
            '/graphql/',
            json={'query': query, 'variables': variables},
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code == 200:
            json_response = response.json()
            return JsonResponse(json_response)
        else:
            return JsonResponse({'errors': 'Failed to log in'}, status=response.status_code)
        

def activation_sent_view(request):
    return render(request, 'activation_sent.html')
from django.shortcuts import render, redirect
from django.urls import reverse
from graphql_auth.utils import get_token_paylod
from graphql_auth.constants import TokenAction
from graphql_auth.models import UserStatus
from django.contrib.auth import get_user_model
import requests

User = get_user_model()

def activate_account(request, token):
        # Decode the token and extract the username
        payload = get_token_paylod(token, TokenAction.ACTIVATION)
        print("Payload:", payload)  # Debugging line to check payload content
        username = payload.get('username')
        print(username)

        if not username:
            print('No username found in payload')

        # Fetch the user and UserStatus using the username
        user = User.objects.filter(username=username).first()

        if not user:
            print('No user found with the given username')

        user_status = UserStatus.objects.filter(user=user).first()

        if not user_status:
            print('No UserStatus found for the given user')
            return render(request, 'activation_invalid.html')

        user_status.verified = True
        user_status.save()
        return redirect('login')
from graphql_auth.decorators import login_required
from django.shortcuts import render

@login_required
def my_courses_view(request):
    user = request.user
    student = Student.objects.get(user=user)  # Assuming you have a Student model related to courses
    courses = student.enrolled_courses.all()  # Retrieve courses for the student
    return render(request, 'my_courses.html', {'courses': courses})

from .models import Lesson
def lesson_detail(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    context = {
        'lesson': lesson
    }
    return render(request, 'lesson_detail.html', context)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Forum, Topic, Post
from .forms import NewTopicForm, NewPostForm
from .models import Student

def forum_list(request):
    forums = Forum.objects.all()
    return render(request, 'forum_list.html', {'forums': forums})

def forum_detail(request, forum_id):
    forum = get_object_or_404(Forum, pk=forum_id)
    topics = forum.topic_set.all()
    return render(request, 'forum_detail.html', {'forum': forum, 'topics': topics})

@login_required
def new_topic(request, forum_id):
    forum = get_object_or_404(Forum, pk=forum_id)
    student = Student.objects.get(user=request.user)
    if request.method == 'POST':
        form = NewTopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.forum = forum
            topic.created_by = student
            topic.save()
            return redirect('forum_detail', forum_id=forum.id)
    else:
        form = NewTopicForm()
    return render(request, 'new_topic.html', {'form': form, 'forum': forum})

def topic_detail(request, topic_id):
    topic = get_object_or_404(Topic, pk=topic_id)
    posts = topic.post_set.all()
    return render(request, 'topic_detail.html', {'topic': topic, 'posts': posts})

@login_required
def new_post(request, topic_id):
    topic = get_object_or_404(Topic, pk=topic_id)
    student = Student.objects.get(user=request.user)
    if request.method == 'POST':
        form = NewPostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.topic = topic
            post.created_by = student
            post.save()
            return redirect('topic_detail', topic_id=topic.id)
    else:
        form = NewPostForm()
    return render(request, 'new_post.html', {'form': form, 'topic': topic})

