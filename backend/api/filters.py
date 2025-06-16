import django_filters
from recipes.models import Recipe, Favorite, ShoppingCart, Ingredient


class RecipeFilter(django_filters.FilterSet):
    author = django_filters.NumberFilter(
        field_name='author__id',
        lookup_expr='exact'
    )
    is_favorited = django_filters.TypedChoiceFilter(
        method='filter_favorited',
        choices=((0, 'False'), (1, 'True')),
        coerce=lambda x: bool(int(x)),
    )
    is_in_shopping_cart = django_filters.TypedChoiceFilter(
        method='filter_in_cart',
        choices=((0, 'False'), (1, 'True')),
        coerce=lambda x: bool(int(x)),
    )

    class Meta:
        model = Recipe
        fields = ['author', 'is_favorited', 'is_in_shopping_cart']

    def init(self, data=None, queryset=None, *, request=None, prefix=None):
        super().init(
            data=data,
            queryset=queryset,
            request=request,
            prefix=prefix
        )

    def filter_favorited(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(
                id__in=Favorite.objects.filter(user=self.request.user)
                .values_list('recipe_id', flat=True)
            )
        return queryset

    def filter_in_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(
                id__in=ShoppingCart.objects.filter(user=self.request.user)
                .values_list('recipe_id', flat=True)
            )
        return queryset


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith',
    )

    class Meta:
        model = Ingredient
        fields = ['name']