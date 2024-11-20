from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    client_code = fields.Char(
        string='Código de Cliente',
        help='Código único para identificar al cliente',
        index=True,  # Hacer el campo buscable en la base de datos
    )

    def name_get(self):
        """
        Personaliza cómo se muestran los clientes en los menús desplegables.
        Incluye el Código de Cliente en el nombre, si está definido.
        """
        result = []
        for record in self:
            name = f"[{record.client_code}] {record.name}" if record.client_code else record.name
            result.append((record.id, name))
        return result
