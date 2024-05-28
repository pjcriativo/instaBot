from django import forms
from django.shortcuts import render
from instagrapi import Client
import openai
import time
import datetime
from PIL import Image, ImageDraw, ImageFont

# Definição do formulário
class BotForm(forms.Form):
    username = forms.CharField(label='Username', max_length=100)
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    ideias = forms.CharField(label='Ideias (separadas por vírgula)', max_length=200)
    openai_key = forms.CharField(label='OpenAI API Key', max_length=100)
    gpt_model = forms.ChoiceField(label='Modelo GPT', choices=[('gpt-3.5-turbo', 'gpt-3.5-turbo'), ('gpt-4', 'gpt-4')])
    intervalo_tempo = forms.ChoiceField(label='Intervalo de tempo (minutos)', choices=[('5', '5'), ('10', '10'), ('15', '15'), ('20', '20'), ('25', '25'), ('30', '30'), ('35', '35'), ('40', '40'), ('45', '45'), ('50', '50'), ('55', '55'), ('60', '60')])

def gerar_legenda(ideia, openai_key, gpt_model):
    openai.api_key = openai_key
    response = openai.ChatCompletion.create(
        model=gpt_model,
        messages=[
            {"role": "system", "content": "Você é cristão do Instagram, você adora compartilhar a palavra de Deus"},
            {"role": "user", "content": f"Crie uma frase sobre {ideia}"}
        ]
    )
    return response['choices'][0]['message']['content']

def quebrar_texto(texto, fonte, largura_maxima, desenho):
    palavras = texto.split()
    linhas = []
    linha_atual = ""

    for palavra in palavras:
        linha_teste = linha_atual + " " + palavra if linha_atual else palavra
        largura_texto, _ = desenho.textbbox((0, 0), linha_teste, font=fonte)[2:4]
        if largura_texto <= largura_maxima:
            linha_atual = linha_teste
        else:
            linhas.append(linha_atual)
            linha_atual = palavra

    if linha_atual:
        linhas.append(linha_atual)

    return "\n".join(linhas)

def criar_imagem_com_texto(largura, altura, cor_fundo, nome_arquivo, texto=None):
    imagem = Image.new("RGB", (largura, altura), cor_fundo)
    desenho = ImageDraw.Draw(imagem)

    if texto:
        try:
            fonte = ImageFont.truetype("arial.ttf", 40)
        except IOError:
            fonte = ImageFont.load_default()

        texto_dividido = quebrar_texto(texto, fonte, largura - 40, desenho)
        bbox = desenho.textbbox((0, 0), texto_dividido, font=fonte)
        largura_texto = bbox[2] - bbox[0]
        altura_texto = bbox[3] - bbox[1]
        posicao_texto = ((largura - largura_texto) // 2, (altura - altura_texto) // 2)
        desenho.text(posicao_texto, texto_dividido, font=fonte, fill="white")

    imagem.save(nome_arquivo)
    return nome_arquivo

def bot_view(request):
    if request.method == 'POST':
        form = BotForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            ideias = form.cleaned_data['ideias'].split(',')
            openai_key = form.cleaned_data['openai_key']
            gpt_model = form.cleaned_data['gpt_model']
            intervalo_tempo = int(form.cleaned_data['intervalo_tempo']) * 60  # Convertendo para segundos

            cl = Client()
            try:
                cl.login(username, password)
            except Exception as e:
                return render(request, 'painel_web/bot_form.html', {'form': form, 'error': f"Erro ao fazer login: {e}"})

            fotos_postadas = 0
            try:
                while True:
                    for ideia in ideias:
                        legenda = gerar_legenda(ideia.strip(), openai_key, gpt_model)
                        imagem = criar_imagem_com_texto(800, 600, (0, 0, 0), "imagem_com_texto.png", legenda)

                        try:
                            cl.photo_upload(imagem, legenda)
                            fotos_postadas += 1
                        except Exception as e:
                            return render(request, 'painel_web/bot_form.html', {'form': form, 'error': f"Erro ao compartilhar a foto: {e}", 'fotos_postadas': fotos_postadas})

                        time.sleep(intervalo_tempo)

            except KeyboardInterrupt:
                # Permite que o loop seja interrompido manualmente
                pass

            return render(request, 'painel_web/bot_form.html', {'form': form, 'message': f"Fotos postadas: {fotos_postadas}", 'fotos_postadas': fotos_postadas})
    else:
        form = BotForm()
    return render(request, 'painel_web/bot_form.html', {'form': form})
