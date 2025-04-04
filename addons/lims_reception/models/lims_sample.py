# lims_sample.py
from odoo import models, fields
from .constants.containers import reception_containers

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
    sample_state = fields.Selection(
        [('draft', 'Borrador'), ('in_analysis', 'En Análisis'), ('done', 'Finalizado')],
        string="Estado de la muestra",
        default='draft'
    )
    attachment_ids = fields.Many2many(
        'ir.attachment', 
        string="Adjuntos"
    )
    sample_quantity = fields.Char(
        string="Cantidad de muestra"
    )
    container_type_id = fields.Many2one( 
        'lims.container.type',
        string='Tipo de recipiente',
        help='Selecciona o crea el tipo de recipiente utilizado'
    )
    instrument_used = fields.Char(
        string="Instrumento utilizado"
    )
    field_results = fields.Char(
        string="Resultados en campo"
    )
    sampling_date = fields.Char(
        string="Fecha de Muestreo"
    )
    sampling_temperature = fields.Char(
        string="Temperatura de muestreo"
    )
    sampling_technician = fields.Char(
        string="Técnico de muestreo"
    )