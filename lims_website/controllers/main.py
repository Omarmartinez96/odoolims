import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

SERVICES = [
    ('clinicos', 'Análisis Clínicos'),
    ('ambientales', 'Análisis Ambientales'),
    ('industriales', 'Análisis Industriales'),
    ('microbiologia', 'Microbiología'),
    ('fisicoquimicos', 'Análisis Fisicoquímicos'),
    ('alimentos', 'Análisis de Alimentos'),
    ('otro', 'Otro / No especificado'),
]

FEEDBACK_TYPES = [
    ('sugerencia', 'Sugerencia'),
    ('queja', 'Queja o Reclamo'),
    ('felicitacion', 'Felicitación'),
    ('consulta', 'Consulta General'),
]


class LimsWebsiteController(http.Controller):

    # =====================================================================
    # CONTACTO COMERCIAL
    # =====================================================================

    @http.route(
        '/contacto-comercial',
        type='http',
        auth='public',
        website=True,
        sitemap=True,
    )
    def contact_sales(self, **kwargs):
        success = kwargs.get('success')
        error = kwargs.get('error')
        values = {
            'services': SERVICES,
            'success': success,
            'error': error,
            'page_name': 'contact_sales',
        }
        return request.render('lims_website.contact_sales_page', values)

    @http.route(
        '/contacto-comercial/enviar',
        type='http',
        auth='public',
        website=True,
        methods=['POST'],
        csrf=True,
    )
    def contact_sales_submit(self, **post):
        name = (post.get('contact_name') or '').strip()
        email = (post.get('contact_email') or '').strip()
        message = (post.get('contact_message') or '').strip()

        if not name or not email or not message:
            return request.redirect('/contacto-comercial?error=campos_requeridos')

        try:
            request.env['lims.contact.inquiry'].sudo().create({
                'name': name,
                'company': (post.get('contact_company') or '').strip(),
                'email': email,
                'phone': (post.get('contact_phone') or '').strip(),
                'service_interest': post.get('contact_service') or 'otro',
                'subject': (post.get('contact_subject') or 'Consulta comercial').strip(),
                'message': message,
            })
            return request.redirect('/contacto-comercial?success=1')
        except Exception:
            _logger.exception('Error al crear solicitud comercial desde el sitio web')
            return request.redirect('/contacto-comercial?error=1')

    # =====================================================================
    # SUGERENCIAS Y QUEJAS
    # =====================================================================

    @http.route(
        '/sugerencias-quejas',
        type='http',
        auth='public',
        website=True,
        sitemap=True,
    )
    def feedback(self, **kwargs):
        success = kwargs.get('success')
        error = kwargs.get('error')
        values = {
            'feedback_types': FEEDBACK_TYPES,
            'success': success,
            'error': error,
            'page_name': 'feedback',
        }
        return request.render('lims_website.feedback_page', values)

    @http.route(
        '/sugerencias-quejas/enviar',
        type='http',
        auth='public',
        website=True,
        methods=['POST'],
        csrf=True,
    )
    def feedback_submit(self, **post):
        name = (post.get('fb_name') or '').strip()
        email = (post.get('fb_email') or '').strip()
        subject = (post.get('fb_subject') or '').strip()
        message = (post.get('fb_message') or '').strip()

        if not name or not email or not subject or not message:
            return request.redirect('/sugerencias-quejas?error=campos_requeridos')

        try:
            service_date = post.get('fb_service_date') or False
            request.env['lims.feedback'].sudo().create({
                'name': name,
                'email': email,
                'feedback_type': post.get('fb_type') or 'sugerencia',
                'subject': subject,
                'message': message,
                'sample_reference': (post.get('fb_reference') or '').strip(),
                'service_date': service_date if service_date else False,
            })
            return request.redirect('/sugerencias-quejas?success=1')
        except Exception:
            _logger.exception('Error al crear comentario desde el sitio web')
            return request.redirect('/sugerencias-quejas?error=1')
