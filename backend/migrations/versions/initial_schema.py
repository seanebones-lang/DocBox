"""
Initial database schema migration.

Revision ID: 001
Revises:
Create Date: 2025-10-20 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database schema."""

    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('ADMIN', 'DOCTOR', 'STAFF', 'KIOSK', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('clinic_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('specialty', sa.String(length=100), nullable=True),
        sa.Column('license_number', sa.String(length=50), nullable=True),
        sa.Column('mfa_enabled', sa.Boolean(), nullable=False),
        sa.Column('mfa_secret', sa.String(length=32), nullable=True),
        sa.Column('last_login_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('login_attempts', sa.Integer(), nullable=False),
        sa.Column('locked_until', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('password_changed_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('deleted_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_clinic_id'), 'users', ['clinic_id'], unique=False)

    # Create clinics table
    op.create_table('clinics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('fax', sa.String(length=20), nullable=True),
        sa.Column('website', sa.String(length=500), nullable=True),
        sa.Column('address_line1', sa.String(length=255), nullable=False),
        sa.Column('address_line2', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('state', sa.String(length=50), nullable=False),
        sa.Column('zip_code', sa.String(length=10), nullable=False),
        sa.Column('country', sa.String(length=50), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('operating_hours', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('max_patients_per_day', sa.Integer(), nullable=False),
        sa.Column('max_patients_per_hour', sa.Integer(), nullable=False),
        sa.Column('services', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('specialties', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=False),
        sa.Column('language_support', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('has_kiosk', sa.Boolean(), nullable=False),
        sa.Column('kiosk_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_accepting_new_patients', sa.Boolean(), nullable=False),
        sa.Column('npi_number', sa.String(length=10), nullable=True),
        sa.Column('tax_id', sa.String(length=20), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('deleted_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_clinics_code'), 'clinics', ['code'], unique=True)

    # Create clinic_locations table
    op.create_table('clinic_locations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('clinic_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('building', sa.String(length=50), nullable=True),
        sa.Column('floor', sa.String(length=20), nullable=True),
        sa.Column('room_number', sa.String(length=20), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_clinic_locations_clinic_id'), 'clinic_locations', ['clinic_id'], unique=False)

    # Create patients table
    op.create_table('patients',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('middle_name', sa.String(length=100), nullable=True),
        sa.Column('date_of_birth', sa.Date(), nullable=False),
        sa.Column('gender', sa.Enum('MALE', 'FEMALE', 'OTHER', 'UNKNOWN', name='gender'), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('address_line1', sa.String(length=255), nullable=True),
        sa.Column('address_line2', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=50), nullable=True),
        sa.Column('zip_code', sa.String(length=10), nullable=True),
        sa.Column('country', sa.String(length=50), nullable=False),
        sa.Column('ssn', sa.String(length=255), nullable=True),
        sa.Column('medical_record_number', sa.String(length=50), nullable=False),
        sa.Column('insurance_provider', sa.String(length=200), nullable=True),
        sa.Column('insurance_policy_number', sa.String(length=100), nullable=True),
        sa.Column('insurance_group_number', sa.String(length=100), nullable=True),
        sa.Column('emergency_contact_name', sa.String(length=200), nullable=True),
        sa.Column('emergency_contact_phone', sa.String(length=20), nullable=True),
        sa.Column('emergency_contact_relationship', sa.String(length=50), nullable=True),
        sa.Column('blood_type', sa.Enum('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', 'UNKNOWN', name='bloodtype'), nullable=False),
        sa.Column('height_cm', sa.Integer(), nullable=True),
        sa.Column('weight_kg', sa.Integer(), nullable=True),
        sa.Column('primary_doctor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('primary_clinic_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('preferred_language', sa.String(length=10), nullable=False),
        sa.Column('communication_preferences', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('biometric_template', sa.Text(), nullable=True),
        sa.Column('biometric_enabled', sa.Boolean(), nullable=False),
        sa.Column('has_genomic_data', sa.Boolean(), nullable=False),
        sa.Column('genomic_data_consent', sa.Boolean(), nullable=False),
        sa.Column('genomic_data_path', sa.String(length=500), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('deleted_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_patients_email'), 'patients', ['email'], unique=False)
    op.create_index(op.f('ix_patients_medical_record_number'), 'patients', ['medical_record_number'], unique=True)
    op.create_index(op.f('ix_patients_primary_clinic_id'), 'patients', ['primary_clinic_id'], unique=False)
    op.create_index(op.f('ix_patients_primary_doctor_id'), 'patients', ['primary_doctor_id'], unique=False)
    op.create_index(op.f('ix_patients_user_id'), 'patients', ['user_id'], unique=True)

    # Create medical_history table
    op.create_table('medical_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('condition', sa.String(length=500), nullable=False),
        sa.Column('icd10_code', sa.String(length=20), nullable=True),
        sa.Column('diagnosis_date', sa.Date(), nullable=False),
        sa.Column('resolution_date', sa.Date(), nullable=True),
        sa.Column('is_chronic', sa.Boolean(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('diagnosed_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medical_history_patient_id'), 'medical_history', ['patient_id'], unique=False)

    # Create allergies table
    op.create_table('allergies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('allergen', sa.String(length=200), nullable=False),
        sa.Column('allergen_type', sa.String(length=50), nullable=False),
        sa.Column('reaction', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('onset_date', sa.Date(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_allergies_patient_id'), 'allergies', ['patient_id'], unique=False)

    # Create appointments table
    op.create_table('appointments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('clinic_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('scheduled_start', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('scheduled_end', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('appointment_type', sa.Enum('ROUTINE', 'FOLLOW_UP', 'URGENT', 'ANNUAL_PHYSICAL', 'CONSULTATION', 'PROCEDURE', 'TELEHEALTH', name='appointmenttype'), nullable=False),
        sa.Column('status', sa.Enum('SCHEDULED', 'CONFIRMED', 'CHECKED_IN', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'NO_SHOW', 'RESCHEDULED', name='appointmentstatus'), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('chief_complaint', sa.Text(), nullable=True),
        sa.Column('provider_notes', sa.Text(), nullable=True),
        sa.Column('staff_notes', sa.Text(), nullable=True),
        sa.Column('checked_in_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('checked_in_by', sa.String(length=50), nullable=True),
        sa.Column('actual_start', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('actual_end', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('reminder_sent_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('confirmation_sent_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('is_telehealth', sa.Boolean(), nullable=False),
        sa.Column('telehealth_url', sa.String(length=500), nullable=True),
        sa.Column('is_follow_up', sa.Boolean(), nullable=False),
        sa.Column('parent_appointment_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('copay_amount', sa.Integer(), nullable=True),
        sa.Column('copay_paid', sa.Boolean(), nullable=False),
        sa.Column('copay_paid_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('intake_form_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('vitals', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('cancelled_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('cancelled_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_appointments_clinic_id'), 'appointments', ['clinic_id'], unique=False)
    op.create_index(op.f('ix_appointments_patient_id'), 'appointments', ['patient_id'], unique=False)
    op.create_index(op.f('ix_appointments_provider_id'), 'appointments', ['provider_id'], unique=False)
    op.create_index(op.f('ix_appointments_scheduled_start'), 'appointments', ['scheduled_start'], unique=False)
    op.create_index(op.f('ix_appointments_status'), 'appointments', ['status'], unique=False)
    op.create_foreign_key(None, 'appointments', 'appointments', ['parent_appointment_id'], ['id'])
    op.create_foreign_key(None, 'appointments', 'users', ['cancelled_by_id'], ['id'])
    op.create_foreign_key(None, 'appointments', 'clinic_locations', ['location_id'], ['id'])
    op.create_foreign_key(None, 'appointments', 'clinics', ['clinic_id'], ['id'])
    op.create_foreign_key(None, 'appointments', 'patients', ['patient_id'], ['id'])
    op.create_foreign_key(None, 'appointments', 'users', ['provider_id'], ['id'])

    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_email', sa.String(length=255), nullable=True),
        sa.Column('user_role', sa.String(length=20), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=False),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('clinic_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_clinic_id'), 'audit_logs', ['clinic_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)
    op.create_index(op.f('ix_audit_logs_resource_id'), 'audit_logs', ['resource_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_resource_type'), 'audit_logs', ['resource_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)

    # Create login_attempts table
    op.create_table('login_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=False),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('failure_reason', sa.String(length=200), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_login_attempts_created_at'), 'login_attempts', ['created_at'], unique=False)
    op.create_index(op.f('ix_login_attempts_email'), 'login_attempts', ['email'], unique=False)
    op.create_index(op.f('ix_login_attempts_user_id'), 'login_attempts', ['user_id'], unique=False)

    # Create foreign key constraints
    op.create_foreign_key(None, 'clinic_locations', 'clinics', ['clinic_id'], ['id'])
    op.create_foreign_key(None, 'medical_history', 'patients', ['patient_id'], ['id'])
    op.create_foreign_key(None, 'medical_history', 'users', ['diagnosed_by_id'], ['id'])
    op.create_foreign_key(None, 'patients', 'clinics', ['primary_clinic_id'], ['id'])
    op.create_foreign_key(None, 'patients', 'users', ['primary_doctor_id'], ['id'])
    op.create_foreign_key(None, 'patients', 'users', ['user_id'], ['id'])
    op.create_foreign_key(None, 'users', 'clinics', ['clinic_id'], ['id'])


def downgrade() -> None:
    """Drop initial database schema."""

    op.drop_table('login_attempts')
    op.drop_table('audit_logs')
    op.drop_table('appointments')
    op.drop_table('allergies')
    op.drop_table('medical_history')
    op.drop_table('patients')
    op.drop_table('clinic_locations')
    op.drop_table('clinics')
    op.drop_table('users')
