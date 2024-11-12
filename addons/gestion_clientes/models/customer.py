from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Customer(models.Model):
    _name = 'customer.management'
    _description = 'Gestión de Clientes'

    name = fields.Char(string="Razón Social", required=True)
    rfc = fields.Char(string="RFC", required=True)
    fiscal_address = fields.Char(string="Dirección Fiscal", required=True)
    client_code = fields.Char(string="Código de Cliente", readonly=False)
    fiscal_certificate = fields.Binary(string="Constancia de Situación Fiscal")
    certificate_filename = fields.Char(string="Nombre del Archivo")

    @api.onchange('rfc')
    def _onchange_rfc(self):
        """ Auto-generate client code based on the first three characters of RFC """
        if self.rfc:
            self.client_code = self.rfc[:3]

    def save_customer(self):
        """ Save customer and show success notification """
        if not self.name:
            raise ValidationError("El campo 'Razón Social' es obligatorio.")
        self.ensure_one()  # Ensure single record context
        self.env['bus.bus']._sendone(
            self.env.user.partner_id,
            'simple_notification',
            {'title': "Cliente creado exitosamente", 'message': "El cliente ha sido guardado con éxito."}
        )

    def clear_fields(self):
        """ Clear all fields without saving """
        self.update({
            'name': '',
            'rfc': '',
            'fiscal_address': '',
            'client_code': '',
            'fiscal_certificate': None,
            'certificate_filename': '',
        })

    def action_go_to_customer_list(self):
        """ Navigate back to the list view without saving """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Clientes',
            'view_mode': 'list',
            'res_model': 'customer.management',
            'target': 'main'
        }
