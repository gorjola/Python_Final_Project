from django.urls import path
from . import views

app_name = 'tickets'

urlpatterns = [
    # მთავარი
    path('', views.HomeView.as_view(), name='home'),

    # განრიგი და ძიება
    path('schedule/', views.ScheduleView.as_view(), name='schedule'),
    path('stations/', views.StationListView.as_view(), name='stations'),
    path('train/<int:train_id>/', views.TrainDetailView.as_view(), name='train_detail'),

    # დაჯავშნები
    path('book/<int:route_id>/', views.BookTicketView.as_view(), name='book_ticket'),
    path('history/', views.BookingHistoryView.as_view(), name='booking_history'),
    path('cancel/<int:booking_id>/', views.CancelBookingView.as_view(), name='cancel_booking'),
]