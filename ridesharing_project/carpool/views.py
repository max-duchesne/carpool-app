from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Ride
from .forms import RideSignUpForm

class RideListView(ListView):
    model = Ride
    template_name = 'carpool/home.html'  #without this, by default, checks for 'app_name/model_name_viewtype.html (here viewtype is ListView)
    context_object_name = 'rides'  #without this, by default, calls context "object list" instead of "rides" like we do here
    ordering = ['-departure_time']  #this is way to change ordering -- eventually need to change to prioritize best ride matches
    paginate_by = 25
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for ride in context['rides']:
            ride.spots_left = ride.capacity - ride.num_riders
            # the code below might be useful to change the styling based on if ride is full or not
            
            # if ride.spots_left <= 0:
            #     ride.is_full = True
            # else:
            #     ride.is_full = False
        return context
    
class UserRideListView(ListView):
    model = Ride
    template_name = 'carpool/user_rides.html'  #without this, by default, checks for 'app_name/model_name_viewtype.html (here viewtype is ListView)
    context_object_name = 'rides'  #without this, by default, calls context "object list" instead of "rides" like we do here
    paginate_by = 3
    
    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get('username'))  #either gets user's username or returns 404 error
        return Ride.objects.filter(driver=user).order_by('-departure_time')  #ordering needs to be done because query overrides it when stated as in RideListView
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for ride in context['rides']:
            ride.spots_left = ride.capacity - ride.num_riders
            # the code below might be useful to change the styling based on if ride is full or not
            
            # if ride.spots_left <= 0:
            #     ride.is_full = True
            # else:
            #     ride.is_full = False
        return context
    
class RideDetailView(DetailView):
    model = Ride
    
    def get_object(self, queryset=None):
        ride = super().get_object(queryset)
        ride.spots_left = ride.capacity - ride.num_riders
        return ride
    
class RideCreateView(LoginRequiredMixin, CreateView):
    model = Ride
    fields = ['origin','destination','departure_time','notes','capacity']
    success_url = '/'
    
    def form_valid(self, form):
        form.instance.driver = self.request.user #set driver to current logged in user
        form.instance.num_riders = 0
        return super().form_valid(form)
    
class RideUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Ride
    fields = ['origin','destination','departure_time','notes','capacity']
    success_url = '/'
    
    def test_func(self):
        ride = self.get_object()
        if self.request.user == ride.driver:
            return True
        return False
    
class RideSignUpView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Ride
    form_class = RideSignUpForm  #when fields are specified in the form class, don't need to include them as 'fields' in view
    template_name_suffix = '_signup_form'
    success_url = '/'

    def test_func(self):
        ride = self.get_object()
        if self.request.user != ride.driver:
            if ride.capacity > ride.num_riders:
                return True
        return False
     
    # this method is working, but the error message is not using CSS styling as expected
    # def handle_no_permission(self):
    #     messages.error(self.request, "You are not allowed to sign up for this ride", extra_tags='alert-danger')
    #     return redirect('carpool-home')
    
    def post(self, request, *args, **kwargs):
        ride = self.get_object()
        ride.num_riders += 1
        ride.save()
        #email the person who signed up
        send_mail(
            'Ride Signup Confirmation',
            'You have successfully signup for a ride',
            'max.duchesne@gmail.com',
            [self.request.user.email],
            fail_silently=False,
        )
        #email the driver
        send_mail(
            'Ride Signup Confirmation',
            f'{self.request.user.username} has signed up for your ride',
            'max.duchesne@gmail.com',
            [ride.driver.email],
            fail_silently=False,
        )
        messages.success(request, 'An email was just sent. Please check your inbox')
        return redirect('carpool-home')
    
        # the method below had a bug where the button was the num_riders field rather than buttons
        # the post method above replaces the form_valid method
        
        # def form_valid(self, form):
        #     ride = self.get_object()
        #     ride.num_riders += 1
        #     ride.save()
        #     # send_mail(
        #     #     'Ride Signup Confirmation',
        #     #     'You have successfully signup for a ride',
        #     #     'max.duchesne@gmail.com',
        #     #     ['mrduch23@colby.edu'],
        #     #     fail_silently=False,
        #     # )
        #     messages.success(self.request, 'An email was just sent. Please check your inbox')
        #     return super().form_valid(form)
    
class RideDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Ride
    success_url = '/'
    
    def test_func(self):
        ride = self.get_object()
        if self.request.user == ride.driver:
            return True
        return False