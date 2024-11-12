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
