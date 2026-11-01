from django.db import transaction
from django.shortcuts import get_object_or_404, render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Order, OrderItem, Product
from .permissions import CanManageProduct, IsAdminUser
from .serializers import (OrderCreateSerializer, OrderReadSerializer,
                          ProductSerializer)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def product_list(request):
    if request.method == 'GET':
        products = Product.objects.all()

        paginator = PageNumberPagination()
        paginator.page_size = 2

        result_page = paginator.paginate_queryset(products, request)

        serializer = ProductSerializer(result_page, many=True)

        return paginator.get_paginated_response(serializer.data)

    elif request.method == 'POST':
        serializer = ProductSerializer(data=request.data)

        if serializer.is_valid():
            product = serializer.save()
            return Response(
                ProductSerializer(product).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([CanManageProduct])
def create_product(request):
    serializer = ProductSerializer(data=request.data)

    if serializer.is_valid():
        product = serializer.save()

        return Response(
            ProductSerializer(product).data,
            status=status.HTTP_201_CREATED
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )

@api_view(['GET'])
def product_detail(request, pk):
    # try:
    #     product = Product.objects.get(pk=pk)
    # except Product.DoesNotExist:
    #     return Response(
    #         {'error': 'Product not found!'},
    #         status=status.HTTP_404_NOT_FOUND
    #     )
    product = get_object_or_404(Product, pk=pk)
    serializer = ProductSerializer(product)
    return Response(serializer.data)

@api_view(['PUT', 'PATCH'])
def update_product(request, pk):
    # try:
    #     product = Product.objects.get(pk=pk)
    # except Product.DoesNotExist:
    #     return Response(
    #         {'error': 'Product not found!'},
    #         status=status.HTTP_404_NOT_FOUND
    #     )
    product = get_object_or_404(Product, pk=pk)

    partial = request.method == 'PATCH'

    serializer = ProductSerializer(
        product,
        data=request.data,
        partial=partial
    )

    if serializer.is_valid():
        updated_product = serializer.save()
        return Response(ProductSerializer(updated_product).data)

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )

@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_product(request, pk):
    # try:
    #     product = Product.objects.get(pk=pk)
    # except Product.DoesNotExist:
    #     return Response(
    #         {'error': 'Product not found'},
    #         status=status.HTTP_404_NOT_FOUND
    #     )
    product = get_object_or_404(Product, pk=pk)

    product.delete()

    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
