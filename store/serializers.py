from decimal import Decimal

from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
import datetime

from .models import (
    Address,
    Cart,
    CartItem,
    OccasionCategory,
    Order,
    OrderItem,
    Review,
    Saree,
    SareeCategory,
    WishlistItem,
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined']
        read_only_fields = ['id', 'is_staff', 'date_joined']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        Cart.objects.get_or_create(user=user)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs['username'], password=attrs['password'])
        if not user:
            raise serializers.ValidationError('Invalid username or password.')
        if not user.is_active:
            raise serializers.ValidationError('This account is inactive.')
        attrs['user'] = user
        return attrs


class SareeCategorySerializer(serializers.ModelSerializer):
    count = serializers.IntegerField(source='sarees.count', read_only=True)

    class Meta:
        model = SareeCategory
        fields = ['id', 'name', 'slug', 'name_ta', 'icon', 'is_active', 'sort_order', 'count']


class OccasionCategorySerializer(serializers.ModelSerializer):
    count = serializers.IntegerField(source='sarees.count', read_only=True)

    class Meta:
        model = OccasionCategory
        fields = ['id', 'name', 'slug', 'is_active', 'sort_order', 'count']


class SareeSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)
    occasion_name = serializers.CharField(source='occasion.name', read_only=True)
    occasion_slug = serializers.CharField(source='occasion.slug', read_only=True)
    in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Saree
        fields = [
            'id', 'name', 'name_ta', 'slug', 'category', 'category_name', 'category_slug',
            'occasion', 'occasion_name', 'occasion_slug', 'saree_type', 'description',
            'information', 'tags', 'colors', 'images', 'video_url', 'price', 'original_price',
            'discount', 'stock_count', 'in_stock', 'rating', 'review_count', 'is_new',
            'is_featured', 'is_bestseller', 'is_active', 'created_at', 'updated_at',
        ]


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'first_name', 'last_name', 'email', 'phone', 'address', 'landmark', 'city', 'state', 'pincode', 'is_default']

    def create(self, validated_data):
        return Address.objects.create(user=self.context['request'].user, **validated_data)


class CartItemSerializer(serializers.ModelSerializer):
    saree_detail = SareeSerializer(source='saree', read_only=True)
    line_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'saree', 'saree_detail', 'selected_color', 'selected_size', 'quantity', 'line_total']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'subtotal']

    def get_subtotal(self, obj):
        return sum((item.line_total for item in obj.items.select_related('saree')), Decimal('0'))


class OrderItemSerializer(serializers.ModelSerializer):
    line_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'saree', 'product_snapshot', 'selected_color', 'selected_size', 'quantity', 'price', 'line_total']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user_detail = UserSerializer(source='user', read_only=True)
    ip_address = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=45)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'user_detail', 'status', 'payment_method',
            'payment_status', 'shipping_address', 'subtotal', 'discount', 'shipping',
            'total', 'notes', 'order_source', 'device_info', 'ip_address',
            'coupon_code', 'items', 'created_at', 'updated_at',
        ]
        read_only_fields = ['order_number', 'user']


class CreateOrderItemSerializer(serializers.Serializer):
    saree = serializers.PrimaryKeyRelatedField(queryset=Saree.objects.filter(is_active=True))
    selected_color = serializers.CharField(required=False, allow_blank=True)
    selected_size = serializers.CharField(required=False, allow_blank=True)
    quantity = serializers.IntegerField(min_value=1)


class CreateOrderSerializer(serializers.Serializer):
    items = CreateOrderItemSerializer(many=True)
    shipping_address = serializers.JSONField()
    payment_method = serializers.ChoiceField(choices=Order.PAYMENT_METHOD_CHOICES, default='cod')
    order_source = serializers.ChoiceField(choices=Order.SOURCE_CHOICES, default='website')
    discount = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    coupon_code = serializers.CharField(required=False, allow_blank=True, max_length=40)
    device_info = serializers.CharField(required=False, allow_blank=True, max_length=200)
    notes = serializers.CharField(required=False, allow_blank=True)


class ReviewSerializer(serializers.ModelSerializer):
    user_detail = UserSerializer(source='user', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'saree', 'user', 'user_detail', 'rating', 'title', 'content', 'is_approved', 'created_at']
        read_only_fields = ['user', 'is_approved']

    def create(self, validated_data):
        return Review.objects.create(user=self.context['request'].user, **validated_data)


class WishlistItemSerializer(serializers.ModelSerializer):
    saree_detail = SareeSerializer(source='saree', read_only=True)

    class Meta:
        model = WishlistItem
        fields = ['id', 'saree', 'saree_detail', 'created_at']

    def create(self, validated_data):
        item, _ = WishlistItem.objects.get_or_create(user=self.context['request'].user, **validated_data)
        return item


class VideoShoppingBookingSerializer(serializers.ModelSerializer):
    time_slot_display = serializers.ReadOnlyField()
 
    class Meta:
        from store.models import VideoShoppingBooking  # lazy import for standalone snippet
        model = VideoShoppingBooking
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "date",
            "time_slot",
            "time_slot_display",
            "note",
            "meet_link",
            "status",
            "attendee_name",
            "created_at",
        ]
        read_only_fields = ["id", "meet_link", "status", "created_at", "time_slot_display"]
 
    # ── Validation ────────────────────────────────────────────────────────────
 
    def validate_date(self, value):
        today = datetime.date.today()
        if value <= today:
            raise serializers.ValidationError("Please choose a future date (from tomorrow onwards).")
        return value
 
    def validate_time_slot(self, value):
        """Accept only valid 30-min slots between 09:00 and 20:30."""
        valid_slots = set()
        h, m = 9, 0
        while h < 20 or (h == 20 and m <= 30):
            valid_slots.add(f"{h:02d}:{m:02d}")
            m += 30
            if m >= 60:
                m = 0
                h += 1
        if value not in valid_slots:
            raise serializers.ValidationError(
                f"Invalid slot '{value}'. Must be a 30-minute interval between 09:00 and 20:30."
            )
        return value
 
    def validate(self, attrs):
        from store.models import VideoShoppingBooking
        date = attrs.get("date")
        time_slot = attrs.get("time_slot")
        if date and time_slot:
            if VideoShoppingBooking.objects.filter(date=date, time_slot=time_slot).exists():
                raise serializers.ValidationError(
                    {"time_slot": "This slot is already booked. Please choose a different time."}
                )
        return attrs


class AdminVideoShoppingBookingSerializer(VideoShoppingBookingSerializer):
    class Meta(VideoShoppingBookingSerializer.Meta):
        fields = VideoShoppingBookingSerializer.Meta.fields + ["updated_at"]
        read_only_fields = [
            "id",
            "name",
            "email",
            "phone",
            "date",
            "time_slot",
            "time_slot_display",
            "note",
            "meet_link",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        status_value = attrs.get("status")
        attendee_name = attrs.get("attendee_name")
        existing_attendee_name = getattr(self.instance, "attendee_name", "")

        if status_value == "completed" and not (attendee_name or existing_attendee_name).strip():
            raise serializers.ValidationError(
                {"attendee_name": "Please enter the attendee name before marking completed."}
            )
        return attrs
