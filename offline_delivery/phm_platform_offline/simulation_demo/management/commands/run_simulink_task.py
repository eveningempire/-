from django.core.management.base import BaseCommand, CommandError
from simulation_demo.worker import execute_task


class Command(BaseCommand):
    help = "Execute one queued customer Simulink fault injection task."

    def add_arguments(self, parser):
        parser.add_argument("task_id")

    def handle(self, *args, **options):
        try:
            executed = execute_task(options["task_id"])
        except Exception as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write("completed" if executed else "task already claimed or not queued")
