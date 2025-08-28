from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from contributions.models import School, Group, Student, StudentGroup, StudentParent
from datetime import date

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test data for the admin dashboard'

    def handle(self, *args, **options):
        self.stdout.write('Creating test data...')
        
        # Create a school
        school, created = School.objects.get_or_create(
            name='Test School',
            defaults={
                'address': '123 Test Street, Nairobi',
                'city': 'Nairobi',
                'county': 'Nairobi',
                'phone_number': '+254700000001',
                'email': 'test@school.com',
                'currency': 'KES',
                'timezone': 'Africa/Nairobi'
            }
        )
        
        if created:
            self.stdout.write(f'Created school: {school.name}')
        else:
            self.stdout.write(f'School already exists: {school.name}')
        
        # Create admin user
        admin_user, created = User.objects.get_or_create(
            phone_number='+254700000000',
            defaults={
                'first_name': 'Admin',
                'last_name': 'User',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'is_phone_verified': True
            }
        )
        
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(f'Created admin user: {admin_user.full_name}')
        else:
            self.stdout.write(f'Admin user already exists: {admin_user.full_name}')
        
        # Create teacher user
        teacher_user, created = User.objects.get_or_create(
            phone_number='+254700000002',
            defaults={
                'first_name': 'John',
                'last_name': 'Teacher',
                'role': 'teacher',
                'is_phone_verified': True
            }
        )
        
        if created:
            teacher_user.set_password('teacher123')
            teacher_user.save()
            self.stdout.write(f'Created teacher user: {teacher_user.full_name}')
        else:
            self.stdout.write(f'Teacher user already exists: {teacher_user.full_name}')
        
        # Create parent users
        parent1, created = User.objects.get_or_create(
            phone_number='+254700000003',
            defaults={
                'first_name': 'Mary',
                'last_name': 'Parent',
                'role': 'parent',
                'is_phone_verified': True
            }
        )
        
        if created:
            parent1.set_password('parent123')
            parent1.save()
            self.stdout.write(f'Created parent user: {parent1.full_name}')
        else:
            self.stdout.write(f'Parent user already exists: {parent1.full_name}')
        
        parent2, created = User.objects.get_or_create(
            phone_number='+254700000004',
            defaults={
                'first_name': 'James',
                'last_name': 'Parent',
                'role': 'parent',
                'is_phone_verified': True
            }
        )
        
        if created:
            parent2.set_password('parent123')
            parent2.save()
            self.stdout.write(f'Created parent user: {parent2.full_name}')
        else:
            self.stdout.write(f'Parent user already exists: {parent2.full_name}')
        
        # Create groups
        class1, created = Group.objects.get_or_create(
            name='Class 1A',
            school=school,
            defaults={
                'description': 'First grade class A',
                'group_type': 'class',
                'teacher': teacher_user,
                'is_active': True,
                'max_students': 30
            }
        )
        
        if created:
            self.stdout.write(f'Created group: {class1.name}')
        else:
            self.stdout.write(f'Group already exists: {class1.name}')
        
        class2, created = Group.objects.get_or_create(
            name='Class 2B',
            school=school,
            defaults={
                'description': 'Second grade class B',
                'group_type': 'class',
                'teacher': teacher_user,
                'is_active': True,
                'max_students': 25
            }
        )
        
        if created:
            self.stdout.write(f'Created group: {class2.name}')
        else:
            self.stdout.write(f'Group already exists: {class2.name}')
        
        # Create students
        students_data = [
            {
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'student_id': 'STU001',
                'date_of_birth': date(2018, 3, 15),
                'gender': 'female',
                'school': school,
                'admission_date': date(2024, 1, 10),
                'is_active': True,
                'emergency_contact_name': 'John Johnson',
                'emergency_contact_phone': '+254700000005',
                'emergency_contact_relationship': 'father'
            },
            {
                'first_name': 'Bob',
                'last_name': 'Smith',
                'student_id': 'STU002',
                'date_of_birth': date(2018, 7, 22),
                'gender': 'male',
                'school': school,
                'admission_date': date(2024, 1, 10),
                'is_active': True,
                'emergency_contact_name': 'Sarah Smith',
                'emergency_contact_phone': '+254700000006',
                'emergency_contact_relationship': 'mother'
            },
            {
                'first_name': 'Charlie',
                'last_name': 'Brown',
                'student_id': 'STU003',
                'date_of_birth': date(2017, 11, 8),
                'gender': 'male',
                'school': school,
                'admission_date': date(2024, 1, 10),
                'is_active': True,
                'emergency_contact_name': 'Lucy Brown',
                'emergency_contact_phone': '+254700000007',
                'emergency_contact_relationship': 'mother'
            },
            {
                'first_name': 'Diana',
                'last_name': 'Wilson',
                'student_id': 'STU004',
                'date_of_birth': date(2018, 5, 12),
                'gender': 'female',
                'school': school,
                'admission_date': date(2024, 1, 10),
                'is_active': True,
                'emergency_contact_name': 'Mike Wilson',
                'emergency_contact_phone': '+254700000008',
                'emergency_contact_relationship': 'father'
            }
        ]
        
        for student_data in students_data:
            student, created = Student.objects.get_or_create(
                student_id=student_data['student_id'],
                defaults=student_data
            )
            
            if created:
                self.stdout.write(f'Created student: {student.full_name}')
            else:
                self.stdout.write(f'Student already exists: {student.full_name}')
        
        # Assign students to groups
        students = Student.objects.all()
        for i, student in enumerate(students):
            if i < 2:  # First two students to Class 1A
                group = class1
            else:  # Last two students to Class 2B
                group = class2
            
            student_group, created = StudentGroup.objects.get_or_create(
                student=student,
                group=group,
                academic_year='2024-2025',
                defaults={
                    'is_active': True,
                    'term': 'Term 1'
                }
            )
            
            if created:
                self.stdout.write(f'Assigned {student.full_name} to {group.name}')
            else:
                self.stdout.write(f'{student.full_name} already assigned to {group.name}')
        
        # Create parent-student relationships
        parent_student_data = [
            (parent1, students[0]),  # Mary Parent - Alice Johnson
            (parent1, students[1]),  # Mary Parent - Bob Smith
            (parent2, students[2]),  # James Parent - Charlie Brown
            (parent2, students[3]),  # James Parent - Diana Wilson
        ]
        
        for parent, student in parent_student_data:
            relationship, created = StudentParent.objects.get_or_create(
                student=student,
                parent=parent,
                defaults={
                    'relationship': 'mother' if parent.first_name == 'Mary' else 'father',
                    'is_primary_contact': True,
                    'is_emergency_contact': True,
                    'receives_notifications': True,
                    'receives_sms': True,
                    'receives_email': False
                }
            )
            
            if created:
                self.stdout.write(f'Created parent relationship: {parent.full_name} - {student.full_name}')
            else:
                self.stdout.write(f'Parent relationship already exists: {parent.full_name} - {student.full_name}')
        
        self.stdout.write(self.style.SUCCESS('Test data created successfully!'))
        self.stdout.write('\nTest Users:')
        self.stdout.write(f'Admin: +254700000000 (password: admin123)')
        self.stdout.write(f'Teacher: +254700000002 (password: teacher123)')
        self.stdout.write(f'Parent 1: +254700000003 (password: parent123)')
        self.stdout.write(f'Parent 2: +254700000004 (password: parent123)') 