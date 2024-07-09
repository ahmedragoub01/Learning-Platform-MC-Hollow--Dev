import graphene
from graphene_django.types import DjangoObjectType
from .models import Student, Course, Lesson, Payment, UserProgress, ExtendUser, Quiz, Question, Answer, Forum, Topic, Post, Comment
from graphql_auth import mutations
from graphql_auth.schema import UserQuery, MeQuery
from graphql_auth.models import UserStatus
from django.contrib.auth import get_user_model
from graphql_jwt.utils import jwt_decode
from graphql_jwt.decorators import login_required
from graphql import GraphQLError
from django.conf import settings
import stripe
import json

stripe.api_key = settings.STRIPE_SECRET_KEY

class QuestionType(DjangoObjectType):
    class Meta:
        model = Question
        fields = ('id', 'text', 'answer_set')
        
class TopicType(DjangoObjectType):
    class Meta:
        model = Topic
        
class  PostType(DjangoObjectType):
    class Meta:
        model = Post



class AnswerType(DjangoObjectType):
    class Meta:
        model = Answer

class QuizType(DjangoObjectType):
    questions = graphene.List(QuestionType)

    class Meta:
        model = Quiz
        fields = ('id', 'title', 'questions')

    def resolve_questions(self, info):
        return self.questions.all()

class CourseType(DjangoObjectType):
    class Meta:
        model = Course

class StudentType(DjangoObjectType):
    class Meta:
        model = Student

class LessonType(DjangoObjectType):
    class Meta:
        model = Lesson

class PaymentType(DjangoObjectType):
    class Meta:
        model = Payment

class UserProgressType(DjangoObjectType):
    progress_percentage = graphene.Float()

    class Meta:
        model = UserProgress

    def resolve_progress_percentage(self, info):
        return self.progress_percentage()

