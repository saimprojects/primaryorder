from django.urls import path
from .views import (
    CartListView, 
    CartAddView, 
    CartUpdateView, 
    CartRemoveView,
    CartSyncView,
    ClearCartView
)

urlpatterns = [
    path('', CartListView.as_view(), name='cart-list'),
    path('add/', CartAddView.as_view(), name='cart-add'),
    path('update/', CartUpdateView.as_view(), name='cart-update'),
    path('remove/', CartRemoveView.as_view(), name='cart-remove'),
    path('clear/', ClearCartView.as_view(), name='cart-clear'),
    path('sync/', CartSyncView.as_view(), name='cart-sync'),
]