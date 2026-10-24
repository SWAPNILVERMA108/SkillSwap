from django import forms

class SwapRequestForm(forms.Form):
    to_user = forms.IntegerField(widget=forms.HiddenInput)
    skill_offered = forms.IntegerField(widget=forms.HiddenInput)
    skill_wanted = forms.IntegerField(widget=forms.HiddenInput)
    message = forms.CharField(required=False, max_length=500, widget=forms.TextInput(
        attrs={"placeholder": "Optional message"}
    ))
