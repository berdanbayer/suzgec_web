from flask import render_template
from . import bp
# app importunuz varsa burada olabilir

# DİKKAT: @bp.errorhandler değil, @bp.app_errorhandler olmalı!
@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@bp.app_errorhandler(500)
def internal_error(error):
    # db.session.rollback() # (Eğer db import ettiysen)
    return render_template('500.html'), 500