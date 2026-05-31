from flask import render_template
from . import bp
from app import db  # Veritabanı nesnenin nerede tanımlı olduğuna göre bu import değişebilir

# app_errorhandler kullanıyoruz ki tüm projede geçerli olsun
@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500