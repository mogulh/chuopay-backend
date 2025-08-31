# Section-Based Data Isolation

## Overview

The Chuopay system now supports section-based data isolation, allowing schools with multiple sections (Primary, Secondary, Nursery, etc.) to maintain separate data and access controls for each section while sharing the same platform.

## Features

### 1. **SchoolSection Model**

The `SchoolSection` model provides the foundation for section-based data isolation:

```python
class SchoolSection(models.Model):
    SECTION_CHOICES = [
        ('nursery', 'Nursery'),
        ('primary', 'Primary'),
        ('secondary', 'Secondary'),
        ('junior_secondary', 'Junior Secondary'),
        ('senior_secondary', 'Senior Secondary'),
    ]

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='sections')
    name = models.CharField(max_length=50, choices=SECTION_CHOICES)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # Section-specific settings
    currency = models.CharField(max_length=3, blank=True)
    timezone = models.CharField(max_length=50, blank=True)

    # Section management
    is_active = models.BooleanField(default=True)
    section_head = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
```

### 2. **Updated Models with Section Support**

All core models now include section relationships:

- **Group**: `section = models.ForeignKey(SchoolSection, ...)`
- **Student**: `section = models.ForeignKey(SchoolSection, ...)`
- **ContributionEvent**: `section = models.ForeignKey(SchoolSection, ...)`

### 3. **Data Isolation Features**

#### **Student Isolation**

- Students are assigned to specific sections
- Students can only belong to groups within their section
- Student data is filtered by section in all queries

#### **Group Isolation**

- Groups are created within specific sections
- Groups can only contain students from the same section
- Group names are unique within each section

#### **Event Isolation**

- Contribution events are created within specific sections
- Events can only target groups within the same section
- Event data is isolated by section

#### **Teacher Access Control**

- Teachers can be assigned to manage specific sections
- Teachers can only see and manage data within their assigned sections
- Access is controlled through `managed_sections` relationship

### 4. **API Endpoints**

New API endpoints for section management:

- `GET /api/school-sections/` - List all sections
- `POST /api/school-sections/` - Create a new section
- `GET /api/school-sections/{id}/` - Get section details
- `PUT /api/school-sections/{id}/` - Update section
- `DELETE /api/school-sections/{id}/` - Delete section

### 5. **Access Control**

#### **Role-Based Section Access**

**Admins:**

- Can access all sections within their school
- Can create, update, and delete sections
- Can assign section heads

**Teachers:**

- Can only access sections they are assigned to manage
- Can only see students and groups within their sections
- Can only create events within their sections

**Parents:**

- Can see all sections where their children are enrolled
- Can access contribution events for their children's sections
- Data is automatically filtered by their children's sections

### 6. **Section-Specific Settings**

Each section can have its own configuration:

- **Currency**: Override school currency if different
- **Timezone**: Override school timezone if different
- **Section Head**: Assign a teacher or admin to manage the section

### 7. **Management Commands**

#### **Create Default Sections**

```bash
python manage.py create_default_sections --all
python manage.py create_default_sections --school-id 1
```

This creates standard sections (Primary, Secondary, Nursery) for schools.

#### **Create Test Data**

```bash
python manage.py create_test_data
```

Creates test data with sections, students, and groups for demonstration.

### 8. **Database Schema**

#### **New Tables**

- `school_sections` - Section information
- `student_groups` - Student-group relationships with academic context
- `student_parents` - Student-parent relationships with contact preferences

#### **Updated Tables**

- `groups` - Added `section_id` foreign key
- `students` - Added `section_id` foreign key
- `contribution_events` - Added `section_id` foreign key

### 9. **Usage Examples**

#### **Creating Sections**

```python
# Create sections for a school
school = School.objects.get(name='Example School')

primary_section = SchoolSection.objects.create(
    school=school,
    name='primary',
    display_name='Primary School',
    description='Primary education section (Grades 1-8)'
)

secondary_section = SchoolSection.objects.create(
    school=school,
    name='secondary',
    display_name='Secondary School',
    description='Secondary education section (Grades 9-12)'
)
```

#### **Creating Groups in Sections**

```python
# Create a group in the primary section
primary_group = Group.objects.create(
    name='Class 1A',
    school=school,
    section=primary_section,
    group_type='class',
    teacher=teacher_user
)
```

#### **Assigning Students to Sections**

```python
# Assign a student to a section
student = Student.objects.create(
    first_name='John',
    last_name='Doe',
    student_id='STU001',
    school=school,
    section=primary_section,
    # ... other fields
)
```

#### **Section-Based Queries**

```python
# Get all students in primary section
primary_students = Student.objects.filter(section__name='primary')

# Get all groups in secondary section
secondary_groups = Group.objects.filter(section__name='secondary')

# Get all events in a specific section
section_events = ContributionEvent.objects.filter(section=primary_section)
```

### 10. **Benefits**

1. **Data Isolation**: Complete separation of data between sections
2. **Access Control**: Granular permissions based on section assignments
3. **Scalability**: Support for schools with multiple educational levels
4. **Flexibility**: Each section can have its own settings and configuration
5. **Security**: Teachers and staff can only access data within their assigned sections
6. **Organization**: Clear structure for managing complex school hierarchies

### 11. **Migration Strategy**

The implementation includes a migration strategy that:

- Adds section fields as nullable initially
- Creates through models for many-to-many relationships
- Maintains backward compatibility during transition
- Provides management commands for data setup

### 12. **Testing**

Use the provided test script to verify section isolation:

```bash
python test_section_isolation.py
```

This script demonstrates:

- Section creation and configuration
- Student assignment to sections
- Group isolation by section
- Teacher access control
- Parent access across sections
- Section-specific settings

## Conclusion

Section-based data isolation provides a robust foundation for multi-section schools, ensuring data security, proper access control, and organizational clarity while maintaining the flexibility to scale with growing educational institutions.