def sell_product(request, pk):
    quantity = request.data.get('quantity')

    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
        return Response(
            {'error': 'Quantity must be a positive integer.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    with transaction.atomic():
        try:
            product = Product.objects.select_for_update().get(pk=pk)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        if product.stock < quantity:
            return Response(
                {'error': 'Insufficient stock.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        product.stock -= quantity
        product.save(update_fields=['stock'])
    return Response({
        'message': 'Sale successful.',
        'product': product.name,
        'quantity_sold': quantity,
        'remaining_stock': product.stock
    })

@api_view(['GET'])
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)

    serializer = OrderReadSerializer(order)

    return Response(serializer.data)

@api_view(['GET', 'POST'])
def order_list(request):
    if request.method == 'GET':
        # orders = Order.objects.all()
        orders = Order.objects.prefetch_related('items__product')
        serializer = OrderReadSerializer(orders, many=True)

        return Response(serializer.data)

    elif request.method == 'POST':
        input_serializer = OrderCreateSerializer(data=request.data)

        # if not input_serializer.is_valid():
        #     return Response(
        #         input_serializer.errors,
        #         status=status.HTTP_400_BAD_REQUEST
        #     )
        input_serializer.is_valid(raise_exception=True)

        items = input_serializer.validated_data['items']

        quantities = {}

        for item in items:
            product_id = item['product_id']
            quantities[product_id] = (
                quantities.get(product_id, 0) + item['quantity']
            )

        with transaction.atomic():
            products = {}

            for product_id in sorted(quantities):
                try:
                    products[product_id] = (
                        Product.objects.select_for_update().get(pk=product_id)
                    )
                except Product.DoesNotExist:
                    return Response(
                        {'error': f'Product {product_id} not found.'},
                        status=status.HTTP_404_NOT_FOUND
                    )

            for product_id, quantity in quantities.items():
                product = products[product_id]

                if product.stock < quantity:
                    return Response(
                        {
                            'error': f'Insufficient stock for {product.name}.',
                            'available': product.stock,
                            'requested': quantity
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            order = Order.objects.create()
            total = 0
            response_items = []

            for product_id, quantity in quantities.items():
                product = products[product_id]
                unit_price = product.price
                subtotal = unit_price * quantity

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price
                )

                product.stock -= quantity
                product.save(update_fields=['stock'])

                total += subtotal
                response_items.append({
                    'product_id': product.pk,
                    'product_name': product.name,
                    'quantity': quantity,
                    'unit_price': str(unit_price),
                    'subtotal': str(subtotal),
                    'remaining_stock': product.stock
                })

        return Response(
            {
                'order_id': order.pk,
                'items': response_items,
                'total': str(total)
            },
            status=status.HTTP_201_CREATED
        )

@api_view(['GET'])
def cancel_order(request, pk):
    with transaction.atomic():
        order = get_object_or_404(
            Order.objects.select_for_update(),
            pk=pk
        )

        if order.is_cancelled:
            return Response(
                {'error': 'Order already cancelled.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        items = order.items.select_related('product')

        for item in items:
            product = Product.objects.select_for_update().get(
                pk=item.product_id
            )

            product.stock += item.quantity
            product.save(update_fields=['stock'])

        order.is_cancelled = True
        order.save(update_fields=['is_cancelled'])

    return Response(
        {'message': 'Order cancelled successfully.'},
        status=status.HTTP_200_OK
    )

# @api_view(['POST'])
# def create_order(request):
#     input_serializer = OrderCreateSerializer(data=request.data)

#     if not input_serializer.is_valid():
#         return Response(
#             input_serializer.errors,
#             status=status.HTTP_400_BAD_REQUEST
#         )
#     items = input_serializer.validated_data['items']

#     quantities = {}

#     for item in items:
#         product_id = item['product_id']
#         quantities[product_id] = (
#             quantities.get(product_id, 0) + item['quantity']
#         )

#     with transaction.atomic():
#         products = {}

#         for product_id in sorted(quantities):
#             try:
#                 products[product_id] = (
#                     Product.objects.select_for_update().get(pk=product_id)
#                 )
#             except Product.DoesNotExist:
#                 return Response(
#                     {'error': f'Product {product_id} not found.'},
#                     status=status.HTTP_404_NOT_FOUND
#                 )

#         for product_id, quantity in quantities.items():
#             product = products[product_id]

#             if product.stock < quantity:
#                 return Response(
#                     {
#                         'error': f'Insufficient stock for {product.name}.',
#                         'available': product.stock,
#                         'requested': quantity
#                     },
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
#         order = Order.objects.create()
#         total = 0
#         response_items = []

#         for product_id, quantity in quantities.items():
#             product = products[product_id]
#             unit_price = product.price
#             subtotal = unit_price * quantity

#             OrderItem.objects.create(
#                 order=order,
#                 product=product,
#                 quantity=quantity,
#                 unit_price=unit_price
#             )

#             product.stock -= quantity
#             product.save(update_fields=['stock'])

#             total += subtotal
#             response_items.append({
#                 'product_id': product.pk,
#                 'product_name': product.name,
#                 'quantity': quantity,
#                 'unit_price': str(unit_price),
#                 'subtotal': str(subtotal),
#                 'remaining_stock': product.stock
#             })

#     return Response(
#         {
#             'order_id': order.pk,
#             'items': response_items,
#             'total': str(total)
#         },
#         status=status.HTTP_201_CREATED
#     )
# @api_view(['GET'])
# def hello_api(request):
#     return Response({
#         'message': 'Hello, Ashik',
#         'framework': 'Django Rest Framework'
#     })

# @api_view(['POST'])
# def validate_product(request):
#     serializer = ProductSerializer(data=request.data)

#     if serializer.is_valid():
#         return Response({
#             'message': 'Product data is valid',
#             'data': serializer.validated_data
#         })

#     return Response(serializer.errors, status=400)

# @api_view(['POST'])
# def create_product(request):
#     serializer = ProductSerializer(data=request.data)

#     if serializer.is_valid():
#         product = serializer.save()

#         return Response(
#             ProductSerializer(product).data,
#             status=status.HTTP_201_CREATED
#         )

#     return Response(
#         serializer.errors,
#         status=status.HTTP_400_BAD_REQUEST
#     )

# @api_view(['GET'])
# def product_list(request):
#     products = Product.objects.all()
#     serializer = ProductSerializer(products, many=True)

#     return Response(serializer.data)
