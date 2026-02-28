from django import forms
from django.utils import timezone
from .models import Station, Booking


class RouteSearchForm(forms.Form):
    departure_station = forms.ModelChoiceField(
        queryset=Station.objects.all(),
        required=False,
        empty_label="გასვლის სადგური",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    arrival_station = forms.ModelChoiceField(
        queryset=Station.objects.all(),
        required=False,
        empty_label="ჩასვლის სადგური",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'min': timezone.now().date().isoformat()
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        departure = cleaned_data.get('departure_station')
        arrival = cleaned_data.get('arrival_station')

        if departure and arrival and departure == arrival:
            raise forms.ValidationError('გასვლის და ჩასვლის სადგური უნდა იყოს განსხვავებული!')

        return cleaned_data


class BookingForm(forms.Form):
    SEAT_TYPES = [
        ('standard', 'სტანდარტული'),
        ('business', 'ბიზნესი'),
        ('first', 'პირველი კლასი'),
    ]

    seat_number = forms.IntegerField(
        widget=forms.HiddenInput()
    )
    seat_type = forms.ChoiceField(
        choices=SEAT_TYPES,
        initial='standard',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, available_seats=None, **kwargs):
        self.available_seats = available_seats or []
        super().__init__(*args, **kwargs)

    def clean_seat_number(self):
        seat = self.cleaned_data['seat_number']
        if self.available_seats and seat not in self.available_seats:
            raise forms.ValidationError('ეს სავარძელი უკვე დაჯავშნილია ან არ არსებობს!')
        return seat