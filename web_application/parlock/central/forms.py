from django.db.models import fields
from django.forms import ModelForm
from .models import Parcel


class ParcelForm(ModelForm):
    class Meta:
        model = Parcel
        fields = ["destination_locker", "tracking_number"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['destination_locker'].widget.attrs.update({'class': 'form-select'})
        self.fields['tracking_number'].widget.attrs.update({'class': 'form-control'})

# notes on styling
    #     class CommentForm(forms.ModelForm):

    #       def __init__(self, *args, **kwargs):
    #           super().__init__(*args, **kwargs)
    #           self.fields['name'].widget.attrs.update({'class': 'special'})
    #           self.fields['comment'].widget.attrs.update(size='40')
