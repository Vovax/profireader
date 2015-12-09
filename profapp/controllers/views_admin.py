from .blueprints_declaration import admin_bp
from flask import g, request, url_for, render_template, flash, current_app
from .request_wrapers import ok
from .pagination import pagination
from ..models.translate import TranslateTemplate
from config import Config
from utils.db_utils import db
from sqlalchemy.sql import expression


@admin_bp.route('/translations', methods=['GET'])
def translations():
    return render_template('admin/translations.html',
                           angular_ui_bootstrap_version='//angular-ui.github.io/bootstrap/ui-bootstrap-tpls-0.14.2.js')


@admin_bp.route('/translations', methods=['POST'])
@ok
def translations_load(json):
    page = json.get('page') or 1

    params = {}
    params['search_in_phrase'] = json.get('search_in_phrase') if json.get('search_in_phrase') else None
    params['search_in_uk'] = json.get('search_in_uk') if json.get('search_in_uk') else None
    params['search_in_en'] = json.get('search_in_en') if json.get('search_in_en') else None
    params['sort_creation_time'] = json.get('sort_creation_time') if json.get('sort_creation_time') else None
    params['sort_last_accessed_time'] = json.get('sort_last_accessed_time') if json.get('sort_last_accessed_time') else None
    subquery = TranslateTemplate.subquery_search(template=json.get('template') or None,
                                                 url=json.get('url') or None,
                                                 **params)
    translations, pages, current_page = pagination(subquery, page=page, items_per_page=json.get('pageSize'))
    tr = [t.get_client_side_dict() for t in translations]
    templates = db(TranslateTemplate.template).group_by(TranslateTemplate.template) \
        .order_by(expression.asc(expression.func.lower(TranslateTemplate.template))).all()
    urls = db(TranslateTemplate.url).group_by(TranslateTemplate.url) \
        .order_by(expression.asc(expression.func.lower(TranslateTemplate.url))).all()
    return {'languages': TranslateTemplate.languages, 'translations': tr,
            'pages': {'total': pages, 'current_page': current_page,
                      'page_buttons': Config.PAGINATION_BUTTONS},
            'templates': [{'label': t.template, 'value': t.template} for t in templates],
            'urls': [{'label': t[0], 'value': t[0]} for t in urls],
            'total': subquery.count()
            }


@admin_bp.route('/translations_save', methods=['POST'])
@ok
def translations_save(json):
    exist = db(TranslateTemplate, template=json['row'], name=json['col']).first()
    return TranslateTemplate.get(exist.id).attr({json['lang']: json['val']}).save().get_client_side_dict()

@admin_bp.route('/delete', methods=['POST'])
@ok
def delete(json):
    return TranslateTemplate.delete(json['objects'])
