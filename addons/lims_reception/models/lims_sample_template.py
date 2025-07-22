from odoo import models, fields, api

class LimsSampleTemplate(models.Model):
    _name = 'lims.sample.template'
    _description = 'Plantillas de Muestras Frecuentes'
    _order = 'times_used desc, name'

    name = fields.Char(string="Nombre de la Plantilla", required=True, help="Ej: Agua Potable - Restaurante XYZ")
    sample_type_id = fields.Many2one('lims.sample.type', string="Tipo de Muestra")
    container_type_id = fields.Many2one('lims.container.type', string="Tipo de Recipiente")
    sample_description = fields.Char(string="Descripción Estándar", help="Descripción que se copiará a nuevas muestras")
    sample_quantity = fields.Char(string="Cantidad Típica", help="Ej: 500ml, 100g, etc.")
    
    parameter_template_ids = fields.Many2many(
        'lims.sample.parameter',
        'sample_template_parameter_rel',  # tabla intermedia
        'template_id',
        'parameter_id',
        string="Plantillas de Parámetros",
        domain=[('is_template', '=', True)],
        help="Parámetros que se crearán automáticamente con esta plantilla"
    )

    # Campos de control
    times_used = fields.Integer(
        string="Veces Utilizada", 
        default=0,
        readonly=True
    )
    active = fields.Boolean(
        string="Activo", 
        default=True
    )
    create_date = fields.Datetime(
        string="Fecha de Creación", 
        readonly=True
    )
    _sql_constraints = [
        ('unique_template_name_', 
         'unique(name)', 
         'Ya existe una plantilla con este nombre')
    ]
    def increment_usage(self):
        """Incrementa el contador de uso de la plantilla"""
        self.times_used += 1

    def create_parameters_for_sample(self, sample_id):
        """Crear parámetros desde las plantillas asociadas"""