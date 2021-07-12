from django.db.models import fields
from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from .models import Parcel, User


class ParcelForm(ModelForm):
    class Meta:
        model = Parcel
        fields = ["destination_locker", "tracking_number"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['destination_locker'].widget.attrs.update({'class': 'form-select m-2'})
        self.fields['tracking_number'].widget.attrs.update({'class': 'form-control m-2'})


class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["email", "username"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'class': 'form-control m-2'})
        self.fields['username'].widget.attrs.update({'class': 'form-control m-2'})


# notes on styling
    #     class CommentForm(forms.ModelForm):

    #       def __init__(self, *args, **kwargs):
    #           super().__init__(*args, **kwargs)
    #           self.fields['name'].widget.attrs.update({'class': 'special'})
    #           self.fields['comment'].widget.attrs.update(size='40')
