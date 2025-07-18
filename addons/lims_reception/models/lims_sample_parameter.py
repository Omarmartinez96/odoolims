# lims_sample_parameter.py
from odoo import models, fields, api

class LimsSampleParameter(models.Model):
    _name = 'lims.sample.parameter'
    _description = 'Parámetros de Muestra'
    _order = 'sequence, name'

    # Relación con la muestra
    sample_id = fields.Many2one(
        'lims.sample',
        string='Muestra',
        required=True,
        ondelete='cascade'
    )
    
    # Información básica del parámetro
    name = fields.Char(
        string='Nombre del Parámetro',
        required=True
    )
    description = fields.Text(
        string='Descripción'
    )
    unit = fields.Char(
        string='Unidad',
        help='Ej: mg/L, µg/g, UFC/mL'
    )
    category = fields.Selection([
        ('physical', 'Físico'),
        ('chemical', 'Químico'),
        ('microbiological', 'Microbiológico'),
        ('other', 'Otro')
    ], string='Categoría')
    
    # Información del método
    method = fields.Char(
        string='Método de Análisis',
        help='Método o norma utilizada'
    )
    method_reference = fields.Char(
        string='Referencia del Método',
        help='Ej: ASTM D1293, EPA 200.8'
    )
    
    # Condiciones de análisis
    incubation_temperature = fields.Char(
        string='Temperatura de Incubación',
        help='Ej: 37°C, 25±2°C'
    )
    incubation_time = fields.Char(
        string='Tiempo de Incubación',
        help='Ej: 24h, 48-72h'
    )
    culture_medium = fields.Char(
        string='Medio de Cultivo',
        help='Para análisis microbiológicos'
    )
    
    # Condiciones específicas adicionales
    ph_conditions = fields.Char(
        string='Condiciones de pH'
    )
    preservation_conditions = fields.Text(
        string='Condiciones de Preservación',
        help='Refrigeración, conservantes, tiempo máximo, etc.'
    )
    sample_preparation = fields.Text(
        string='Preparación de Muestra',
        help='Pasos previos al análisis'
    )
    
    # Resultados y control
    result = fields.Char(
        string='Resultado'
    )
    detection_limit = fields.Char(
        string='Límite de Detección'
    )
    quantification_limit = fields.Char(
        string='Límite de Cuantificación'
    )
    
    # Estado y control
    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help='Orden de los parámetros'
    )
    state = fields.Selection([
        ('pending', 'Pendiente'),
        ('in_progress', 'En Análisis'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado')
    ], string='Estado', default='pending')
    
    # Observaciones
    analyst_notes = fields.Text(
        string='Notas del Analista'
    )
    observations = fields.Text(
        string='Observaciones Generales'
    )
    
    # Plantilla de origen (para trazabilidad)
    template_id = fields.Many2one(
        'lims.parameter.template',
        string='Plantilla de Origen',
        readonly=True
    )
    
    # Campos computados
    parameter_info = fields.Char(
        string='Info Completa',
        compute='_compute_parameter_info',
        store=True
    )
    
    @api.depends('name', 'method', 'unit')
    def _compute_parameter_info(self):
        for record in self:
            parts = [record.name]
            if record.method:
                parts.append(f"({record.method})")
            if record.unit:
                parts.append(f"[{record.unit}]")
            record.parameter_info = " ".join(parts)
    
    @api.model
    def create_from_template(self, sample_id, template_id):
        """Crear parámetro desde plantilla"""
        template = self.env['lims.parameter.template'].browse(template_id)
        if not template.exists():
            return False
            
        return self.create({
            'sample_id': sample_id,
            'template_id': template_id,
            'name': template.name,
            'description': template.description,
            'unit': template.unit,
            'method': template.method,
            'category': template.category,
        })
    
    def name_get(self):
        """Mostrar nombre completo en listas"""
        result = []
        for record in self:
            name = record.name
            if record.unit:
                name += f" ({record.unit})"
            if record.method:
                name += f" - {record.method}"
            result.append((record.id, name))
        return result