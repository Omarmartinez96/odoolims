from odoo import models, fields

class LimsCustodyChain(models.Model):
    _name = 'lims.custody_chain'
    _description = 'Cadena de Custodia'
    _rec_name = 'custody_chain_code'

    custody_chain_code = fields.Char(string="Código de Cadena de Custodia", required=True, copy=False)
    cliente_id = fields.Many2one('res.partner', string="Cliente", required=True, domain=[('is_lims_customer', '=', True)])
    sucursal_id = fields.Many2one('lims.branch', string="Sucursal", required=True, domain="[('customer_id', '=', cliente_id)]")
    departamento_id = fields.Many2one('lims.department', string="Departamento", domain="[('branch_id', '=', sucursal_id)]")
    date_created = fields.Datetime(string="Fecha de Creación", default=fields.Datetime.now)
    sample_ids = fields.One2many('lims.sample', 'custody_chain_id', string='Muestras Recibidas')
    state = fields.Selection([('draft', 'Borrador'), ('in_progress', 'En Proceso'), ('done', 'Finalizado')], default='draft', required=True)
