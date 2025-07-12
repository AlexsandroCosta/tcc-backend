import pytesseract
import numpy
import cv2
import mimetypes
import fitz
from .mapa_braille import mapa_braille
from docx import Document
import re

class TradutoTexto:
    def __init__(self, caminho_arquivo: str):
        self.texto_extraido = self._extrair_texto(caminho_arquivo)
        self.traducao_braille = self._traduzir_para_braille()

    def _carregar_arquivo(self, caminho_arquivo: str) -> tuple[str, numpy.ndarray | fitz.Document]:
        """Carrega o arquivo e retorna seu tipo e conteúdo."""
        tipo, _ = mimetypes.guess_type(caminho_arquivo)

        if not tipo:
            raise ValueError("Tipo de arquivo não reconhecido")

        try:
            if tipo:
                if tipo.startswith('image'):
                    tipo_arquivo = 'imagem'
                    arquivo = cv2.imread(caminho_arquivo)
                
                elif tipo == 'application/pdf':
                    tipo_arquivo = 'pdf'
                    arquivo = fitz.open(caminho_arquivo)

                elif tipo == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    tipo_arquivo = 'docx'
                    arquivo = Document(caminho_arquivo)

                else:
                    raise ValueError('Tipo de arquivo não suportado')
        except Exception as e:
            raise ValueError(f'Erro ao carregar arquivo: {str(e)}')

        return tipo_arquivo, arquivo
    
    def _extrair_texto_imagem(self, imagem: numpy.ndarray) -> str:
        """Extrai texto de uma imagem usando OCR."""
        try:
            return pytesseract.image_to_string(imagem, lang='por')
        except Exception as e:
            raise RuntimeError(f"Erro ao extrair texto da imagem: {str(e)}")

    def _extrair_texto_pdf(self, pdf: fitz.Document) -> str:
        """Extrai texto de um arquivo PDF."""
        try:
            ### Falta fazer: Identificar se é um pdf digital (apenas texto), scaneado (imagens) ou dos dois
            texto = []

            for pagina in pdf:
                texto.append(pagina.get_textpage().extractText())
            
            return ''.join(texto)
        except Exception as e:
            raise RuntimeError(f"Erro ao extrair texto do PDF: {str(e)}")
        finally:
            pdf.close()

    def _extrair_texto_docx(self, docx: Document):
        try:
            texto = '\n'.join([paragrafo.text for paragrafo in docx.paragraphs])
            return texto
        except Exception as e:
            raise RuntimeError(f"Erro ao extrair texto do docx: {str(e)}")

    def _extrair_texto(self, caminho_arquivo: str) -> str:
        tipo_arquivo, arquivo = self._carregar_arquivo(caminho_arquivo)

        if tipo_arquivo == 'imagem':
            return self._extrair_texto_imagem(arquivo)
        elif tipo_arquivo == 'pdf':
            return self._extrair_texto_pdf(arquivo)
        else:
            return self._extrair_texto_docx(arquivo) 

    def _traduzir_para_braille(self) -> str:
        """Traduz o texto extraído para Braille."""
        traducao = []

        try:
            # Remove hifens no final de linha (junção de palavras quebradas)
            texto = self.texto_extraido.lower().replace('-\n', '')
            # Substitui \n seguido de caractere (exceto \n) por " " + caractere
            texto_tratado = re.sub(r'\n([^\n])', r' \1', texto)

            for linha in texto_tratado:
                for letra in linha:
                        traducao.append(mapa_braille.get(letra, ''))

            return ''.join(traducao)
        except Exception as e:
            raise RuntimeError(f"Erro durante a tradução: {str(e)}")