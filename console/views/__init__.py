from console import app
from console.views.add_user import add_user_bp
from console.views.home import home_bp
from console.views.info import info_bp
from console.views.logout import logout_bp
from console.views.store import store_bp
from console.views.test import test_bp


app.register_blueprint(add_user_bp)
app.register_blueprint(home_bp)
app.register_blueprint(info_bp)
app.register_blueprint(logout_bp)
app.register_blueprint(store_bp)
app.register_blueprint(test_bp)
