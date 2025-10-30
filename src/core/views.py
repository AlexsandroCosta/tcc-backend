from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from rest_framework.response import Response
from .utils.tradutor_texto import TradutorTexto
from .utils.exportador import Exportador
from .utils.mapa_braille import lista_mapa
from .utils.processar_imagem import ProcessarImagem
from django.http import FileResponse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import tempfile
import os
from ultralytics import YOLO
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont
from django.core.files.base import ContentFile 
import io
from .models import Imagem
from .serializers import ImagemSerializer

caminho_modelo = os.path.join(settings.BASE_DIR, "core", "utils", "modelo", "best.pt")
MODELO = YOLO(caminho_modelo)

class View(viewsets.ViewSet):
    parser_classes = (MultiPartParser, FormParser)
    exportador = Exportador()

    @swagger_auto_schema(
        operation_description='Traduz um arquivo para Braille e retorna no formato desejado.',
        tags=['Tradutor'],
        manual_parameters=[
            openapi.Parameter(name='arquivo', in_=openapi.IN_FORM, type=openapi.TYPE_FILE)
        ],
        responses={
            200: 'Download do arquivo traduzido'
        }
    )
    @action(detail=False, methods=['post'], url_path='texto-braille')
    def texto_braille(self, request):
        try:
            arquivo = request.FILES.get('arquivo') 

            if not arquivo:
                return Response({'erro': 'Nenhum arquivo enviado'}, status=400)

            # Verificar o tipo de arquivo
            tipo_arquivo = arquivo.name.split('.')[-1].lower()

            # Lógica de processamento dependendo do tipo do arquivo
            if not tipo_arquivo in ['txt', 'pdf', 'docx', 'jpg', 'jpeg', 'png']:
                return Response({'erro': 'Tipo de arquivo não suportado'}, status=400)

            with tempfile.NamedTemporaryFile(delete=False, suffix=f'_{arquivo.name}') as arquivo_temp:
                for chunk in arquivo.chunks():
                    arquivo_temp.write(chunk)
                
                temp_path = arquivo_temp.name

            tradutor = TradutorTexto(temp_path)
            
            nome_original = os.path.splitext(arquivo.name)[0]

            return Response({'exportacao': self.exportador.exportar(tradutor.traducao_braille, nome_original, 'braille')}, status=200)

        except Exception as e:
            return Response({'erro': str(e)}, status=400)
        
    @swagger_auto_schema(
        operation_description='Traduz braille de uma imagem para texto e retorna o texto.',
        tags=['Tradutor'],
        manual_parameters=[
            openapi.Parameter(name='imagens', in_=openapi.IN_FORM, type=openapi.TYPE_FILE),
        ],
        responses={
            200: 'Texto extraído da imagem'
        }
    )
    @action(detail=False, methods=['post'], url_path='braille-texto')
    def braille_texto(self, request):
        imagens = request.FILES.getlist('imagens')
        lista_obj = []

        if not imagens:
            return Response({'erro': 'Nenhuma imagem enviada'}, status=400)
    
        for imagem in imagens:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'_{imagem.name}') as img_temp:
                for chunk in imagem.chunks():
                    img_temp.write(chunk)

                ProcessarImagem(img_temp.name).processar_imagem()
                temp_img_path = img_temp.name

            try:
                resultados = MODELO.predict(source=temp_img_path, save=False, device='cpu')

                for resultado in resultados:
                    
                    imagem_np = resultado.orig_img.copy()  # np.array
                    imagem_pil = Image.fromarray(imagem_np)
                    draw = ImageDraw.Draw(imagem_pil)

                    try:
                        font = ImageFont.truetype(f'{settings.BASE_DIR}/core/utils/fontes/DejaVuSans.ttf', size=35)
                    except:
                        font = ImageFont.load_default()

                    caixas_info = []

                    for caixa in resultado.boxes:
                        classe_id = int(caixa.cls[0])
                        conteudo = lista_mapa[classe_id]
                        x1, y1, x2, y2 = caixa.xyxy[0]  # coordenadas da caixa
                        
                        draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
                        draw.text((x1, y1 - 35), conteudo, fill="red", font=font)
                        
                        caixas_info.append({
                            'conteudo': conteudo,
                            'x1': float(x1),
                            'y1': float(y1),
                            'x2': float(x2),
                            'y2': float(y2)
                        })
               
                buffer = io.BytesIO()
                imagem_pil.save(buffer, format='JPEG')
                buffer.seek(0)

                nome_arquivo = f'processed_{imagem.name}'
                conteudo = ContentFile(buffer.read(), name=nome_arquivo)

                # ---- ORDENAR E AGRUPAR ----
                # 1. Ordena por y1
                caixas_info.sort(key=lambda e: e['y1'])

                # 2. Agrupa por linhas com base em uma tolerância vertical
                linhas = []
                tolerancia = 100  # ajuste conforme o espaçamento vertical entre as linhas

                for elem in caixas_info:
                    y = elem['y1']
                    colocado = False
                    for linha in linhas:
                        # verifica se está na mesma linha (diferença pequena no y)
                        if abs(linha[0]['y1'] - y) < tolerancia:
                            linha.append(elem)
                            colocado = True
                            break
                    if not colocado:
                        linhas.append([elem])

                # 3. Ordena cada linha da esquerda para a direita
                for linha in linhas:
                    linha.sort(key=lambda e: e['x1'])

                # 4. Junta tudo em texto com quebras de linha
                texto_final = ''
                for linha in linhas:
                    for caixa in linha:
                        texto_final += f'{caixa["conteudo"]} '
                    texto_final += '\n'  # quebra de linha após final de cada linha

                lista_obj.append({
                    'arquivo':Imagem.objects.create(arquivo=conteudo, boxes=caixas_info, traducao=texto_final).arquivo.name,
                    'exportacao': self.exportador.exportar(texto_final, imagem.name, 'texto')
                })

            except Exception as e:
                return Response({'erro': f'Erro ao processar a imagem {imagem.name}: {str(e)}'}, status=400)

        # serializer = ImagemSerializer(lista_obj, many=True)
        
        return Response(lista_obj, status=200)