from django import forms


class RefundRequestForm(forms.Form):
    reason = forms.CharField(
        label="退票原因",
        widget=forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        required=False,
    )
