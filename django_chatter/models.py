import uuid

from django.conf import settings
from django.db import models
from django.utils.module_loading import import_string


def get_text_field(**kwargs):
    """It allows to customize the field in order to make it html for example"""
    config = getattr(settings, "CHATTER_TEXTFIELD_CONFIG", {})
    config.setdefault('field', "django.db.models.TextField")
    config.setdefault('attributes', {})
    text_field = import_string(config['field'])
    attributes = config['attributes']
    for key in kwargs:
        attributes.setdefault(key, kwargs[key])
    return text_field(**attributes)


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE, related_name='profile')
    last_visit = models.DateTimeField()


# This model is used to give date and time when a message was created/modified.
class DateTimeModel(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Room(DateTimeModel):
    id = models.UUIDField(primary_key=True,
                          default=uuid.uuid4,
                          editable=False)
    name = models.CharField(verbose_name="name",
                            max_length=350,
                            null=True, blank=True)
    # deactivated rooms should not appear in lists.
    enabled = models.BooleanField(verbose_name="enabled", default=True)

    members = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)

    def __str__(self):
        if self.name:
            return self.name
        members_limit = 20
        members_qs = self.get_members_all()
        members_total = members_qs.count()
        members_list = []
        for member in members_qs[:members_limit]:
            members_list.append(str(member))
        s = ", ".join(members_list)
        if members_total > members_limit:
            s += "..."
        return s

    def is_member(self, user):
        """Checks whether the user is a member of the room
        :rtype bool
        """
        return self.members.filter(pk=user.pk).exists()

    def get_members_all(self, excluding=None, pks=False):
        """Returns all members of the room following the configuration criteria"""
        members = self.members
        if excluding is not None:
            members = members.exclude(**excluding)
        if pks:
            members = members.values_list('pk', flat=pks)
        return members

    class Meta:
        verbose_name = "Room"
        verbose_name_plural = "Rooms"


class Message(DateTimeModel):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL,
                               verbose_name="sender",
                               on_delete=models.CASCADE,
                               related_name='sender')
    room = models.ForeignKey(Room,
                             verbose_name="room",
                             on_delete=models.CASCADE)
    text = get_text_field(verbose_name="text")
    recipients = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                        verbose_name="recipients",
                                        related_name='recipients')

    def __str__(self):
        return f'sent by "{self.sender}" in room "{self.room}"'

    class Meta:
        ordering = ['-id']
        verbose_name = "Message"
        verbose_name_plural = "Messages"
