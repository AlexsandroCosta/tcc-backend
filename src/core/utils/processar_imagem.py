import cv2

class ProcessarImagem:

    def __init__(self, caminho_imagem):
        self.caminho_imagem = caminho_imagem
        self.imagem = cv2.imread(caminho_imagem)

        if self.imagem is None:
            raise FileNotFoundError(f"Imagem não encontrada ou não pôde ser lida: {caminho_imagem}")

    def processar_imagem(self):
        self._converter_para_cinza()

        # return self.imagem

    # Converte a imagem em escala de cinza
    def _converter_para_cinza(self):
        # só converte se for colorida
        if len(self.imagem.shape) == 3:
            self.imagem = cv2.cvtColor(self.imagem, cv2.COLOR_BGR2GRAY)

        self._filtragem()

    # Aplica um filtro de mediana e gaussiana para reduzir ruídos
    def _filtragem(self):
        # self.imagem = cv2.medianBlur(self.imagem, 5)
        self.imagem = cv2.GaussianBlur(self.imagem, (5, 5), 0)

        # self._binarizacao_adaptativa()

    # Ajusta automaticamente o limiar conforme a iluminação local
    def _binarizacao_adaptativa(self):
        self.imagem = cv2.adaptiveThreshold(
            self.imagem, 
            255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY,
            15,
            5
        )

        self._operacoes_morfologicas()

    def _operacoes_morfologicas(self):
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

        # --- ABERTURA ---
        # Remove pequenos objetos brancos do fundo preto
        self.imagem = cv2.morphologyEx(self.imagem, cv2.MORPH_OPEN, kernel)

        # --- FECHAMENTO ---
        # Preenche pequenos buracos em objetos brancos
        self.imagem = cv2.morphologyEx(self.imagem, cv2.MORPH_CLOSE, kernel)
        