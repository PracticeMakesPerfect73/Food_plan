from django.contrib import admin
from django.utils.html import format_html
from .models import Recipe


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'preview_image',)

    def preview_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="60" height="60" />', obj.image.url)
        return '-'

    preview_image.short_description = 'Превью'


admin.site.register(Recipe, RecipeAdmin)
