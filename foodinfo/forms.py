from django import forms
from .models import Question, Option

def generate_dynamic_form():
    """
    Dynamically generates a form with fields corresponding to active questions.
    """
    class DynamicQuestionForm(forms.Form):
        def __init__(self, *args, **kwargs):
            super(DynamicQuestionForm, self).__init__(*args, **kwargs)
            for question in Question.objects.all():
                options = Option.objects.filter(question=question)
                self.fields[f'question_{question.id}'] = forms.ChoiceField(
                    label=question.text,
                    choices=[(option.id, option.text) for option in options],
                    widget=forms.RadioSelect,
                    required=True
                )
    return DynamicQuestionForm
