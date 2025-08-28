# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)
    name = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthtokenToken(models.Model):
    key = models.CharField(primary_key=True, max_length=40)
    created = models.DateTimeField()
    user = models.OneToOneField('Users', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'authtoken_token'


class ContributionEvents(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    event_type = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=5)  # max_digits and decimal_places have been guessed, as this database handles decimal fields as float
    currency = models.CharField(max_length=3)
    has_tiers = models.BooleanField()
    participation_type = models.CharField(max_length=20)
    due_date = models.DateTimeField()
    event_date = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField()
    is_published = models.BooleanField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    created_by = models.ForeignKey('Users', models.DO_NOTHING)
    school = models.ForeignKey('Schools', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'contribution_events'


class ContributionEventsGroups(models.Model):
    contributionevent = models.ForeignKey(ContributionEvents, models.DO_NOTHING)
    group = models.ForeignKey('Groups', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'contribution_events_groups'
        unique_together = (('contributionevent', 'group'),)


class ContributionTiers(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=5)  # max_digits and decimal_places have been guessed, as this database handles decimal fields as float
    is_default = models.BooleanField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    event = models.ForeignKey(ContributionEvents, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'contribution_tiers'
        unique_together = (('event', 'name'),)


class DjangoAdminLog(models.Model):
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey('Users', models.DO_NOTHING)
    action_time = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class Groups(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    group_type = models.CharField(max_length=20)
    is_active = models.BooleanField()
    max_students = models.PositiveIntegerField(blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    teacher = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)
    school = models.ForeignKey('Schools', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'groups'
        unique_together = (('name', 'school'),)


class Leads(models.Model):
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=254)
    user_type = models.CharField(max_length=20)
    source = models.CharField(max_length=50)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'leads'


class NotificationLogs(models.Model):
    notification_type = models.CharField(max_length=20)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(max_length=20)
    sent_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    external_id = models.CharField(max_length=100)
    external_status = models.CharField(max_length=50)
    delivery_error = models.TextField()
    cost = models.DecimalField(max_digits=10, decimal_places=5)  # max_digits and decimal_places have been guessed, as this database handles decimal fields as float
    currency = models.CharField(max_length=3)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    created_by = models.ForeignKey('Users', models.DO_NOTHING)
    event = models.ForeignKey(ContributionEvents, models.DO_NOTHING)
    recipient = models.ForeignKey('Users', models.DO_NOTHING, related_name='notificationlogs_recipient_set')
    student = models.ForeignKey('Students', models.DO_NOTHING)
    schedule = models.ForeignKey('NotificationSchedules', models.DO_NOTHING, blank=True, null=True)
    template = models.ForeignKey('NotificationTemplates', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'notification_logs'


class NotificationSchedules(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    schedule_type = models.CharField(max_length=20)
    scheduled_time = models.DateTimeField(blank=True, null=True)
    recurring_type = models.CharField(max_length=20)
    recurring_interval = models.PositiveIntegerField()
    event_types = models.JSONField()
    payment_statuses = models.JSONField()
    days_before_due = models.PositiveIntegerField(blank=True, null=True)
    is_active = models.BooleanField()
    last_run = models.DateTimeField(blank=True, null=True)
    next_run = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    created_by = models.ForeignKey('Users', models.DO_NOTHING)
    template = models.ForeignKey('NotificationTemplates', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'notification_schedules'


class NotificationSettings(models.Model):
    receives_notifications = models.BooleanField()
    receives_sms = models.BooleanField()
    receives_email = models.BooleanField()
    receives_push = models.BooleanField()
    receives_in_app = models.BooleanField()
    payment_reminders = models.BooleanField()
    event_updates = models.BooleanField()
    general_announcements = models.BooleanField()
    quiet_hours_start = models.TimeField(blank=True, null=True)
    quiet_hours_end = models.TimeField(blank=True, null=True)
    max_notifications_per_day = models.PositiveIntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    user = models.OneToOneField('Users', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'notification_settings'


class NotificationTemplates(models.Model):
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=20)
    subject = models.CharField(max_length=200)
    content = models.TextField()
    variables = models.JSONField()
    is_active = models.BooleanField()
    max_length = models.PositiveIntegerField(blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'notification_templates'
        unique_together = (('name', 'template_type'),)


class PaymentHistory(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=5)  # max_digits and decimal_places have been guessed, as this database handles decimal fields as float
    payment_method = models.CharField(max_length=20)
    transaction_id = models.CharField(max_length=100)
    status = models.CharField(max_length=20)
    payment_date = models.DateTimeField()
    processed_at = models.DateTimeField(blank=True, null=True)
    external_id = models.CharField(max_length=100)
    external_status = models.CharField(max_length=50)
    external_response = models.JSONField(blank=True, null=True)
    notes = models.TextField()
    metadata = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    contribution = models.ForeignKey('StudentContributions', models.DO_NOTHING)
    created_by = models.ForeignKey('Users', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'payment_history'


class PhoneVerifications(models.Model):
    phone_number = models.CharField(max_length=13)
    verification_code = models.CharField(max_length=6)
    is_used = models.BooleanField()
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'phone_verifications'


class ReminderLogs(models.Model):
    reminder_type = models.CharField(max_length=20)
    message = models.TextField()
    status = models.CharField(max_length=20)
    sent_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    delivery_error = models.TextField()
    external_id = models.CharField(max_length=100)
    external_status = models.CharField(max_length=50)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    created_by = models.ForeignKey('Users', models.DO_NOTHING)
    event = models.ForeignKey(ContributionEvents, models.DO_NOTHING)
    parent = models.ForeignKey('Users', models.DO_NOTHING, related_name='reminderlogs_parent_set')
    student = models.ForeignKey('Students', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'reminder_logs'


class Schools(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    city = models.CharField(max_length=100)
    county = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=13)
    email = models.CharField(max_length=254, blank=True, null=True)
    website = models.CharField(max_length=200, blank=True, null=True)
    logo = models.CharField(max_length=100, blank=True, null=True)
    currency = models.CharField(max_length=3)
    timezone = models.CharField(max_length=50)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'schools'


class SmsCredits(models.Model):
    amount = models.IntegerField()
    credit_type = models.CharField(max_length=20)
    cost = models.DecimalField(max_digits=10, decimal_places=5)  # max_digits and decimal_places have been guessed, as this database handles decimal fields as float
    currency = models.CharField(max_length=3)
    provider = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=100)
    notes = models.TextField()
    created_at = models.DateTimeField()
    created_by = models.ForeignKey('Users', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'sms_credits'


class StudentContributions(models.Model):
    amount_required = models.DecimalField(max_digits=10, decimal_places=5)  # max_digits and decimal_places have been guessed, as this database handles decimal fields as float
    amount_paid = models.DecimalField(max_digits=10, decimal_places=5)  # max_digits and decimal_places have been guessed, as this database handles decimal fields as float
    payment_status = models.CharField(max_length=20)
    payment_date = models.DateTimeField(blank=True, null=True)
    payment_method = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=100)
    notes = models.TextField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    event = models.ForeignKey(ContributionEvents, models.DO_NOTHING)
    student = models.ForeignKey('Students', models.DO_NOTHING)
    tier = models.ForeignKey(ContributionTiers, models.DO_NOTHING, blank=True, null=True)
    updated_by = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)
    confirmation_notes = models.TextField()
    confirmed_at = models.DateTimeField(blank=True, null=True)
    confirmed_by = models.ForeignKey('Users', models.DO_NOTHING, related_name='studentcontributions_confirmed_by_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'student_contributions'
        unique_together = (('student', 'event'),)


class StudentGroups(models.Model):
    joined_date = models.DateField()
    is_active = models.BooleanField()
    academic_year = models.CharField(max_length=9)
    term = models.CharField(max_length=20)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    group = models.ForeignKey(Groups, models.DO_NOTHING)
    student = models.ForeignKey('Students', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'student_groups'
        unique_together = (('student', 'group', 'academic_year'),)


class StudentParents(models.Model):
    relationship = models.CharField(max_length=20)
    is_primary_contact = models.BooleanField()
    is_emergency_contact = models.BooleanField()
    receives_notifications = models.BooleanField()
    receives_sms = models.BooleanField()
    receives_email = models.BooleanField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    parent = models.ForeignKey('Users', models.DO_NOTHING)
    student = models.ForeignKey('Students', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'student_parents'
        unique_together = (('student', 'parent'),)


class Students(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10)
    student_id = models.CharField(unique=True, max_length=50)
    admission_date = models.DateField()
    is_active = models.BooleanField()
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_phone = models.CharField(max_length=13)
    emergency_contact_relationship = models.CharField(max_length=50)
    medical_conditions = models.TextField()
    allergies = models.TextField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    school = models.ForeignKey(Schools, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'students'


class UserProfiles(models.Model):
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10)
    address = models.TextField()
    city = models.CharField(max_length=100)
    county = models.CharField(max_length=100)
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_phone = models.CharField(max_length=13)
    emergency_contact_relationship = models.CharField(max_length=50)
    notification_preferences = models.JSONField()
    language_preference = models.CharField(max_length=10)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    user = models.OneToOneField('Users', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'user_profiles'


class Users(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()
    email = models.CharField(unique=True, max_length=254, blank=True, null=True)
    phone_number = models.CharField(unique=True, max_length=13)
    role = models.CharField(max_length=10)
    is_phone_verified = models.BooleanField()
    firebase_uid = models.CharField(unique=True, max_length=128, blank=True, null=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    profile_picture = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'users'


class UsersGroups(models.Model):
    user = models.ForeignKey(Users, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'users_groups'
        unique_together = (('user', 'group'),)


class UsersUserPermissions(models.Model):
    user = models.ForeignKey(Users, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'users_user_permissions'
        unique_together = (('user', 'permission'),)
