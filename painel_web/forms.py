from django import forms

class BotForm(forms.Form):
    username = forms.CharField(label='Username', max_length=100)
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    ideias = forms.CharField(label='Ideias (separadas por vírgula)', max_length=200)
    openai_key = forms.CharField(label='OpenAI API Key', max_length=100)
    gpt_model = forms.ChoiceField(label='Modelo GPT', choices=[('gpt-3.5-turbo', 'gpt-3.5-turbo'), ('gpt-4', 'gpt-4')])
    intervalo_tempo = forms.ChoiceField(label='Intervalo de tempo (minutos)', choices=[('5', '5'), ('10', '10'), ('15', '15'), ('20', '20'), ('25', '25'), ('30', '30'), ('35', '35'), ('40', '40'), ('45', '45'), ('50', '50'), ('55', '55'), ('60', '60')])
