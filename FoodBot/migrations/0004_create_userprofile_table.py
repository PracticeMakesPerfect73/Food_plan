from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('FoodBot', '0003_alter_userprofile_is_premium'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.BigIntegerField(unique=True, verbose_name='Telegram ID')),
                ('is_premium', models.BooleanField(default=False, verbose_name='Платная подписка:')),
            ],
        ),
        migrations.AddField(
            model_name='userprofile',
            name='favorite_recipes',
            field=models.ManyToManyField(blank=True, related_name='favorited_by', to='FoodBot.recipe', verbose_name='ID избранных рецептов:'),
        ),
    ]
