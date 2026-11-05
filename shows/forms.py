# INF601 - Advanced Programming in Python
# Alex Crenshaw
# Mini Project 6

from django import forms


class BootstrapFormMixin:
    """Adds Bootstrap's CSS classes to every field's widget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs['class'] = css_class
