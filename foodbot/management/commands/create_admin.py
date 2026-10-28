
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a Django superuser from environment variables"

    def handle(self, *args, **options):
        User = get_user_model()

        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

        if not username or not password:
            self.stderr.write(
                "DJANGO_SUPERUSER_USERNAME жана "
                "DJANGO_SUPERUSER_PASSWORD талап кылынат."
            )
            return

        user = User.objects.filter(username=username).first()

        if user:
            self.stdout.write("Администратор мурда эле бар.")
            return

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )

        self.stdout.write(
            self.style.SUCCESS("Администратор ийгиликтүү түзүлдү.")
        )
x