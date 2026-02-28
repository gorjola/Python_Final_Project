from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView

from .forms import RegisterForm, ProfileUpdateForm
from tickets.models import Booking


class RegisterView(FormView):
    form_class = RegisterForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('tickets:home')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, 'რეგისტრაცია წარმატებით დასრულდა!')
        return super().form_valid(form)


class UserLoginView(LoginView):
    template_name = 'users/login.html'

    def form_valid(self, form):
        messages.success(self.request, 'კეთილი იყოს თქვენი მობრძანება!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'მომხმარებლის სახელი ან პაროლი არასწორია.')
        return super().form_invalid(form)


class UserLogoutView(LogoutView):
    pass


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'users/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_bookings'] = Booking.objects.filter(
            user=self.request.user
        ).select_related(
            'route',
            'route__departure_station',
            'route__arrival_station'
        ).order_by('-booking_date')
        return context


class ProfileUpdateView(LoginRequiredMixin, TemplateView):

    template_name = 'users/profile_edit.html'
    success_url = reverse_lazy('users:profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['u_form'] = ProfileUpdateForm(instance=self.request.user)
        context['p_form'] = PasswordChangeForm(self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        u_form = ProfileUpdateForm(request.POST, instance=request.user)

        # ვამოწმებთ პაროლის ველები შევსებულია თუ არა
        password_fields = ['old_password', 'new_password1', 'new_password2']
        has_password_data = any(request.POST.get(f) for f in password_fields)

        if has_password_data:
            p_form = PasswordChangeForm(request.user, request.POST)

            if u_form.is_valid() and p_form.is_valid():
                u_form.save()
                user = p_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'პროფილი და პაროლი წარმატებით განახლდა!')
                return redirect(self.success_url)
            else:
                if not u_form.is_valid():
                    messages.error(request, 'პროფილის მონაცემებში შეცდომაა.')
                if not p_form.is_valid():
                    messages.error(request, 'პაროლის შეცვლისას დაფიქსირდა შეცდომა.')

                # ფორმების ჩვენება შეცდომებით
                context = self.get_context_data()
                context['u_form'] = u_form
                context['p_form'] = p_form
                return self.render_to_response(context)
        else:
            # მხოლოდ პროფილის რედაქტირება
            if u_form.is_valid():
                u_form.save()
                messages.success(request, 'პროფილის მონაცემები განახლდა!')
                return redirect(self.success_url)

        # GET-ის მსგავსად ვაბრუნებთ ფორმებს შეცდომებით
        context = self.get_context_data()
        context['u_form'] = u_form
        return self.render_to_response(context)