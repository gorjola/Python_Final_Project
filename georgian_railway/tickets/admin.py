from django.contrib import admin
from .models import Station, Train, Route, Booking


class RouteInline(admin.TabularInline):
    model = Route
    extra = 1
    fields = ['departure_station', 'arrival_station', 'departure_time', 'price']


class BookingInline(admin.TabularInline):
    model = Booking
    extra = 0
    readonly_fields = ['booking_date']
    fields = ['user', 'seat_number', 'seat_type', 'booking_date']


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'image_preview']
    search_fields = ['name', 'city']
    list_filter = ['city']


    fields = ['name', 'city', 'image']
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-height: 50px; border-radius: 4px;" />'
        return "❌ სურათი არ არის"

    image_preview.allow_tags = True
    image_preview.short_description = "სურათი"


@admin.register(Train)
class TrainAdmin(admin.ModelAdmin):
    list_display = ['number', 'train_type', 'total_seats', 'image_preview']
    list_filter = ['train_type']
    search_fields = ['number']
    inlines = [RouteInline]


    fields = ['number', 'train_type', 'total_seats', 'image']
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-height: 50px; border-radius: 4px;" />'
        return "❌ სურათი არ არის"

    image_preview.allow_tags = True
    image_preview.short_description = "სურათი"


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ['route_name', 'train', 'departure_station', 'arrival_station',
                    'departure_time', 'arrival_time', 'price', 'is_active']
    list_filter = ['is_active', 'departure_station', 'arrival_station', 'train__train_type']
    search_fields = ['train__number', 'route_name']
    date_hierarchy = 'departure_time'
    inlines = [BookingInline]
    list_editable = ['price', 'is_active']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'route', 'seat_number', 'seat_type', 'booking_date']
    list_filter = ['seat_type', 'booking_date', 'route__departure_station']
    search_fields = ['user__username', 'user__email', 'route__train__number']
    date_hierarchy = 'booking_date'
    list_select_related = ['user', 'route', 'route__train']