from django.db import models


class Recipe(models.Model):
    title = models.CharField(verbose_name='Название:',max_length=100)
    description = models.TextField(verbose_name='Описание:')
    price = models.DecimalField(verbose_name='Стоимость в Р.:', max_digits=10, decimal_places=2)
    image = models.ImageField(verbose_name='Изображение', upload_to='recipes/', blank=True, null=True)