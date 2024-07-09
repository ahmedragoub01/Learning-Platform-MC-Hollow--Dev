from django.urls import path
from .views import enroll_in_course, take_quiz
from django.views.generic import TemplateView
from .views import RegisterView, lesson_detail, login_view, activate_account, activation_sent_view, my_courses_view,course_detail
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt
from .schema import schema
from . import views

urlpatterns = [
    path('enroll/<int:course_id>/', enroll_in_course, name='enroll_in_course'),
    path('quiz/<int:quiz_id>/', take_quiz, name='take_quiz'),
    path('register/', RegisterView.as_view(), name='register'),
    path('home/', TemplateView.as_view(template_name="home.html"), name='home'),
    path('login/', login_view, name='login'),
    path('activate/<str:token>', activate_account, name='activate'),
    path('activation-sent/', activation_sent_view, name='activate'),
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True, schema=schema))),
    path('home/course/<int:course_id>/', course_detail, name='course_detail'),
    path('my-courses/',  TemplateView.as_view(template_name="my_courses.html"), name='my_courses'),
    path('my-courses/course/<int:course_id>/',  TemplateView.as_view(template_name="lesson_detail.html"), name='lesson_detail'),
    path('Quizzes/', TemplateView.as_view(template_name='take_quiz.html'), name='take_quiz'),
    path('forums/', views.forum_list, name='forum_list'),
    path('forums/<int:forum_id>/', views.forum_detail, name='forum_detail'),
    path('forums/<int:forum_id>/new/', TemplateView.as_view(template_name="new_topic.html"), name='new_topic'),
    path('topics/<int:topic_id>/', views.topic_detail, name='topic_detail'),
    path('topics/<int:topic_id>/new/', TemplateView.as_view(template_name="new_post.html"), name='new_post'),

    # Other URL patterns
]
