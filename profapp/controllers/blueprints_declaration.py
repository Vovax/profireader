from flask import Blueprint

general_bp = Blueprint('general', __name__)
auth_bp = Blueprint('auth', __name__)
user_bp = Blueprint('user', __name__)
article_bp = Blueprint('article', __name__)
filemanager_bp = Blueprint('filemanager', __name__)
static_bp = Blueprint('static', __name__, static_url_path='')
image_editor_bp = Blueprint('image_editor', __name__)
company_bp = Blueprint('company', __name__)
portal_bp = Blueprint('portal', __name__)
front_bp = Blueprint('front', __name__)
file_bp = Blueprint('file', __name__)
exception_bp = Blueprint('exception', __name__)
