"""Api urls."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views


app_name = 'api'

router_v1 = DefaultRouter()

router_v1.register(
    r'users',
    views.UserViewSet,
    basename='users',
)
router_v1.register(
    'recipes',
    views.RecipeViewSet,
    basename='recipes'
)
router_v1.register(
    'ingredients',
    views.IngredientViewSet,
    basename='ingredients'
)
router_v1.register(
    'tags',
    views.TagViewSet,
    basename='tags'
)
# router_v1.register(
#     r'titles/(?P<title_id>\d+)/reviews',
#     views.ReviewViewSet,
#     basename='reviews'
# )
# router_v1.register(
#     r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
#     views.CommentViewSet,
#     basename='comments'
# )
# router_v1.register(
#     'categories',
#     views.CategoriesViewSet,
#     basename='categories'
# )
# router_v1.register(
#     'genres',
#     views.GenresViewSet,
#     basename='genres'
# )
# router_v1.register(
#     'titles',
#     views.TitlesViewSet,
#     basename='titles'
# )
# router_v1.register(
#     r'users',
#     views.UserViewSet,
#     basename='users',
# )

# signup_urls = [
#     path('auth/signup/', views.SignUPAPIView.as_view()),
#     path('auth/token/', views.TokenAPIView.as_view()),
# ]

urlpatterns = [
    # path('v1/', include(signup_urls)),
    path('', include(router_v1.urls)),
]
