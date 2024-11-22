# models/res_partner.py
from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    client_code = fields.Char(
        string='Código de Cliente',
        help='Código único para identificar al cliente',
    )
    sucursal_id = fields.Many2one('res.sucursal', string='Sucursal')
    departamento_id = fields.Many2one('res.departamento', string='Departamento')
    is_contact = fields.Boolean(string='¿Es un contacto?', default=False)

    @api.onchange('parent_id', 'sucursal_id', 'departamento_id')
    def _onchange_related_fields(self):
        """Actualizar client_code dependiendo de la relación."""
        if self.parent_id:
            self.client_code = self.parent_id.client_code
        elif self.sucursal_id:
            self.client_code = self.sucursal_id.client_code
        elif self.departamento_id:
            self.client_code = self.departamento_id.client_code
