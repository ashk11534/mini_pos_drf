from decimal import Decimal

from rest_framework import serializers

from .models import Order, OrderItem, Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'stock']
        read_only_fields = ['id']

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                'Price must be greater than zero.'
            )
        return value

    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError(
                'Stock cannot be negative.'
            )
        return value

class OrderItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)

class OrderCreateSerializer(serializers.Serializer):
    items = OrderItemInputSerializer(many=True, allow_empty=False)

class OrderItemReadSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(
        source='product.name',
        read_only=True
    )

    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            'id',
            'product',
            'product_name',
            'quantity',
            'unit_price',
            'subtotal'
        ]
    def get_subtotal(self, obj):
        return obj.unit_price * obj.quantity

class OrderReadSerializer(serializers.ModelSerializer):
    items = OrderItemReadSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'created_at', 'items', 'total']

    def get_total(self, obj):
        total = Decimal('0.00')

        for item in obj.items.all():
            total += item.unit_price * item.quantity

        return total


















# class ProductSerializer(serializers.Serializer):
#     id = serializers.IntegerField(read_only=True)
#     name = serializers.CharField(max_length=100)
#     price = serializers.DecimalField(
#         max_digits=10,
#         decimal_places=2
#     )
#     stock = serializers.IntegerField(min_value=0)
