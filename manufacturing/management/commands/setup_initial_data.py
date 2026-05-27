"""
Management command to populate initial data:
- Manufacturing process stages (in order)
- Material categories
- Item types for orders
- Demo admin user
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

PROCESS_STAGES = [
    (1,  'DESIGN',           'Design & Specification',    'Customer requirements, sketch, and design approval.'),
    (2,  'WAX_CARVING',      'Wax Carving / CAD Modeling','Wax model carved or CAD model prepared for casting.'),
    (3,  'INVESTMENT',       'Investment & Burnout',       'Wax invested in plaster; burned out in kiln.'),
    (4,  'CASTING',          'Metal Casting',              'Molten metal poured into the investment mold.'),
    (5,  'FILING',           'Filing & Sprue Removal',    'Sprues cut off; rough edges filed smooth.'),
    (6,  'POLISHING',        'Polishing & Cleaning',      'Progressive polishing to required finish.'),
    (7,  'STONE_SETTING',    'Stone Setting',              'Gemstones set according to design specifications.'),
    (8,  'QUALITY_CHECK',    'Quality Control Check',     'Dimensional, weight, and finish inspection.'),
    (9,  'PLATING',          'Plating & Finishing',       'Gold plating, rhodium, or other surface finish applied.'),
    (10, 'FINAL_INSPECTION', 'Final Inspection',           'Final QC sign-off before packaging.'),
    (11, 'PACKAGING',        'Packaging & Delivery Ready','Piece packaged, documented, ready for customer.'),
]

MATERIAL_CATEGORIES = [
    ('Gold',       'Precious metal - gold alloys'),
    ('Silver',     'Precious metal - silver alloys'),
    ('Platinum',   'Precious metal - platinum alloys'),
    ('Gemstones',  'Diamonds, rubies, emeralds, sapphires, etc.'),
    ('Chemicals',  'Acids, polishing compounds, plating solutions'),
    ('Tools',      'Consumable tools and equipment parts'),
    ('Packaging',  'Boxes, pouches, certificates, tags'),
    ('Other',      'Miscellaneous materials'),
]

ITEM_TYPES = [
    'Ring', 'Necklace', 'Bracelet', 'Earring', 'Pendant',
    'Bangle', 'Chain', 'Brooch', 'Anklet', 'Custom',
]


class Command(BaseCommand):
    help = 'Set up initial data: process stages, categories, item types, admin user'

    def add_arguments(self, parser):
        parser.add_argument('--admin-password', default='admin123', help='Password for the admin user')
        parser.add_argument('--skip-demo-user', action='store_true', help='Skip creating demo users')

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Setting up initial data...'))

        self._setup_process_stages()
        self._setup_material_categories()
        self._setup_item_types()

        if not options['skip_demo_user']:
            self._setup_demo_users(options['admin_password'])

        self.stdout.write(self.style.SUCCESS('\nInitial data setup complete!'))
        self.stdout.write('')
        self.stdout.write('  Admin login: admin / ' + options['admin_password'])
        self.stdout.write('  Manager login: manager / manager123')
        self.stdout.write('  Worker login: worker / worker123')
        self.stdout.write('')
        self.stdout.write('  Run the server: python manage.py runserver')

    def _setup_process_stages(self):
        from manufacturing.models import ProcessStage
        created = 0
        for order_num, code, name, description in PROCESS_STAGES:
            stage, is_new = ProcessStage.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'order_number': order_num,
                    'description': description,
                    'is_active': True,
                }
            )
            if not is_new:
                stage.order_number = order_num
                stage.name = name
                stage.description = description
                stage.save()
            else:
                created += 1
        self.stdout.write(f'  Process stages: {created} created, {len(PROCESS_STAGES) - created} already existed')

    def _setup_material_categories(self):
        from inventory.models import MaterialCategory
        created = 0
        for name, description in MATERIAL_CATEGORIES:
            _, is_new = MaterialCategory.objects.get_or_create(
                name=name,
                defaults={'description': description}
            )
            if is_new:
                created += 1
        self.stdout.write(f'  Material categories: {created} created')

    def _setup_item_types(self):
        from orders.models import ItemType
        created = 0
        for name in ITEM_TYPES:
            _, is_new = ItemType.objects.get_or_create(name=name)
            if is_new:
                created += 1
        self.stdout.write(f'  Item types: {created} created')

    def _setup_demo_users(self, admin_password):
        demo_users = [
            {
                'username': 'admin',
                'first_name': 'System',
                'last_name': 'Administrator',
                'email': 'admin@pvdgold.com',
                'role': 'admin',
                'employee_id': 'EMP001',
                'department': 'Management',
                'password': admin_password,
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'username': 'manager',
                'first_name': 'Production',
                'last_name': 'Manager',
                'email': 'manager@pvdgold.com',
                'role': 'manager',
                'employee_id': 'EMP002',
                'department': 'Management',
                'password': 'manager123',
                'is_staff': True,
                'is_superuser': False,
            },
            {
                'username': 'supervisor',
                'first_name': 'Floor',
                'last_name': 'Supervisor',
                'email': 'supervisor@pvdgold.com',
                'role': 'supervisor',
                'employee_id': 'EMP003',
                'department': 'Production',
                'password': 'super123',
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'username': 'worker',
                'first_name': 'John',
                'last_name': 'Craftsman',
                'email': 'worker@pvdgold.com',
                'role': 'production_worker',
                'employee_id': 'EMP004',
                'department': 'Production',
                'password': 'worker123',
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'username': 'inventory',
                'first_name': 'Stock',
                'last_name': 'Clerk',
                'email': 'inventory@pvdgold.com',
                'role': 'inventory_clerk',
                'employee_id': 'EMP005',
                'department': 'Inventory',
                'password': 'inv123',
                'is_staff': False,
                'is_superuser': False,
            },
        ]

        created = 0
        for data in demo_users:
            password = data.pop('password')
            username = data['username']
            user, is_new = User.objects.get_or_create(username=username, defaults=data)
            if is_new:
                user.set_password(password)
                user.save()
                created += 1
        self.stdout.write(f'  Demo users: {created} created')
