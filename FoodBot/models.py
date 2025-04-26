from django.db import models


class Recipe(models.Model):
    title = models.CharField(verbose_name='Название:',max_length=100)
    description = models.TextField(verbose_name='Описание:')
    price = models.DecimalField(verbose_name='Стоимость в Р.:', max_digits=10, decimal_places=2)
    image = models.ImageField(verbose_name='Изображение', upload_to='recipes/', blank=True, null=True)


class UserProfile(models.Model):
    user_id = models.BigIntegerField(verbose_name='Telegram ID', unique=True)
    favorite_recipes = models.ManyToManyField(
        'Recipe',
        blank=True,
        related_name='favorited_by',
        verbose_name='ID избранных рецептов:',
    )
    is_premium = models.BooleanField(verbose_name='Платная подписка:', default=False)
    