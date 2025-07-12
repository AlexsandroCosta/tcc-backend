from pathlib import Path
from docx import Document
from typing import Literal
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
import re
from django.conf import settings

pdfmetrics.registerFont(TTFont('DejaVuSans', f'{settings.BASE_DIR}/core/utils/fontes/DejaVuSans.ttf'))

class Exportador:
    def __init__(self, codificacao: str = 'utf-8', tamanho_fonte_pdf: int = 12):
        self.codificacao = codificacao
        self.tamanho_fonte_pdf = tamanho_fonte_pdf

    def _verificar_caminho(self, caminho: str) -> str:
        """
        Valida se o caminho de saída é válido.
        Se existir, adiciona um sufixo numérico ao nome até encontrar um nome livre.
        """

        caminho_arquivo = Path(caminho)
        contador = 1

        while caminho_arquivo.exists():
            caminho_arquivo = caminho_arquivo.with_name(
                f"{caminho_arquivo.stem}_{contador}{caminho_arquivo.suffix}"
            )
            contador += 1

        return str(caminho_arquivo)
    
    def exportar_txt(self, texto: str, caminho_saida: str):
        try:
            with open(caminho_saida, 'w', encoding=self.codificacao) as arquivo:
                arquivo.write(texto)
        except Exception as e:
            raise IOError(f'Erro ao exportar txt: {str(e)}')
        
    def exportar_pdf(self, texto: str, caminho_saida: str):
        try:
            doc = SimpleDocTemplate(str(caminho_saida), pagesize=A4,
                                    leftMargin=50, rightMargin=50,
                                    topMargin=50, bottomMargin=50)
            
            nome_fonte = 'DejaVuSans'
            espacamento = 12

            # verificar se o texto contém pelo menos uma letra do alfabeto
            if re.search(r'[a-zA-Z]', texto):
                nome_fonte = 'Helvetica'
                espacamento = 1.5
    
            styles = getSampleStyleSheet()
            style = ParagraphStyle(
                'Normal',
                parent=styles['Normal'],
                fontName=nome_fonte,
                fontSize=12,
                leading=15,
                spaceAfter=6
            )
            
            story = []
            for linha in texto.split('\n'):
                p = Paragraph(linha, style)
                story.append(p)
                story.append(Spacer(1, espacamento))
            
            doc.build(story)
        except Exception as e:
            raise IOError(f'Erro ao exportar PDF: {str(e)}')
        
    def exportar_docx(self, texto: str, caminho_saida: str):
        try:
            docx = Document()
            docx.add_paragraph(texto)
            docx.save(caminho_saida)
        except Exception as e:
            raise IOError(f'Erro ao exportar docx: {str(e)}')
        
    def exportar(self, texto: str, nome_arquivo: str, formato: Literal['txt', 'docx', 'pdf']) -> str:
        """
        Exporta texto para um arquivo no formato especificado.
        """
        if not (formato in ['txt', 'docx', 'pdf']):
            raise ValueError(f'Formato não suportado: {formato}')
        
        caminho_saida = Path('media/exportacoes')
        caminho_saida.mkdir(parents=True, exist_ok=True)

        caminho_saida = f'{caminho_saida}/{nome_arquivo}.{formato}'

        caminho_saida = self._verificar_caminho(caminho_saida)

        if formato == 'txt':
            self.exportar_txt(texto, caminho_saida)
        elif formato == 'pdf':
            self.exportar_pdf(texto, caminho_saida)
        else:
            self.exportar_docx(texto, caminho_saida)

        return caminho_saida