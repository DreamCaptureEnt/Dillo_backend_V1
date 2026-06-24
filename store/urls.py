from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import *

router = DefaultRouter()
router.register('saree-categories', SareeCategoryViewSet, basename='saree-category')
router.register('occasion-categories', OccasionCategoryViewSet, basename='occasion-category')
router.register('sarees', SareeViewSet, basename='saree')
router.register('addresses', AddressViewSet, basename='address')
router.register('cart', CartViewSet, basename='cart')
router.register('orders', OrderViewSet, basename='order')
router.register('wishlist', WishlistViewSet, basename='wishlist')
router.register('reviews', ReviewViewSet, basename='review')
router.register('admin/users', AdminUserViewSet, basename='admin-user')
router.register('admin/video-shopping', AdminVideoShoppingBookingViewSet, basename='admin-video-shopping')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/me/', MeView.as_view(), name='me'),
    path('admin/dashboard/', dashboard_summary, name='admin-dashboard'),


    # ── Video Shopping ────────────────────────────────────────────────────────
    path('video-shopping/booked-slots/', video_shopping_booked_slots, name='vs-slots'),
    path('video-shopping/book/', video_shopping_book, name='vs-book'),
]
