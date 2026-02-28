from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db.models import Q, Count
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView, ListView, FormView, DeleteView, DetailView
from .models import Station, Train, Route, Booking
from .forms import BookingForm, RouteSearchForm


class HomeView(TemplateView):
    template_name = 'tickets/home.html'


class ScheduleView(ListView):
    model = Route
    template_name = 'tickets/schedule.html'
    context_object_name = 'routes'

    def get_queryset(self):
        # ძირითადი queryset - აქტიური და მომავალი მარშრუტები
        queryset = Route.objects.filter(
            is_active=True,
            departure_time__gte=timezone.now()
        ).select_related('train', 'departure_station', 'arrival_station')

        # ფორმის შექმნა GET პარამეტრებით
        self.form = RouteSearchForm(self.request.GET or None)

        if self.form.is_valid():
            departure = self.form.cleaned_data.get('departure_station')
            arrival = self.form.cleaned_data.get('arrival_station')
            date = self.form.cleaned_data.get('date')

            if departure:
                queryset = queryset.filter(departure_station=departure)
            if arrival:
                queryset = queryset.filter(arrival_station=arrival)
            if date:
                queryset = queryset.filter(departure_time__date=date)

        return queryset

    def get_context_data(self, **kwargs):
        # კონტექსტში ფორმის დამატება
        context = super().get_context_data(**kwargs)
        context['form'] = self.form
        return context


class BookTicketView(LoginRequiredMixin, FormView):
    template_name = 'tickets/book_ticket.html'
    form_class = BookingForm

    def dispatch(self, request, *args, **kwargs):
        self.route_id = self.kwargs.get('route_id')
        self.route = get_object_or_404(
            Route,
            id=self.route_id,
            is_active=True
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        #თავისუფალი ადგილების გადაცემა ფორმებში
        kwargs = super().get_form_kwargs()
        booked_seats = list(
            Booking.objects.filter(route=self.route)
            .values_list('seat_number', flat=True)
        )
        kwargs['available_seats'] = [
            i for i in range(1, self.route.train.total_seats + 1)
            if i not in booked_seats
        ]
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['route'] = self.route

        booked_seats = list(
            Booking.objects.filter(route=self.route)
            .values_list('seat_number', flat=True)
        )
        total_seats = self.route.train.total_seats

        context['booked_seats'] = booked_seats
        context['available_seats'] = [i for i in range(1, total_seats + 1) if i not in booked_seats]
        context['all_seats'] = list(range(1, total_seats + 1))

        return context

    @transaction.atomic
    def form_valid(self, form):
        seat_number = form.cleaned_data['seat_number']

        # ორმაგი შემოწმება (race condition-ისთვის)
        is_booked = Booking.objects.select_for_update().filter(
            route=self.route,
            seat_number=seat_number
        ).exists()

        if is_booked:
            messages.error(self.request, 'ეს სავარძელი უკვე დაჯავშნილია!')
            return redirect('tickets:book_ticket', route_id=self.route_id)

        Booking.objects.create(
            user=self.request.user,
            route=self.route,
            seat_number=seat_number,
            seat_type=form.cleaned_data.get('seat_type', 'standard')
        )

        messages.success(
            self.request,
            f'ბილეთი წარმატებით დაჯავშნეთ! სავარძელი #{seat_number}'
        )
        return redirect('tickets:booking_history')

    def form_invalid(self, form):
        messages.error(self.request, 'ფორმა არასწორია. გთხოვთ შეამოწმოთ მონაცემები.')
        return self.render_to_response(self.get_context_data(form=form))


class BookingHistoryView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'tickets/booking_history.html'
    context_object_name = 'bookings'

    def get_queryset(self):
        return Booking.objects.filter(
            user=self.request.user
        ).select_related(
            'route',
            'route__train',
            'route__departure_station',
            'route__arrival_station'
        ).order_by('-booking_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()


        bookings = list(context['bookings'])  # list() რომ ორჯერ არ გავიმეოროთ query

        context['active_bookings'] = [b for b in bookings if b.route.departure_time > now]
        context['past_bookings'] = [b for b in bookings if b.route.arrival_time <= now]
        context['now'] = [b for b in bookings if b.route.departure_time <= now < b.route.arrival_time]

        return context


class CancelBookingView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Booking
    pk_url_kwarg = 'booking_id'
    template_name = 'tickets/cancel_booking.html'
    success_url = reverse_lazy('tickets:booking_history')

    def test_func(self):
        # მხოლოდ თავისი დაჯავშნის გაუქმება შეუძლია
        booking = self.get_object()
        return booking.user == self.request.user

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # ვამოწმებთ არის თუ არა მატარებელი უკვე გასული
        if self.object.route.departure_time < timezone.now():
            messages.error(request, 'ამ მატარებლის დაჯავშნის გაუქმება შეუძლებელია!')
        else:
            self.object.delete()
            messages.success(request, 'დაჯავშნა წარმატებით გაუქმდა!')

        return redirect(self.get_success_url())


class StationListView(ListView):
    model = Station
    template_name = 'tickets/stations.html'
    context_object_name = 'stations'

    def get_queryset(self):
        now = timezone.now()
        return Station.objects.annotate(
            active_departures_count=Count(
                'departures',
                filter=Q(departures__departure_time__gte=now),
                distinct=True
            ),
            active_arrivals_count=Count(
                'arrivals',
                filter=Q(arrivals__arrival_time__gte=now),
                distinct=True
            )
        )


class TrainDetailView(DetailView):
    model = Train
    pk_url_kwarg = 'train_id'
    template_name = 'tickets/train_detail.html'
    context_object_name = 'train'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # მატარებლის აქტიური მარშრუტები
        context['routes'] = self.object.routes.filter(is_active=True)
        return context