class CreatePayment(graphene.Mutation):
    class Arguments:
        courseId = graphene.Int(required=True)
        token = graphene.String(required=True)
        amount = graphene.Int(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @classmethod
    @login_required
    def mutate(cls, root, info, courseId, token, amount):
        try:
            User = get_user_model()
            jwt_token = info.context.headers.get('Authorization')
            if jwt_token is None:
                raise GraphQLError('Authorization header missing.')

            jwt_token = jwt_token[4:]  # Remove 'JWT ' prefix
            payload = jwt_decode(jwt_token)
            username = payload['username']

            user = User.objects.get(username=username)
            if user is None:
                raise GraphQLError('User not found.')

            # Create a Stripe charge
            charge = stripe.Charge.create(
                amount=amount * 100,  # Stripe uses cents
                currency='usd',
                description=f'Course purchase for course ID: {courseId}',
                source=token,
            )

            # Create payment record
            payment = Payment.objects.create(
                user=user,
                stripe_charge_id=charge.id,
                amount=amount,
                success=True
            )

            # Enroll user in course
            course = Course.objects.get(id=courseId)
            student, created = Student.objects.get_or_create(user=user)
            UserProgress.objects.create(student=student, course=course)

            return CreatePayment(success=True, message='Payment successful and course enrolled.')
        except stripe.error.StripeError as e:
            return CreatePayment(success=False, message=f'Stripe error: {str(e)}')
        except User.DoesNotExist:
            return CreatePayment(success=False, message='User does not exist.')
        except Exception as e:
            return CreatePayment(success=False, message=f'Error: {str(e)}')

class Query(graphene.ObjectType):
    all_courses = graphene.List(CourseType)
    course_details = graphene.Field(CourseType, id=graphene.Int(required=True))
    my_courses = graphene.List(CourseType)
    course_lessons = graphene.List(LessonType, course_id=graphene.Int(required=True))
    user_progress = graphene.List(UserProgressType, student_id=graphene.Int(required=True))
    user_percentage = graphene.Field(UserProgressType, student_id=graphene.Int(required=True), course_id=graphene.Int(required=True))
    student_id = graphene.Int(username=graphene.String(required=True))
    completed_courses_with_quiz = graphene.List(CourseType)
    quiz_details = graphene.Field(QuizType, course_id=graphene.Int(required=True))

    def resolve_quiz_details(self, info, course_id):
        try:
            return Quiz.objects.get(course_id=course_id)
        except Quiz.DoesNotExist:
            raise GraphQLError("Quiz matching query does not exist.")
    
    
    def resolve_completed_courses_with_quiz(self, info):
        User = get_user_model()
        jwt_token = info.context.headers.get('Authorization')
        jwt_token = jwt_token[4:]
        payload = jwt_decode(jwt_token)
        username = payload['username']
        user = User.objects.get(username=username)
        student = Student.objects.get(user=user)
        completed_courses = []

        for progress in UserProgress.objects.filter(student=student):
            if progress.progress_percentage() == 100:
                completed_courses.append(progress.course)

        return completed_courses

    def resolve_student_id(self, info, username):
        try:
            user = ExtendUser.objects.get(username=username)
            student = Student.objects.get(user=user)
            return student.id
        except (ExtendUser.DoesNotExist, Student.DoesNotExist):
            return None

    def resolve_all_courses(self, info):
        return Course.objects.all()

    def resolve_course_details(self, info, id):
        return Course.objects.get(id=id)

    def resolve_my_courses(self, info):
        User = get_user_model()
        jwt_token = info.context.headers.get('Authorization')
        jwt_token = jwt_token[4:]
        payload = jwt_decode(jwt_token)
        username = payload['username']
        user = User.objects.get(username=username)
        student = Student.objects.get(user=user)
        return student.enrolled_courses.all()

    def resolve_course_lessons(self, info, course_id):
        return Lesson.objects.filter(course_id=course_id)

    def resolve_user_progress(self, info, student_id):
        return UserProgress.objects.filter(student_id=student_id)

    def resolve_user_percentage(self, info, student_id, course_id):
        return UserProgress.objects.get(student__id=student_id, course__id=course_id)

class CourseDetailsType(DjangoObjectType):
    progress = graphene.Field(graphene.List(graphene.Int))

    class Meta:
        model = Course

    def resolve_progress(self, info):
        User = get_user_model()
        jwt_token = info.context.headers.get('Authorization')
        jwt_token = jwt_token[4:]
        payload = jwt_decode(jwt_token)
        username = payload['username']
        user = User.objects.get(username=username)
        student = Student.objects.get(user=user)
        progress = UserProgress.objects.filter(student=student, course=self).first()
        if progress:
            return [lesson.id for lesson in progress.completed_lessons.all()]
        return []

class Register(mutations.Register):
    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        first_name = graphene.String(required=True)
        last_name = graphene.String(required=True)
        password1 = graphene.String(required=True)
        password2 = graphene.String(required=True)

    @classmethod
    def perform_mutation(cls, root, info, **kwargs):
        User = get_user_model()
        user = User.objects.create(
            username=kwargs['username'],
            email=kwargs['email'],
            first_name=kwargs['first_name'],
            last_name=kwargs['last_name']
        )
        user.set_password(kwargs['password1'])
        user.save()
        user_status = UserStatus.objects.create(user=user)
        user_status.send_activation_email()
        return cls(success=True)


class CreatePost(graphene.Mutation):
    class Arguments:
        topic_id = graphene.Int(required=True)
        message = graphene.String(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    post = graphene.Field(PostType)

    @classmethod
    @login_required
    def mutate(cls, root, info, topic_id, message):
        try:
            User = get_user_model()
            jwt_token = info.context.headers.get('Authorization')
            if jwt_token is None:
                raise GraphQLError('Authorization header missing.')

            jwt_token = jwt_token[4:]  # Remove 'JWT ' prefix
            payload = jwt_decode(jwt_token)
            username = payload['username']
            user = User.objects.get(username=username)

            student = Student.objects.get(user=user)
            topic = Topic.objects.get(id=topic_id)

            new_post = Post.objects.create(
                topic=topic,
                message=message,
                created_by=student
            )

            return CreatePost(success=True, message="Post created successfully.", post=new_post)
        except Topic.DoesNotExist:
            return CreatePost(success=False, message="Topic does not exist.")
        except Exception as e:
            return CreatePost(success=False, message=f"Error: {str(e)}")
class UpdateProgress(graphene.Mutation):
    class Arguments:
        course_id = graphene.Int(required=True)
        lesson_id = graphene.Int(required=True)
        student_id = graphene.Int(required=True)  # New argument

    success = graphene.Boolean()
    message = graphene.String()

    @classmethod
    @login_required
    def mutate(cls, root, info, course_id, lesson_id, student_id):
        try:
            User = get_user_model()
            jwt_token = info.context.headers.get('Authorization')
            if jwt_token is None:
                raise GraphQLError('Authorization header missing.')

            jwt_token = jwt_token[4:]  # Remove 'JWT ' prefix
            payload = jwt_decode(jwt_token)
            username = payload['username']
            user = User.objects.get(username=username)
            if user is None:
                raise GraphQLError('User not found.')

            # Fetch student and user progress
            student = Student.objects.get(id=student_id)
            course = Course.objects.get(id=course_id)
            lesson = Lesson.objects.get(id=lesson_id)

            user_progress = UserProgress.objects.get(student=student, course=course)

            if lesson in user_progress.completed_lessons.all():
                return cls(success=False, message="Lesson already completed")

            user_progress.completed_lessons.add(lesson)
            user_progress.save()

            return cls(success=True, message="Lesson marked as completed")
        except User.DoesNotExist:
            return cls(success=False, message='User does not exist.')
        except Student.DoesNotExist:
            return cls(success=False, message='Student does not exist.')
        except Course.DoesNotExist:
            return cls(success=False, message='Course does not exist.')
        except Lesson.DoesNotExist:
            return cls(success=False, message='Lesson does not exist.')
        except UserProgress.DoesNotExist:
            return cls(success=False, message='User progress does not exist.')
        except Exception as e:
            return cls(success=False, message=f'Error: {str(e)}')

class SubmitQuiz(graphene.Mutation):
    class Arguments:
        quiz_id = graphene.Int(required=True)
        answers = graphene.String(required=True)  # Change this to String

    success = graphene.Boolean()
    message = graphene.String()

    @classmethod
    @login_required
    def mutate(cls, root, info, quiz_id, answers):
        User = get_user_model()
        jwt_token = info.context.headers.get('Authorization')
        jwt_token = jwt_token[4:]
        payload = jwt_decode(jwt_token)
        username = payload['username']
        user = User.objects.get(username=username)
        student = Student.objects.get(user=user)

        try:
            quiz = Quiz.objects.get(id=quiz_id)
            # Parse the answers string back into a dictionary
            answers_dict = json.loads(answers)
            correct_answers = 0
            for question in quiz.questions.all():
                selected_answer_id = answers_dict.get(f'question-{question.id}')
                if selected_answer_id is not None:
                    selected_answer = Answer.objects.get(id=selected_answer_id)
                    if selected_answer.is_correct:
                        correct_answers += 1

            if correct_answers == quiz.questions.count():
                user_progress = UserProgress.objects.get(student=student, course=quiz.course)
                user_progress.quiz_completed = True
                user_progress.save()
                return SubmitQuiz(success=True, message="Quiz passed successfully.")
            else:
                return SubmitQuiz(success=False, message="Not all answers were correct.")

        except Quiz.DoesNotExist:
            return SubmitQuiz(success=False, message="Quiz does not exist.")
        except json.JSONDecodeError:
            return SubmitQuiz(success=False, message="Invalid answer format.")
        except Exception as e:
            return SubmitQuiz(success=False, message=f"Error: {str(e)}")
class CreateTopic(graphene.Mutation):
    class Arguments:
        forum_id = graphene.Int(required=True)
        title = graphene.String(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    topic = graphene.Field(TopicType)

    @classmethod
    @login_required
    def mutate(cls, root, info, forum_id, title):
        try:
            User = get_user_model()
            jwt_token = info.context.headers.get('Authorization')
            if jwt_token is None:
                raise GraphQLError('Authorization header missing.')

            jwt_token = jwt_token[4:]  # Remove 'JWT ' prefix
            payload = jwt_decode(jwt_token)
            username = payload['username']
            user = User.objects.get(username=username)

            student = Student.objects.get(user=user)
            forum = Forum.objects.get(id=forum_id)

            new_topic = Topic.objects.create(
                forum=forum,
                title=title,
                created_by=student
            )

            return CreateTopic(success=True, message="Topic created successfully.", topic=new_topic)
        except Forum.DoesNotExist:
            return CreateTopic(success=False, message="Forum does not exist.")
        except Exception as e:
            return CreateTopic(success=False, message=f"Error: {str(e)}")

class AuthMutation(graphene.ObjectType):
    register = Register.Field()
    verify_account = mutations.VerifyAccount.Field()
    token_auth = mutations.ObtainJSONWebToken.Field()
    update_account = mutations.UpdateAccount.Field()
    resend_activation_email = mutations.ResendActivationEmail.Field()
    send_password_reset_email = mutations.SendPasswordResetEmail.Field()
    password_reset = mutations.PasswordReset.Field()
    password_change = mutations.PasswordChange.Field()
    archive_account = mutations.ArchiveAccount.Field()
    delete_account = mutations.DeleteAccount.Field()
    update_progress = UpdateProgress.Field()
    submit_quiz = SubmitQuiz.Field()
    create_payment = CreatePayment.Field()  # Added CreatePayment mutation
    create_topic = CreateTopic.Field()
    create_post = CreatePost.Field()
    

class Mutation(AuthMutation, graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)
