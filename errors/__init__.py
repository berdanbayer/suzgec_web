from flask import Blueprint

# 'errors' adında bir blueprint oluşturuyoruz
bp = Blueprint('errors', __name__)

from . import handlers