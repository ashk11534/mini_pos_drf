from django.urls import path

from . import views

urlpatterns = [
    path('products/', views.product_list, name='product-list'),
    path('products/create', views.create_product, name='create-product'),
    path('products/<int:pk>', views.product_detail, name='product-detail'),
    path('products/<int:pk>/update/', views.update_product, name='update-product'),
    path('products/<int:pk>/delete', views.delete_product, name='delete-product'),
    path('products/<int:pk>/sell/', views.sell_product, name='sell-product'),
    # path('orders/', views.create_order, name='create-order'),
    path('orders/<int:pk>/', views.order_detail, name='order-detail'),
    path('orders/', views.order_list, name='order-list'),
    path('orders/<int:pk>/cancel/', views.cancel_order, name='cancel-order')

    # path('hello/', views.hello_api, name='hello-api'),
    # path('products/validate', views.validate_product, name='validate-product'),
]
