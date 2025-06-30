from odoo import models, api

class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)

        # Verificamos que es una cotización
        if res.get('model') == 'sale.order' and res.get('res_id'):
            order = self.env['sale.order'].browse(res['res_id'])

            # Obtenemos contactos relacionados al departamento
            contacts = self.env['lims.contact'].search([
                ('department_id', '=', order.lims_department_id.id),
                ('partner_id', '!=', False)
            ])

            # Agregamos esos contactos como destinatarios
            extra_partner_ids = contacts.mapped('partner_id.id')

            # Combinamos con los destinatarios existentes (si los hay)
            res['partner_ids'] = [(6, 0, list(set(extra_partner_ids)))]

        return res
