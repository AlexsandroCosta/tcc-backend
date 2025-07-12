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