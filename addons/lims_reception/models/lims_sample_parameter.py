# lims_sample_parameter.py
from odoo import models, fields, api

class LimsSampleParameter(models.Model):
    _name = 'lims.sample.parameter'
    _description = 'Parámetros de Muestra'
    _order = 'sequence, name'

    # Relación con la muestra (OPCIONAL ahora)
    sample_id = fields.Many2one(
        'lims.sample',
        string='Muestra',
        ondelete='cascade'
    )
    
    # 🆕 CAMPO PARA INDICAR SI ES PLANTILLA
    is_template = fields.Boolean(
        string='Es Plantilla',
        default=False,
        help='Marcar si este parámetro es una plantilla reutilizable'
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

    microorganism = fields.Char(
        string='Microorganismo', 
        help='Ej: Coliformes totales, E. coli'
    )
    
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
    
    # Resultados y control (SOLO para parámetros de muestra, no plantillas)
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
    
    # 🆕 PLANTILLA DE ORIGEN (referencia a otro parámetro plantilla)
    template_id = fields.Many2one(
        'lims.sample.parameter',
        string='Plantilla de Origen',
        domain=[('is_template', '=', True)],
        help='Seleccionar parámetro plantilla para copiar configuración'
    )
    
    # 🆕 CAMPOS PARA CONTROL DE PLANTILLAS
    times_used = fields.Integer(
        string="Veces Utilizada", 
        default=0,
        readonly=True,
        help="Contador de cuántas veces se ha usado esta plantilla"
    )
    
    active = fields.Boolean(
        string='Activo', 
        default=True
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
            parts = []
            if record.name:
                parts.append(record.name)
            if record.method:
                parts.append(f"({record.method})")
            if record.unit:
                parts.append(f"[{record.unit}]")
            record.parameter_info = " ".join(parts) if parts else ""
    
    @api.model
    def create_from_template(self, sample_id, template_id):
        """Crear parámetro desde plantilla"""
        template = self.browse(template_id)
        if not template.exists() or not template.is_template:
            return False
        
        # Incrementar contador de uso
        template.times_used += 1
            
        return self.create({
            'sample_id': sample_id,
            'template_id': template_id,
            'name': template.name,
            'description': template.description,
            'unit': template.unit,
            'method': template.method,
            'category': template.category,
            'microorganism': template.microorganism,
            'method_reference': template.method_reference,
            'incubation_temperature': template.incubation_temperature,
            'incubation_time': template.incubation_time,
            'culture_medium': template.culture_medium,
            'ph_conditions': template.ph_conditions,
            'preservation_conditions': template.preservation_conditions,
            'sample_preparation': template.sample_preparation,
            'detection_limit': template.detection_limit,
            'quantification_limit': template.quantification_limit,
            'is_template': False,  # El nuevo NO es plantilla
        })
    
    def name_get(self):
        """Mostrar nombre completo en listas"""
        result = []
        for record in self:
            name = record.name
            if record.is_template:
                name = f"🔧 {name}"  # Icono para plantillas
            if record.unit:
                name += f" ({record.unit})"
            if record.method:
                name += f" - {record.method}"
            result.append((record.id, name))
        return result
    
    @api.onchange('template_id')
    def _onchange_template_id(self):
        if self.template_id:
            template = self.template_id
            # Copiar todos los campos de la plantilla
            self.name = template.name
            self.category = template.category
            self.method = template.method
            self.unit = template.unit
            self.description = template.description
            self.microorganism = template.microorganism
            self.method_reference = template.method_reference
            self.incubation_temperature = template.incubation_temperature
            self.incubation_time = template.incubation_time
            self.culture_medium = template.culture_medium
            self.ph_conditions = template.ph_conditions
            self.preservation_conditions = template.preservation_conditions
            self.sample_preparation = template.sample_preparation
            self.detection_limit = template.detection_limit
            self.quantification_limit = template.quantification_limit
            
            # Incrementar contador
            template.times_used += 1
    
    def action_save_as_template(self):
        """Convertir parámetro actual en plantilla"""
        self.ensure_one()
        if self.is_template:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Ya es Plantilla',
                    'message': 'Este parámetro ya es una plantilla',
                    'type': 'info',
                }
            }
        
        # Crear copia como plantilla
        template = self.copy({
            'is_template': True,
            'sample_id': False,  # Las plantillas no tienen muestra
            'result': False,     # Las plantillas no tienen resultados
            'state': 'pending',
            'times_used': 0,
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Plantilla Creada',
                'message': f'Plantilla "{template.name}" creada exitosamente',
                'type': 'success',
            }
        }