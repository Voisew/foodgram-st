from django.contrib import admin
from django.db.models import Count

from .models import (
    Ingredient,
    Recipe,
    IngredientsInRecipe,
    Favorite,
    ShoppingCart,
)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit',
    )
    search_fields = (
        'name',
    )


class IngredientsInRecipeInline(admin.TabularInline):
    model = IngredientsInRecipe
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'author',
        'favorites_count'
    )
    search_fields = (
        'name',
        'author__username',
        'author__email',
    )
    inlines = [IngredientsInRecipeInline]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(fav_count=Count('recipe_favorite'))

    @admin.display(description='Добавлений в избранное')
    def favorites_count(self, obj):
        return obj.fav_count


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe',
    )


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe',
    )


@admin.register(IngredientsInRecipe)
class IngredientsInRecipeAdmin(admin.ModelAdmin):
    list_display = (
        'recipe',
        'ingredient',
        'amount',
    )