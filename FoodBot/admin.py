from django.contrib import admin
from django import forms
from .models import Recipe, UserProfile
from django.utils.html import format_html


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'preview_image',)

    def preview_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="60" height="60" />', obj.image.url)
        return '-'

    preview_image.short_description = 'Превью'


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['favorite_recipes'].queryset = self.instance.favorite_recipes.all()


class UserProfileAdmin(admin.ModelAdmin):
    form = UserProfileForm
    list_display = ('user_id', 'is_premium',)


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
