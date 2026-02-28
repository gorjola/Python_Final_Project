from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.db import models
from decimal import Decimal


class Station(models.Model):
    name = models.CharField(max_length=100, verbose_name="სადგურის სახელი")
    city = models.CharField(max_length=100, verbose_name="ქალაქი")
    image = models.ImageField(upload_to='stations/', null=True, blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = "სადგური"
        verbose_name_plural = "სადგურები"

    def __str__(self):
        return f"{self.name} ({self.city})"


class Train(models.Model):
    TRAIN_TYPES = [
        ('express', 'ექსპრესი'),
        ('passenger', 'სამგზავრო'),
    ]

    number = models.CharField(max_length=20, unique=True, verbose_name="მატარებლის ნომერი")
    train_type = models.CharField(max_length=20, choices=TRAIN_TYPES, default='passenger')
    total_seats = models.PositiveIntegerField(default=100, verbose_name="სავარძლების რაოდენობა")
    image = models.ImageField(upload_to='trains/', null=True, blank=True)

    class Meta:
        verbose_name = "მატარებელი"
        verbose_name_plural = "მატარებლები"

    def __str__(self):
        return f"{self.number} ({self.get_train_type_display()})"


class Route(models.Model):
    route_name = models.CharField(max_length=100, verbose_name="მარშრუტის სახელი")
    train = models.ForeignKey(Train, on_delete=models.CASCADE, related_name='routes')
    departure_station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='departures')
    arrival_station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='arrivals')
    departure_time = models.DateTimeField(verbose_name="გასვლის დრო")
    arrival_time = models.DateTimeField(verbose_name="ჩასვლის დრო")
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['departure_time']
        verbose_name = "მარშრუტი"
        verbose_name_plural = "მარშრუტები"

    def __str__(self):
        return f"{self.train} | {self.departure_station} → {self.arrival_station}"

    def clean(self):
        if self.arrival_time <= self.departure_time:
            raise ValidationError("ჩასვლის დრო უნდა იყოს გასვლის დროზე მეტი")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def duration(self):

        return self.arrival_time - self.departure_time

    @property
    def available_seats_count(self):

        booked = self.bookings.count()
        return self.train.total_seats - booked


class Booking(models.Model):
    SEAT_TYPES = [
        ('standard', 'სტანდარტული'),
        ('business', 'ბიზნესი'),
        ('first', 'პირველი კლასი'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='bookings')
    seat_number = models.PositiveIntegerField(verbose_name="სავარძლის ნომერი")
    seat_type = models.CharField(max_length=20, choices=SEAT_TYPES, default='standard')
    final_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="საბოლოო ფასი",
        null=True,
        blank=True
    )
    booking_date = models.DateTimeField(auto_now_add=True)



    class Meta:
        ordering = ['-booking_date']
        verbose_name = "დაჯავშნა"
        verbose_name_plural = "დაჯავშნები"
        unique_together = ['route', 'seat_number']

    def save(self, *args, **kwargs):

        multipliers = {
            'standard': Decimal('1.0'),
            'business': Decimal('1.5'),
            'first': Decimal('2.0'),
        }


        multiplier = multipliers.get(self.seat_type, Decimal('1.0'))


        self.final_price = self.route.price * multiplier


        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} | სავარძელი #{self.seat_number} ({self.get_seat_type_display()} | {self.final_price})"