# lims_sample.py
from odoo import models, fields, api
from odoo.exceptions import UserError

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
        ondelete='cascade'
    )
    sample_identifier = fields.Char(
        string="Identificación de Muestra", 
        required=True
    )
    sample_description = fields.Char(
        string="Descripción de la muestra"
    )
    sample_type_id = fields.Many2one(
        'lims.sample.type', 
        string='Tipo de Muestra', 
        help='Selecciona o crea el tipo de muestra'
    )
    date_received = fields.Datetime(
        string="Fecha de Recepción", 
        default=fields.Datetime.now
    )
    sample_state = fields.Selection(
        [('draft', 'Borrador'), 
         ('in_analysis', 'En Análisis'), 
         ('done', 'Finalizado')], 
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
    field_result_ids = fields.One2many(
        'lims.field.result',
        'sample_id',
        string='Resultados de Campo'
    )
    parameter_ids = fields.One2many(
        'lims.sample.parameter',
        'sample_id',
        string='Parámetros de Análisis'
    )
    
    # Recolección
    collection_date = fields.Date(
        string="Fecha de Recolección"
    )
    collection_time = fields.Char(
        string="Hora de Recolección", 
        help="Hora en que se realizó la recolección"
    )
    collection_temperature = fields.Char(
        string="Temperatura de Recolección", 
        help="Temperatura en grados Celsius al momento de la recolección"
    )    
    collected_by = fields.Char(
        string="Recolectado por", 
        help="Nombre del personal que realizó la recolección"
    )
    collection_observations = fields.Text(
        string="Observaciones de Recolección", 
        help="Observaciones generales sobre la recolección de la muestra"
    )

    # Muestreo
    sampling_plan = fields.Text(
        string="Plan de muestreo"
    )    
    sampling_date = fields.Date(
        string="Fecha de Muestreo"
    )
    sampling_time = fields.Char(
        string="Hora de Muestreo", 
        help="Hora en que se realizó el muestreo"
    )
    sampling_temperature = fields.Char(
        string="Temperatura de muestreo"
    )
    sampling_technician = fields.Char(
        string="Técnico de muestreo"
    )
    sampling_observations = fields.Text(
        string="Observaciones de Muestreo"
    )

    def create(self, vals_list):
        for vals in vals_list:
            text_fields_na = ['sampling_plan', 'sampling_observations']
            for field in text_fields_na:
                if not vals.get(field) or (isinstance(vals.get(field), str) and vals.get(field).strip() == ''):
                    vals[field] = 'N/A'

        return super(LimsSample, self).create(vals_list)

    def write(self, vals):
        text_fields_na = ['sampling_plan', 'sampling_observations']

        for field in text_fields_na:
            if field in vals: 
                if not vals.get(field) or (isinstance(vals.get(field), str) and vals.get(field).strip() == ''):
                    vals[field] = 'N/A'

        return super(LimsSample, self).write(vals)

    # Plantilla de muestras
    sample_template_id = fields.Many2one('lims.sample.template', string="Plantilla", domain="[('active', '=', True)]")

    @api.onchange('sample_template_id')
    def _onchange_sample_template_id(self):
        """Cargar datos de la plantilla seleccionada."""
        if self.sample_template_id:
            template = self.sample_template_id

            # Copiar datos de la plantilla a los campos de la muestra
            self.sample_type_id = template.sample_type_id
            self.container_type_id = template.container_type_id
            self.sample_description = template.sample_description
            self.sample_quantity = template.sample_quantity

            template.increment_usage()

            # NUEVA LÓGICA PARA PARÁMETROS
            if hasattr(template, 'parameter_template_ids') and template.parameter_template_ids:
                # Limpiar parámetros existentes
                self.parameter_ids = [(5, 0, 0)]
                
                # Crear nuevos parámetros desde plantillas
                new_params = []
                for param_template in template.parameter_template_ids:
                    param_vals = {
                        'template_id': param_template.id,
                        'name': param_template.name,
                        'method': param_template.method,
                        'category': param_template.category,
                        'microorganism': param_template.microorganism,
                        'is_template': False,
                    }
                    new_params.append((0, 0, param_vals))
                
                self.parameter_ids = new_params

    @api.onchange('sample_type_id')
    def _onchange_sample_suggestion(self):
        if self.sample_type_id and not self.sample_template_id:
            # Buscar muestras recientes de este tipo 
            recent_samples = self.search([
                ('sample_type_id', '=', self.sample_type_id.id)
            ], limit=1, order='create_date desc')
        
            if recent_samples:
                latest = recent_samples[0]
                if not self.sample_description:
                    self.sample_description = latest.sample_description
                if not self.container_type_id:
                    self.container_type_id = latest.container_type_id
                if not self.sample_quantity:
                    self.sample_quantity = latest.sample_quantity

    def action_save_as_template(self):
        """Acción para guardar la muestra actual como plantilla"""
        self.ensure_one()
        
        if not self.sample_type_id:
            raise UserError("Necesitas seleccionar tipo de muestra para crear una plantilla")
        
        # Generar nombre automático para la plantilla
        template_name = f"{self.sample_type_id.name}"
        
        # Verificar si ya existe
        existing = self.env['lims.sample.template'].search([
            ('name', '=', template_name)
        ])
        
        if existing:
            template_name = f"{template_name} ({fields.Datetime.now().strftime('%d/%m/%Y')})"
        
        # Crear la plantilla
        template = self.env['lims.sample.template'].create({
            'name': template_name,
            'sample_type_id': self.sample_type_id.id,
            'container_type_id': self.container_type_id.id if self.container_type_id else False,
            'sample_description': self.sample_description,
            'sample_quantity': self.sample_quantity,
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

    def name_get(self):
        result = []
        for record in self:
            # Solo mostrar muestras con identificación válida
            if record.sample_identifier:
                name = f"{record.sample_identifier}"
                if record.sample_description:
                    name += f" - {record.sample_description}"
                result.append((record.id, name))
            else:
                # Para registros huérfanos, no mostrar
                continue
        return result
    
    def copy(self, default=None):
        """Personalizar duplicado de muestras CON todos sus parámetros"""
        if default is None:
            default = {}
        
        # Solo limpiar identificación y descripción si no se especifica
        if 'sample_identifier' not in default:
            default['sample_identifier'] = ''
        if 'sample_description' not in default:
            default['sample_description'] = ''
        
        # Crear la nueva muestra SIN parámetros primero
        new_sample = super().copy(default)
        
        # Ahora copiar manualmente cada parámetro
        for parameter in self.parameter_ids:
            parameter.copy({
                'sample_id': new_sample.id,
            })
        
        # También copiar resultados de campo
        for field_result in self.field_result_ids:
            field_result.copy({
                'sample_id': new_sample.id,
            })
        
        return new_sample

    def action_duplicate_sample(self):
        """Acción para duplicar muestra desde interfaz"""
        self.ensure_one()
        
        # Crear copia (ya limpia automáticamente identificación y descripción)
        new_sample = self.copy()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Muestra Duplicada',
                'message': f'Se duplicó la muestra. Complete identificación y descripción.',
                'type': 'success',
            }
        }