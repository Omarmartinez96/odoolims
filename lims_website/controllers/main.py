import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

SERVICES = [
    ('agua', 'Agua'),
    ('alimentos', 'Alimentos'),
    ('dispositivos_medicos', 'Dispositivos Médicos'),
    ('microbiologia', 'Microbiología General'),
    ('otro', 'Otro / No especificado'),
]

FEEDBACK_TYPES = [
    ('sugerencia', 'Sugerencia'),
    ('queja', 'Queja o Reclamo'),
    ('felicitacion', 'Felicitación'),
    ('consulta', 'Consulta General'),
]

NOTIFY_EMAIL = 'contacto@proteuslaboratorio.com'


def _get_notify_email():
    """Retorna el correo de la compañía registrada, con fallback al correo del lab."""
    company = request.env['res.company'].sudo().search([], limit=1)
    return (company.email or NOTIFY_EMAIL).strip()


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
        service = post.get('contact_service') or 'otro'

        if not name or not email or not message:
            return request.redirect('/contacto-comercial?error=campos_requeridos')

        try:
            service_label = dict(SERVICES).get(service, service)
            subject = 'Solicitud comercial – %s' % service_label

            request.env['lims.contact.inquiry'].sudo().create({
                'name': name,
                'company': (post.get('contact_company') or '').strip(),
                'email': email,
                'phone': (post.get('contact_phone') or '').strip(),
                'service_interest': service,
                'subject': subject,
                'message': message,
            })

            # Notificación por correo
            body = '''
                <p><strong>Nueva solicitud de contacto comercial recibida.</strong></p>
                <table>
                    <tr><td><strong>Nombre:</strong></td><td>%s</td></tr>
                    <tr><td><strong>Empresa:</strong></td><td>%s</td></tr>
                    <tr><td><strong>Correo:</strong></td><td>%s</td></tr>
                    <tr><td><strong>Teléfono:</strong></td><td>%s</td></tr>
                    <tr><td><strong>Servicio de interés:</strong></td><td>%s</td></tr>
                </table>
                <p><strong>Mensaje:</strong><br/>%s</p>
            ''' % (
                name,
                (post.get('contact_company') or '').strip() or '—',
                email,
                (post.get('contact_phone') or '').strip() or '—',
                service_label,
                message.replace('\n', '<br/>'),
            )

            request.env['mail.mail'].sudo().create({
                'subject': subject,
                'email_to': _get_notify_email(),
                'email_from': email,
                'body_html': body,
                'auto_delete': True,
            }).send()

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
        message = (post.get('fb_message') or '').strip()
        fb_type = post.get('fb_type') or 'sugerencia'

        if not name or not email or not message:
            return request.redirect('/sugerencias-quejas?error=campos_requeridos')

        try:
            type_label = dict(FEEDBACK_TYPES).get(fb_type, fb_type)
            subject = '%s de %s' % (type_label, name)
            service_date = post.get('fb_service_date') or False

            request.env['lims.feedback'].sudo().create({
                'name': name,
                'email': email,
                'feedback_type': fb_type,
                'subject': subject,
                'message': message,
                'sample_reference': (post.get('fb_reference') or '').strip(),
                'service_date': service_date if service_date else False,
            })

            # Notificación por correo
            body = '''
                <p><strong>Nuevo comentario recibido: %s</strong></p>
                <table>
                    <tr><td><strong>Tipo:</strong></td><td>%s</td></tr>
                    <tr><td><strong>Nombre:</strong></td><td>%s</td></tr>
                    <tr><td><strong>Correo:</strong></td><td>%s</td></tr>
                    <tr><td><strong>Folio de muestra:</strong></td><td>%s</td></tr>
                    <tr><td><strong>Fecha del servicio:</strong></td><td>%s</td></tr>
                </table>
                <p><strong>Mensaje:</strong><br/>%s</p>
            ''' % (
                type_label,
                type_label,
                name,
                email,
                (post.get('fb_reference') or '').strip() or '—',
                service_date or '—',
                message.replace('\n', '<br/>'),
            )

            request.env['mail.mail'].sudo().create({
                'subject': subject,
                'email_to': _get_notify_email(),
                'email_from': email,
                'body_html': body,
                'auto_delete': True,
            }).send()

            return request.redirect('/sugerencias-quejas?success=1')
        except Exception:
            _logger.exception('Error al crear comentario desde el sitio web')
            return request.redirect('/sugerencias-quejas?error=1')
