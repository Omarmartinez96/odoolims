# lims_sample_parameter.py
from odoo import models, fields, api

class LimsSampleParameter(models.Model):
    _name = 'lims.sample.parameter'
    _description = 'Parámetros de Muestra'
    # Relación con controles de calidad
    quality_control_ids = fields.One2many(
        'lims.quality.control',
        'parameter_id',
        string='Controles de Calidad'
    )
    _order = 'name'

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
        translate=True,
        required=True
    )
    description = fields.Text(
        string='Descripción'
    )
    unit = fields.Char(
        string='Unidad',
        translate=True,
        help='Ej: mg/L, µg/g, UFC/mL'
    )
    category = fields.Selection([
        ('physical', 'Físico'),
        ('chemical', 'Químico'),
        ('microbiological', 'Microbiológico'),
        ('other', 'Otro')
    ], 
        string='Categoría'
    )

    microorganism = fields.Char(
        string='Microorganismo/Analito', 
        translate=True,
        help='⚠️ NOTA: Esto es lo que se mostrará al cliente en los informes de ensayo'
    )
    
    # Acreditaciones
    accreditation_iso = fields.Boolean(
        string='Acreditado ISO/IEC 17025',
        default=False
    )
    authorized_cofepris = fields.Boolean(
        string='Autorizado por COFEPRIS',
        default=False
    )
    accredited_ema = fields.Boolean(
        string='Acreditado EMA', 
        default=False
    )
    other_accreditation = fields.Boolean(
        string='Otra Acreditación',
        default=False
    )
    other_accreditation_detail = fields.Char(
        string='Especifique Otra Acreditación'
    )

    # Tipo de análisis
    analysis_internal = fields.Boolean(
        string='Análisis Interno',
        default=True
    )
    analysis_external = fields.Boolean(
        string='Laboratorio Externo/Subrogado',
        default=False
    )
    external_lab_name = fields.Char(
        string='Nombre del Laboratorio Externo'
    )

    # Tipos de muestra aplicables
    applicable_sample_types = fields.Many2many(
        'lims.sample.type', 
        string='Tipos de Muestra Aplicables'
    )

    # Control de calidad
    quality_control_procedure = fields.Text(
        string='Procedimiento de Control de Calidad'
    )
    quality_control_frequency = fields.Char(
        string='Frecuencia de Control de Calidad'
    )
    quality_control_acceptance = fields.Text(
        string='Criterios de Aceptación'
    )

    # Información del método
    method = fields.Char(
        string='Método de Análisis',
        help='⚠️ NOTA: Esto es lo que el cliente verá en su informe final. Cuidar ortografía.'
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
    culture_media_ids = fields.One2many(
        'lims.parameter.culture.media',
        'parameter_id',
        string='Medios de Cultivo'
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
    
    detection_limit = fields.Char(
        string='Límite de Detección'
    )
    quantification_limit = fields.Char(
        string='Límite de Cuantificación'
    )
    
    # Observaciones
    analyst_notes = fields.Text(
        string='Notas para el Analista',
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
            'culture_media_ids': template.culture_media_ids,
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
            self.culture_media_ids = template.culture_media_ids
            self.ph_conditions = template.ph_conditions
            self.preservation_conditions = template.preservation_conditions
            self.sample_preparation = template.sample_preparation
            self.detection_limit = template.detection_limit
            self.quantification_limit = template.quantification_limit
            
            if template.culture_media_ids:
                culture_media_lines = []
                for cm in template.culture_media_ids:
                    culture_media_lines.append((0, 0, {
                        'culture_media_id': cm.culture_media_id.id,
                        'notes': cm.notes,
                        'sequence': cm.sequence,
                    }))
                self.culture_media_ids = culture_media_lines

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
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create para añadir controles de calidad por defecto"""
        records = super().create(vals_list)
        for record in records:
            if not record.is_template and not record.quality_control_ids:
                # Añadir control de esterilidad por defecto si es microbiológico
                if record.category == 'microbiological':
                    self._create_default_quality_controls(record)
        return records
    
    def _create_default_quality_controls(self, parameter):
        """Crear controles de calidad por defecto"""
        # Buscar tipo de control de esterilidad
        sterility_type = self.env['lims.quality.control.type'].search([
            ('category', '=', 'sterility')
        ], limit=1)
        
        if sterility_type:
            self.env['lims.quality.control'].create({
                'parameter_id': parameter.id,
                'control_type_id': sterility_type.id,
                'expected_result': 'Estéril',
                'sequence': 10
            })

    def copy(self, default=None):
        """Personalizar duplicado de parámetros CON medios de cultivo y controles"""
        if default is None:
            default = {}
        
        # Crear el nuevo parámetro
        new_parameter = super().copy(default)
        
        # Copiar manualmente los medios de cultivo
        for culture_media in self.culture_media_ids:
            culture_media.copy({
                'parameter_id': new_parameter.id,
            })
        
        # Copiar manualmente los controles de calidad
        for quality_control in self.quality_control_ids:
            quality_control.copy({
                'parameter_id': new_parameter.id,
            })
        
        return new_parameter