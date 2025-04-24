# post_init.py
from odoo import api, SUPERUSER_ID

def create_mail_template(env):
    # ¿ya existe el registro XML? (para no duplicar)
    if not env.ref('lims_reception.email_template_comprobante', raise_if_not_found=False):
        # 1) Creamos la plantilla
        model = env['ir.model']._get('lims.custody_chain')
        template = env['mail.template'].create({
            'name': 'Comprobante de Cadena de Custodia',
            'model_id': model.id,
            'email_from': '${(user.email or "")|safe}',
            'email_to': '${object.cliente_id.email}',
            'subject': 'Comprobante de Cadena de Custodia',
            'body_html': """
                <p>Estimado/a Cliente,</p>
                <p>Adjunto el comprobante correspondiente a la siguiente Cadena de Custodia:</p>
                <p><strong>Código:</strong> ${object.custody_chain_code}</p>
                <p>Gracias por su confianza.</p>
                <br/>
                <p>Atentamente,<br/>El equipo de ${user.company_id.name}</p>
            """,
        })
        # 2) Le asignamos el XML ID para que env.ref y el botón lo encuentren
        env['ir.model.data'].create({
            'module': 'lims_reception',
            'name': 'email_template_comprobante',
            'model': 'mail.template',
            'res_id': template.id,
            'noupdate': True,
        })
