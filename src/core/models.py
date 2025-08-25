from django.db import models

class Imagem(models.Model):
    arquivo = models.ImageField(upload_to='imagens/')
    traducao = models.TextField(blank=True, null=True)
    boxes = models.JSONField(blank=True, null=True)
