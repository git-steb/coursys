"""
A module written to manage our sessional contracts.  This will be similar to RA and TA contracts, but with
some important differences.
"""

from django.db import models
from autoslug import AutoSlugField
from coredata.models import AnyPerson, Unit, JSONField, CourseOffering, Person
from courselib.slugs import make_slug
from courselib.storage import UploadedFileStorage, upload_path
import os


GUARANTEE_CHOICES = (
    ('GUAR', 'Appointment Guaranteed'),
    ('COND', 'Appointment Conditional Upon Enrolment')
)
TYPE_CHOICES = (
    ('INIT', 'Initial Appointment to this Position Number'),
    ('REAP', 'Reappointment to Same Position Number or Revision')
)

class SessionalAccountQuerySet(models.QuerySet):
    """
    As usual, define some querysets.
    """
    def visible(self, units):
        """
        Only see visible items, in this case also limited by accessible units.
        """
        return self.filter(hidden=False, unit__in=units)


class SessionalAccount(models.Model):
    """
    Sessionals have their own position and account number per unit.  Each unit has up to
    two of these account/position numbers, one for SFUFA and one for TSSU.  They don't need
    to fill in two things for every contract, so we'll store them together and let them pick.
    """
    unit = models.ForeignKey(Unit, null=False, blank=False, on_delete=models.PROTECT)
    title = models.CharField(max_length=60)
    account_number = models.CharField(max_length=40, null=False, blank=False)
    position_number = models.PositiveIntegerField(null=False, blank=False)

    def autoslug(self):
        """As usual, create a unique slug for each object"""
        return make_slug(self.unit.label + '-' + str(self.account_number) + '-' + str(self.title))

    slug = AutoSlugField(populate_from='autoslug', null=False, editable=False, unique=True)
    hidden = models.BooleanField(null=False, default=False, editable=False)
    objects = SessionalAccountQuerySet.as_manager()

    def __str__(self):
        return "%s - %s" % (self.unit, self.title)

    def delete(self):
        """Like most of our objects, we don't want to ever really delete it."""
        self.hidden = True
        self.save()


class SessionalContractQuerySet(models.QuerySet):
    """
    As usual, define some querysets.
    """
    def visible(self, units):
        """
        Only see visible items, in this case also limited by accessible units.
        """
        return self.filter(hidden=False, unit__in=units)


class SessionalContract(models.Model):
    """
    Similar to TA or RA contract, but we need to be able to use them with people who aren't in the
    system yet.
    """
    sessional = models.ForeignKey(AnyPerson, null=False, blank=False, on_delete=models.PROTECT)
    account = models.ForeignKey(SessionalAccount, null=False, blank=False, on_delete=models.PROTECT)
    unit = models.ForeignKey(Unit, null=False, blank=False, on_delete=models.PROTECT)
    sin = models.CharField(max_length=30,
                           verbose_name="SIN",
                           help_text="Social Insurance Number - 000000000 if unknown")

    # We want do add some sort of accountability for checking visas.  Don't
    # allow printing of the contract if this box hasn't been checked.
    visa_verified = models.BooleanField(default=False, help_text="I have verified this sessional's visa information")
    appointment_start = models.DateField(null=False, blank=False)
    appointment_end = models.DateField(null=False, blank=False)
    pay_start = models.DateField(null=False, blank=False)
    pay_end = models.DateField(null=False, blank=False)
    # Was going to add a Semester, but since the offering itself has a semester, no need for it.
    offering = models.ForeignKey(CourseOffering, null=False, blank=False, on_delete=models.PROTECT)
    course_hours_breakdown = models.CharField(null=True, blank=True, max_length=100,
                                              help_text="e.g. 1x2HR Lecture, etc.  This will show up in the form in "
                                                        "the column after the course department and number.")
    appt_guarantee = models.CharField("Appoinment Guarantee", max_length=4, choices=GUARANTEE_CHOICES, null=False,
                                      blank=False, default='GUAR')
    appt_type = models.CharField("Appointment Type", max_length=4, choices=TYPE_CHOICES, null=False, blank=False,
                                 default='INIT')
    contact_hours = models.DecimalField("Weekly Contact Hours", max_digits=6, decimal_places=2, null=False, blank=False)
    total_salary = models.DecimalField(max_digits=8, decimal_places=2, null=False, blank=False)
    notes = models.CharField(max_length=400, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    created_by = models.CharField(max_length=20, null=False, blank=False, editable=False)
    hidden = models.BooleanField(null=False, default=False, editable=False)
    config = JSONField(null=False, blank=False, editable=False, default=dict)
    objects = SessionalContractQuerySet.as_manager()

    def autoslug(self):
        """As usual, create a unique slug for each object"""
        return make_slug(str(self.sessional) + "-" + str(self.offering))

    slug = AutoSlugField(populate_from='autoslug', null=False, editable=False, unique=True)

    def __str__(self):
        return "%s - %s" % (str(self.sessional), str(self.offering))

    def delete(self):
        """Like most of our objects, we don't want to ever really delete it."""
        self.hidden = True
        self.save()

    def has_attachments(self):
        return self.attachments.visible().count() > 0


class SessionalConfig(models.Model):
    """
    An object to hold default dates for a given unit.  The user can change these whenever the semesters change,
    and the new contracts will use these as defaults.  There should only be one of these per unit, to avoid
    overwriting someone else's.
    """
    unit = models.OneToOneField(Unit, null=False, blank=False, on_delete=models.PROTECT)
    appointment_start = models.DateField()
    appointment_end = models.DateField()
    pay_start = models.DateField()
    pay_end = models.DateField()
    course_hours_breakdown = models.CharField(null=True, blank=True, max_length=100,
                                              help_text="e.g. 1x2HR Lecture, etc.  This will show up in the form in "
                                                        "the column after the course department and number.")

    def autoslug(self):
        return make_slug(self.unit.label)

    slug = AutoSlugField(populate_from='autoslug', null=False, editable=False, unique=True)

    def __str__(self):
        return "%s - %s" % (self.unit.label, "default configuration for sessional contracts")

    def delete(self):
        raise NotImplementedError("This object cannot be deleted")


def sessional_attachment_upload_to(instance, filename):
    return upload_path('sessionals', filename)


class SessionalAttachmentQueryset(models.QuerySet):
    def visible(self):
        return self.filter(hidden=False)


class SessionalAttachment(models.Model):
    """
    Document attached to a CareerEvent.
    """
    sessional = models.ForeignKey(SessionalContract, null=False, blank=False, related_name="attachments", on_delete=models.PROTECT)
    title = models.CharField(max_length=250, null=False)
    slug = AutoSlugField(populate_from='title', null=False, editable=False, unique_with=('sessional',))
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(Person, help_text='Document attachment created by.', on_delete=models.PROTECT)
    contents = models.FileField(storage=UploadedFileStorage, upload_to=sessional_attachment_upload_to, max_length=500)
    mediatype = models.CharField(max_length=200, null=True, blank=True, editable=False)
    hidden = models.BooleanField(default=False, editable=False)

    objects = SessionalAttachmentQueryset.as_manager()

    def __str__(self):
        return self.contents.name

    class Meta:
        ordering = ("created_at",)
        unique_together = (("sessional", "slug"),)

    def contents_filename(self):
        return os.path.basename(self.contents.name)

    def hide(self):
        self.hidden = True
        self.save()

