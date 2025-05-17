from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.


class Book(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название")
    author = models.CharField(max_length=200, verbose_name="Автор")
    publisher = models.CharField(max_length=200, verbose_name="Издатель",
                                 blank=True, null=True)
    cost = models.FloatField(verbose_name="Стоимость")

    def __str__(self):
        return self.title

    class Meta:
        db_table = "book"
        verbose_name = "Книга"
        verbose_name_plural = "Книги"
        ordering = ['title']

