from odoo import models, fields, api

class LimsSample(models.Model):
    _name = 'lims.sample'
    _description = 'Recepción de Muestras'

    cliente_id = fields.Many2one(
        'res.partner', 
        string="Cliente", 
        related='custody_chain_id.cliente_id',
        readonly=True,
        store=True
    )

    sucursal_id = fields.Many2one(
        'lims.branch',
        string="Sucursal",
        related='custody_chain_id.sucursal_id',
        readonly=True,
        store=True
    )

    departamento_id = fields.Many2one(
        'lims.department',
        string="Departamento",
        related='custody_chain_id.departamento_id',
        readonly=True,
        store=True
    )

    custody_chain_id = fields.Many2one(
        'lims.custody_chain',
        string="Cadena de Custodia",
        help="Número de Cadena de Custodia asociada."
    )

    sample_identifier = fields.Char(
        string="Identificación de Muestra",
        required=True,
        help="Identificación con la que el cliente identifica la muestra."
    )

    sample_description = fields.Char(  
        string="Descripción de la muestra",
        help="Descripción específica de la muestra si aplica"
    )

    sample_type = fields.Char(
        string="Tipo de Muestra",
        help="Tipo o descripción de la muestra."
    )

    state = fields.Selection(
        [('draft', 'Borrador'),
         ('in_analysis', 'En Análisis'),
         ('done', 'Finalizado')],
        string="Estado",
        default='draft',
        required=True,
        help="Estado actual de la muestra."
    )

    date_received = fields.Datetime(
        string="Fecha de Recepción",
        default=fields.Datetime.now,
        help="Fecha en la que se recibió la muestra."
    )

    attachment_ids = fields.Many2many(
        'ir.attachment',
        string="Adjuntos",
        help="Archivos relacionados con esta muestra."
    )
