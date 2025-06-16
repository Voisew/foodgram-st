from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.db import models


class User(AbstractUser):
    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name='Электронная почта'
    )
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[RegexValidator(regex=r"^[\w.@+-]+\Z")],
        verbose_name='Логин пользователя'
    )
    first_name = models.CharField(max_length=150,
                                  verbose_name='Имя пользователя')
    last_name = models.CharField(max_length=150,
                                 verbose_name='Фамилия пользователя')
    avatar = models.ImageField(
        upload_to='users/', null=True, blank=True,
        verbose_name='Аватар'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Пользователь',
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Подписчик',
    )

    class Meta:
        unique_together = (
            'user',
            'following',
        )
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['user__username',]

    def unique(self):
        if self.user == self.following:
            raise ValidationError(
                "Невозможно подписаться на самого себя."
            )

    def save(self, *args, **kwargs):
        self.unique()
        super().save(*args, **kwargs)