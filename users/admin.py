from django.contrib import admin
from .models import ExtendUser
from users.models import Quiz, Question, Answer, UserProgress, Course, Student, Lesson, Forum, Topic, Post, Comment

from django.apps import apps
# Register your models here.
admin.site.register(ExtendUser)

app = apps.get_app_config('graphql_auth')

for model_name, model in app.models.items() :
    admin.site.register(model)
    from django.contrib import admin

# Register your models here.
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'enrolled_courses')
    
class LessonAdmin(admin.ModelAdmin):
    list_display = ('course', 'title', 'order')

class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'total_lessons')

class UserProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'completed_lessons', 'quiz_50_percent_done', 'quiz_completed', 'passed_quiz')

class QuizAdmin(admin.ModelAdmin):
    list_display = ('course', 'title', 'is_midterm')

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'text')

class AnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'text', 'is_correct')

admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Student)
admin.site.register(Course)
admin.site.register(UserProgress)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(Forum)
admin.site.register(Topic)
admin.site.register(Post)
admin.site.register(Comment)
