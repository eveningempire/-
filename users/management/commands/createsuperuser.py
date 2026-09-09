from django.contrib.auth.management.commands import createsuperuser
from django.core.management import CommandError
from users.models import CustomUser

class Command(createsuperuser.Command):
    help = 'Creates a superuser, prompting for a role.'

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            '--role',
            dest='role',
            default=None,
            help='Specifies the role for the superuser.',
        )

    def handle(self, *args, **options):
        # If role is not provided via command line, prompt for it interactively.
        if options.get('role') is None:
            role_choices = [choice[0] for choice in CustomUser.Role.choices]
            while True:
                role = input(f"Role ({', '.join(role_choices)}): ")
                if role in role_choices:
                    options['role'] = role
                    break
                else:
                    self.stderr.write(self.style.ERROR(f"Error: '{role}' is not a valid role."))
        
        # Store the role and username before calling super().handle()
        role = options.get('role')
        username = options.get(self.UserModel.USERNAME_FIELD)
        
        # Remove role from options to prevent super().handle() from erroring
        if 'role' in options:
            options.pop('role')
        
        # Call the original command to create the user.
        # This will handle username, email, password prompts.
        super().handle(*args, **options)
        
        # After the user is created, find them and set their role.
        # If username wasn't provided in options, get it from the most recently created user
        if not username:
            # Get the most recently created superuser (this is a fallback)
            try:
                user = self.UserModel._default_manager.filter(is_superuser=True).latest('date_joined')
                username = user.username
            except self.UserModel.DoesNotExist:
                raise CommandError("Could not find the newly created user.")
        
        try:
            user = self.UserModel._default_manager.get_by_natural_key(username)
            user.role = role
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Role for user '{username}' set to '{role}'."))
        except self.UserModel.DoesNotExist:
            # This should not happen if super().handle() was successful.
            raise CommandError(f"User '{username}' was not found. The role could not be set.")
