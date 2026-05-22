from datetime import timedelta

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from accounts.models import User
from calendar_app.models import Lesson
from students.models import ScheduleSlot, Student, Subject


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    is_active = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.pop("password", "testpass123")
        user = super()._create(model_class, *args, **kwargs)
        user.username = user.email
        user.set_password(password)
        user.save()
        return user


class SubjectFactory(DjangoModelFactory):
    class Meta:
        model = Subject

    owner = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f"과목{n}")


class StudentFactory(DjangoModelFactory):
    class Meta:
        model = Student

    owner = factory.SubFactory(UserFactory)
    name = "테스트학생"
    birth_year = 2010
    grade = "중2"
    timezone = "Asia/Seoul"
    lesson_duration_minutes = 60
    lessons_completed = 0


class ScheduleSlotFactory(DjangoModelFactory):
    class Meta:
        model = ScheduleSlot

    student = factory.SubFactory(StudentFactory)
    day_of_week = 1
    start_time = factory.LazyFunction(lambda: timezone.datetime(2000,  1, 1, 19, 0).time())
    end_time = factory.LazyFunction(lambda: timezone.datetime(2000, 1, 1, 20, 0).time())


class LessonFactory(DjangoModelFactory):
    class Meta:
        model = Lesson

    student = factory.SubFactory(StudentFactory)
    schedule_slot = None
    date = factory.LazyFunction(lambda: timezone.now().date())
    start_datetime = factory.LazyFunction(timezone.now)
    end_datetime = factory.LazyAttribute(
        lambda o: o.start_datetime + timedelta(minutes=o.student.lesson_duration_minutes)
    )
    lesson_number = factory.LazyAttribute(lambda o: o.student.lessons_completed + 1)
    status = Lesson.Status.SCHEDULED
