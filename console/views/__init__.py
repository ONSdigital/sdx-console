from console import app
from console.views.add_user import add_user_bp
from console.views.FTP import FTP_bp
from console.views.logout import logout_bp
from console.views.store import store_bp
from console.views.submit import submit_bp


app.register_blueprint(add_user_bp)
app.register_blueprint(FTP_bp)
app.register_blueprint(logout_bp)
app.register_blueprint(store_bp)
app.register_blueprint(submit_bp)
