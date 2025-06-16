import os
import tempfile

from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404
from django.http import FileResponse

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

from rest_framework.permissions import (
    IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
)
from .permissions import IsAuthorOrReadOnly

from django_filters.rest_framework import DjangoFilterBackend
from .filters import RecipeFilter, IngredientFilter

from .serializers import (
    IngredientSerializer,
    RecipeSerializer,
    RecipeCreateSerializer,
    RecipeShortSerializer,
    UserSerializer,
    RegisterSerializer,
    PasswordSerializer,
    FollowSerializer,
    ShoppingCartSerializer,
    AvatarSerializer
)

from recipes.models import (
    Ingredient,
    Recipe,
    Favorite,
    ShoppingCart,
    IngredientsInRecipe
)
from users.models import User, Follow


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        if user.is_authenticated:
            context['favorited_ids'] = set(
                Favorite.objects.filter(user=user)
                .values_list('recipe_id', flat=True)
            )
        else:
            context['favorited_ids'] = set()
        return context

    @action(
        detail=True,
        methods=("get",),
        permission_classes=(IsAuthenticatedOrReadOnly,),
        url_path="get-link",
        url_name="get-link",
    )
    def get_link(self, request, pk):
        instance = self.get_object()

        url = f"{request.get_host()}/s/{instance.id}"

        return Response(data={"short-link": url})

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        return self._handle_add_relation(request, Favorite)

    @favorite.mapping.delete
    def remove_favorite(self, request, pk=None):
        return self._handle_remove_relation(request, Favorite)

    def _handle_add_relation(self, request, model):
        recipe = self.get_object()
        user = request.user
        if model.objects.filter(user=user, recipe=recipe).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        model.objects.create(user=user, recipe=recipe)
        return Response(
            RecipeShortSerializer(recipe).data,
            status=status.HTTP_201_CREATED,
        )

    def _handle_remove_relation(self, request, model):
        recipe = self.get_object()
        user = request.user
        relation = model.objects.filter(user=user, recipe=recipe)
        if not relation.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        relation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=("post", "delete"),
        permission_classes=(IsAuthenticated,),
        url_path="shopping_cart",
        url_name="shopping_cart",
    )
    def shopping_cart(self, request, pk):
        if request.method == "POST":
            return self.recordUsersRecipe(
                request, pk, ShoppingCartSerializer
            )
        return self.deleteUsersRecipe(
            request, pk, "shopping_cart", ShoppingCart.DoesNotExist
        )

    def recordUsersRecipe(self, request, pk, serializerClass):
        if not Recipe.objects.filter(pk=pk).exists():
            raise NotFound(detail="Не существует такого рецепта!")
        serializer = serializerClass(
            data={
                "user": request.user.id,
                "recipe": pk,
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def deleteUsersRecipe(
        self,
        request,
        pk,
        related_name_for_user,
        notFoundException,
    ):
        get_object_or_404(Recipe, pk=pk)
        try:
            getattr(request.user, related_name_for_user).get(
                user=request.user, recipe_id=pk
            ).delete()
        except notFoundException:
            return Response(
                'Рецепт не найден!',
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='download_shopping_cart',
        url_name='download_shopping_cart'
    )
    def download_shopping_cart(self, request):
        recipe_ids = ShoppingCart.objects.filter(
            user=request.user
        ).values_list('recipe_id', flat=True)

        ingredients = (
            IngredientsInRecipe.objects.filter(recipe_id__in=recipe_ids)
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(totalSum=Sum("amount"))
        )

        if not ingredients:
            return Response(
                {"detail": "Ваша корзина пуста."},
                status=status.HTTP_400_BAD_REQUEST
            )
        txtContent = self.convertToTXT(ingredients)
        return self.responseFromFile(txtContent, file_name='shopping_cart.txt')

    def convertToTXT(self, ingredients):
        result = []
        for ingredient in ingredients:
            name = ingredient['ingredient__name']
            unit = ingredient['ingredient__measurement_unit']
            amount = ingredient['totalSum']
            result.append(f"{name} - {amount} ({unit})")
        return "\n".join(result)

    def responseFromFile(self, text, file_name):
        fd, path = tempfile.mkstemp(suffix='.txt')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as tmp:
                tmp.write(text)

            return FileResponse(
                open(path, 'rb'),
                as_attachment=True,
                filename=file_name,
                content_type='text/plain'
            )
        except Exception as e:
            raise e
        finally:
            pass


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'create':
            return RegisterSerializer
        return UserSerializer

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path="me",
    )
    def me(self, request):
        serializer = self.get_serializer(
            request.user,
            context=self.get_serializer_context()
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='set_password',
    )
    def set_password(self, request):
        serializer = PasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(
                    serializer.validated_data['current_password']):
                return Response(
                    {'current_password': ['Неверный пароль.']},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request):
        user = request.user
        recipes_limit = request.query_params.get('recipes_limit')

        queryset = User.objects.filter(following__user=user) \
            .annotate(recipes_count=Count('recipe'))
        page = self.paginate_queryset(queryset)

        context = self.get_serializer_context()
        context['recipes_limit'] = recipes_limit

        serializer = FollowSerializer(page, many=True, context=context)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, pk=None):
        user = request.user
        author = self.get_object()

        if author == user or \
                Follow.objects.filter(user=user, following=author).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        Follow.objects.create(user=user, following=author)

        serializer = FollowSerializer(
            author,
            context=self._get_follow_context(request),
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk=None):
        user = request.user
        author = self.get_object()

        follow = Follow.objects.filter(user=user, following=author)
        if not follow.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _get_follow_context(self, request):
        return {
            'request': request,
            'recipes_limit': request.query_params.get('recipes_limit')
        }

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar',
    )
    def avatar(self, request):
        return self.update_avatar(request) if request.method == "PUT" \
            else self.delete_avatar(request)

    def update_avatar(self, request):
        user = request.user
        serializer = AvatarSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            avatar_url = request.build_absolute_uri(user.avatar.url)
            return Response({"avatar": avatar_url},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)

    def delete_avatar(self, request):
        user = request.user
        if user.avatar:
            user.avatar.delete(save=False)
            user.avatar = None
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)