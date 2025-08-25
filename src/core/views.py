from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from rest_framework.response import Response
from .utils.tradutor_texto import TradutoTexto
from .utils.exportador import Exportador
from django.http import FileResponse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import tempfile
import os
from ultralytics import YOLO
from django.conf import settings
from .utils.mapa_braille import lista_mapa
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
            openapi.Parameter(name='arquivo', in_=openapi.IN_FORM, type=openapi.TYPE_FILE),
            openapi.Parameter(name='formato', in_=openapi.IN_FORM, type=openapi.TYPE_STRING, enum=['docx', 'pdf', 'txt'])
        ],
        responses={
            200: 'Download do arquivo traduzido'
        }
    )
    @action(detail=False, methods=['post'], url_path='texto-braille')
    def texto_braille(self, request):
        try:
            arquivo = request.FILES.get('arquivo')
            formato = request.data.get('formato')

            if not arquivo:
                return Response({'erro': 'Arquivo não enviado'}, status=400)
            if not formato:
                return Response({'erro': 'Formato não especificado'}, status=400)

            if not formato in ['docx', 'pdf', 'txt']:
                return Response({'erro': f'Formato não suportado: {formato}'}, status=400)

            # Verificar o tipo de arquivo
            tipo_arquivo = arquivo.name.split('.')[-1].lower()

            # Lógica de processamento dependendo do tipo do arquivo
            if not tipo_arquivo in ['txt', 'pdf', 'docx', 'jpg', 'jpeg', 'png']:
                return Response({'erro': 'Tipo de arquivo não suportado'}, status=400)

            with tempfile.NamedTemporaryFile(delete=False, suffix=f'_{arquivo.name}') as arquivo_temp:
                for chunk in arquivo.chunks():
                    arquivo_temp.write(chunk)
                
                temp_path = arquivo_temp.name

            traduto = TradutoTexto(temp_path)

            nome_original = os.path.splitext(arquivo.name)[0]
            
            caminho_saida = self.exportador.exportar(traduto.traducao_braille, nome_original, formato)

            return FileResponse(open(caminho_saida, 'rb'), as_attachment=True, filename=f'{nome_original}_traduzido.{formato}')

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

                lista_obj.append(Imagem.objects.create(arquivo=conteudo, boxes=caixas_info))

            except Exception as e:
                return Response({'erro': f'Erro ao processar a imagem {imagem.name}: {str(e)}'}, status=400)

        serializer = ImagemSerializer(lista_obj, many=True)
        
        return Response(serializer.data, status=200)