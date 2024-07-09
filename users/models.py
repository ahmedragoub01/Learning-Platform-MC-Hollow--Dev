from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# ExtendUser model remains unchanged
class ExtendUser(AbstractUser):
    email = models.EmailField(blank=False, max_length=255, verbose_name="email")
    first_name = models.CharField(blank=False, max_length=255, verbose_name="first_name")
    last_name = models.CharField(blank=False, max_length=255, verbose_name="last_name")

    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"

# Course model remains unchanged
class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    total_lessons = models.IntegerField()
    imageUrl = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.title

# Lesson model remains unchanged
class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    order = models.IntegerField()  # To keep track of lesson order

    def __str__(self):
        return f"{self.course.title} - {self.title}"

# Student model
class Student(models.Model):
    user = models.OneToOneField(ExtendUser, on_delete=models.CASCADE)
    enrolled_courses = models.ManyToManyField(Course, through='UserProgress')

    def __str__(self):
        return self.user.username

# UserProgress model
class UserProgress(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    completed_lessons = models.ManyToManyField(Lesson, blank=True)
    quiz_completed = models.BooleanField(default=False)

    def progress_percentage(self):
        total_lessons = Lesson.objects.filter(course=self.course).count()
        completed_count = self.completed_lessons.count()
        return (completed_count / total_lessons) * 100

    def __str__(self):
        return f"{self.student.user.username} - {self.course.title}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'course'], name='unique_user_course_progress')
        ]

# Payment model remains unchanged
class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stripe_charge_id = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.amount}"

# Quiz, Question, and Answer models remain unchanged
class Quiz(models.Model):
    course = models.OneToOneField(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    questions = models.ManyToManyField('Question', related_name='quizzes', blank=True)

    def __str__(self):
        return f"{self.course.title} - {self.title}"

# Question model
class Question(models.Model):
    text = models.TextField()

    def __str__(self):
        return self.text

# Answer model
class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

# Forum model
class Forum(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()

    def __str__(self):
        return self.title

# Topic model
class Topic(models.Model):
    forum = models.ForeignKey(Forum, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    created_by = models.ForeignKey('Student', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# Post model
class Post(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    message = models.TextField()
    created_by = models.ForeignKey('Student', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Post by {self.created_by.user.username} on {self.created_at}"

# Comment model (optional)
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    message = models.TextField()
    created_by = models.ForeignKey('Student', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Comment by {self.created_by.user.username} on {self.created_at}"
