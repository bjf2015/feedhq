from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext_lazy as _


POST_TOKEN_DURATION = 60 * 30  # 30 minutes
AUTH_TOKEN_TIMEOUT = 3600 * 24 * 7  # 1 week

AUTH_TOKEN_LENGTH = 267
POST_TOKEN_LENGTH = 57


def check_auth_token(token):
    key = 'reader_auth_token:{0}'.format(token)
    value = cache.get(key)
    if value is None:
        try:
            token = AuthToken.objects.get(token=token)
        except AuthToken.DoesNotExist:
            return False
        value = token.user_id
        cache.set(key, value, AUTH_TOKEN_TIMEOUT)
    return int(value)


def check_post_token(token):
    key = 'reader_post_token:{0}'.format(token)
    value = cache.get(key)
    if value is None:
        return False
    return int(value)


def generate_auth_token(user):
    token = user.auth_tokens.create()
    key = 'reader_auth_token:{0}'.format(token.token)
    cache.set(key, user.pk, AUTH_TOKEN_TIMEOUT)
    return token.token


def generate_post_token(user):
    token = get_random_string(POST_TOKEN_LENGTH)
    key = 'reader_post_token:{0}'.format(token)
    cache.set(key, user.pk, POST_TOKEN_DURATION)
    return token


class AuthToken(models.Model):
    user = models.ForeignKey(User, verbose_name=_('User'),
                             related_name='auth_tokens')
    token = models.CharField(_('Token'), max_length=300, db_index=True,
                             default=get_random_string(AUTH_TOKEN_LENGTH))
    date_created = models.DateTimeField(_('Creation date'),
                                        default=timezone.now)

    def delete(self):
        cache_key = 'reader_auth_token:{0}'.format(self.token)
        super(AuthToken, self).delete()
        cache.delete(cache_key)
