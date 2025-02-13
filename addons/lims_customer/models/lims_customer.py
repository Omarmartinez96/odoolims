from odoo import models, fields

class LimsCustomer(models.Model):
    _name = 'lims.customer'
    _description = 'Gestión de Clientes'

    name = fields.Char(string='Nombre del Cliente', required=True)
    client_code = fields.Char(string='Código del Cliente', readonly=True)
    fiscal_address = fields.Char(string='Dirección Fiscal')
    
    branch_ids = fields.One2many('lims.branch', 'customer_id', string='Sucursales')

    def action_view_branches(self):
        """ Acción para abrir la vista de sucursales relacionadas con el cliente. """
        return {
            'name': 'Sucursales',
            'type': 'ir.actions.act_window',
            'res_model': 'lims.branch',
            'view_mode': 'list,form',
            'domain': [('customer_id', '=', self.id)],
        }
