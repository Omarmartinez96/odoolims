from odoo import models, fields

class LimsBranch(models.Model):
    _name = 'lims.branch'
    _description = 'Sucursales de Clientes en LIMS'

    name = fields.Char(string="Nombre de la Sucursal", required=True)
    customer_id = fields.Many2one('lims.customer', string="Cliente", ondelete="cascade")
    address = fields.Char(string="Dirección")
    comment = fields.Text(string="Comentarios")
