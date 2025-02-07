from django.urls import path
from .views import SignUpView, SigninView, LogoutView, ProfileView
from .views import LeadListCreateView, LeadRetrieveUpdateDeleteView
from .views import ReviewListCreateView, ReviewRetrieveUpdateDeleteView
from .views import WishlistView, CartView, download_lead_pdf, AddressView
from .views import FillDetailsView, CreateOrderView, ProcessPaymentView

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('signin/', SigninView.as_view(), name='signin'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('leads/', LeadListCreateView.as_view(), name='lead-list-create'),
    path('leads/<int:lead_id>/', LeadRetrieveUpdateDeleteView.as_view(), name='lead-detail'),
    path('leads/<int:lead_id>/reviews/', ReviewListCreateView.as_view(), name='review-list-create'),
    path('reviews/<int:review_id>/', ReviewRetrieveUpdateDeleteView.as_view(), name='review-detail'),
    path('wishlists/', WishlistView.as_view(), name='wishlist-list'),
    path('wishlists/<int:lead_id>/', WishlistView.as_view(), name='wishlist-manage'),
    path('cart/', CartView.as_view(), name='cart-list'),
    path('cart/<int:lead_id>/', CartView.as_view(), name='cart-manage'),
    path("leads/download/<int:lead_id>/", download_lead_pdf, name="download_leads_pdf"),
    path('addresses/', AddressView.as_view(), name='addresses'),
    path('orders/fill-details/', FillDetailsView.as_view(), name='fill-details'),
    path('orders/', CreateOrderView.as_view(), name='create-order'),
    path('orders/<int:order_id>/pay/', ProcessPaymentView.as_view(), name='process-payment'),
]