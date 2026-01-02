from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import AdminActivityLog

User = get_user_model()

class Command(BaseCommand):
    help = 'Set up initial admin users for the system'

    def handle(self, *args, **options):
        # Create Super Admin
        super_admin, created = User.objects.get_or_create(
            username='SuperAdmin',
            defaults={
                'email': 'superadmin@realestate.com',
                'first_name': 'Super',
                'last_name': 'Admin',
                'user_type': 'super_admin',
                'is_admin_active': True,
                'is_staff': True,
                'is_superuser': True,
                'admin_permissions': {
                    'manage_users': True,
                    'manage_properties': True,
                    'manage_payments': True,
                    'manage_premium': True,
                    'manage_admins': True,
                    'system_settings': True,
                    'view_logs': True,
                    'delete_data': True,
                    'export_data': True,
                    'manage_content': True,
                }
            }
        )

        if created:
            super_admin.set_password('@Phulasi923')
            super_admin.save()
            self.stdout.write(
                self.style.SUCCESS(f'Super Admin created: {super_admin.username}')
            )

            # Log the creation
            AdminActivityLog.objects.create(
                admin=super_admin,
                action_type='create',
                description='Super Admin account created during system setup',
                target_model='User',
                target_id=super_admin.id,
                ip_address='127.0.0.1'
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Super Admin already exists: {super_admin.username}')
            )

        # Create Normal Admin
        normal_admin, created = User.objects.get_or_create(
            username='RENAdmin',
            defaults={
                'email': 'normaladmin@realestate.com',
                'first_name': 'Normal',
                'last_name': 'Admin',
                'user_type': 'admin',
                'is_admin_active': True,
                'is_staff': True,
                'admin_permissions': {
                    'manage_users': False,
                    'manage_properties': True,
                    'manage_payments': False,
                    'manage_premium': False,
                    'manage_admins': False,
                    'system_settings': False,
                    'view_logs': False,
                    'delete_data': False,
                    'export_data': False,
                    'manage_content': False,
                }
            }
        )

        if created:
            normal_admin.set_password('@Phulasi923')
            normal_admin.save()
            self.stdout.write(
                self.style.SUCCESS(f'Normal Admin created: {normal_admin.username}')
            )

            # Log the creation
            AdminActivityLog.objects.create(
                admin=super_admin,
                action_type='create',
                description='Normal Admin account created during system setup',
                target_model='User',
                target_id=normal_admin.id,
                ip_address='127.0.0.1'
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Normal Admin already exists: {normal_admin.username}')
            )

        self.stdout.write(
            self.style.SUCCESS('\nAdmin Setup Complete!')
        )
        self.stdout.write('Super Admin Login: SuperAdmin / @Phulasi923')
        self.stdout.write('Normal Admin Login: RENAdmin / @Phulasi923')
        self.stdout.write('\nURLs:')
        self.stdout.write('Super Admin: http://127.0.0.1:8000/real-admin/')
        self.stdout.write('Normal Admin: http://127.0.0.1:8000/net-admin/')
