# lims_sample.py
from odoo import models, fields

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
        string="Cadena de Custodia"
    )

    sample_identifier = fields.Char(
        string="Identificación de Muestra", 
        required=True
    )
    sample_description = fields.Char(
        string="Descripción de la muestra"
    )
    sample_type = fields.Char(
        string="Tipo de Muestra"
    )
    date_received = fields.Datetime(
        string="Fecha de Recepción", 
        default=fields.Datetime.now
    )
    state = fields.Selection(
        [('draft', 'Borrador'), ('in_analysis', 'En Análisis'), ('done', 'Finalizado')],
        default='draft'
    )
    attachment_ids = fields.Many2many(
        'ir.attachment', 
        string="Adjuntos"
    )
