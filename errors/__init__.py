from flask import Blueprint

bp = Blueprint('errors', __name__)

# BU SATIR ÇOK ÖNEMLİ: Blueprint tanımlandıktan SONRA import edilmeli
from . import handlers