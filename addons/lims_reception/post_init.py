from odoo import api, SUPERUSER_ID

def create_mail_template(registry):
    # 1) Abre un cursor para esta sesión
    cr = registry.cursor()
    try:
        # 2) Crea un env de superusuario
        env = api.Environment(cr, SUPERUSER_ID, {})

        # 3) Si la plantilla ya existe no hacer nada
        if not env.ref('lims_reception.email_template_comprobante', raise_if_not_found=False):
            model = env['ir.model']._get('lims.custody_chain')
            env['mail.template'].create({
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
    finally:
        # 4) Cierra el cursor
        cr.close()
