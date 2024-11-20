from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    rfc = fields.Char(string='RFC', required=True)
    client_code = fields.Char(string='Código de Cliente', readonly=True)

    @api.onchange('rfc')
    def _generate_client_code(self):
        """
        Genera el Código de Cliente basado en las primeras 3 letras del RFC.
        """
        if self.rfc:
            # Tomar las primeras 3 letras del RFC en mayúsculas
            prefix = self.rfc[:3].upper()
            # Generar un número secuencial único
            existing_count = self.env['res.partner'].search_count([])
            self.client_code = f"{prefix}-{existing_count + 1:04d}"
