from odoo import models, fields

class LimsSample(models.Model):
    _name = 'lims.sample'
    _description = 'Recepción de Muestras'

    sample_code = fields.Char(
        string="Código de Muestra",
        required=True,
        copy=False,
        default=lambda self: self.env['ir.sequence'].next_by_code('lims.sample')
    )
    cliente_id = fields.Many2one('res.partner', string="Cliente", required=True)
    sucursal_id = fields.Many2one(
        'res.sucursal', string="Sucursal", required=True,
        domain="[('cliente_id', '=', cliente_id)]"
    )
    departamento_id = fields.Many2one(
        'res.departamento', string="Departamento",
        domain="[('sucursal_id', '=', sucursal_id)]"
    )
    state = fields.Selection(
        [('draft', 'Borrador'),
         ('in_analysis', 'En Análisis'),
         ('done', 'Finalizado')],
        string="Estado",
        default='draft',
        required=True
    )
    date_received = fields.Datetime(string="Fecha de Recepción", default=fields.Datetime.now)
    attachment_ids = fields.Many2many(
        'ir.attachment', string="Adjuntos",
        help="Archivos relacionados con esta muestra."
    )
