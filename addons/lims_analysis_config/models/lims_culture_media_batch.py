from odoo import models, fields, api
from datetime import datetime

class LimsCultureMediaBatch(models.Model):
    _name = 'lims.culture.media.batch'
    _description = 'Lotes de Medios de Cultivo Preparados'
    _rec_name = 'batch_code'
    _order = 'preparation_date desc, batch_code desc'

    # Código del lote (auto-generado)
    batch_code = fields.Char(
        string='Código de Lote', 
        default='/', 
        copy=False,
    )
    
    # Relación con el catálogo de medios
    culture_media_id = fields.Many2one(
        'lims.culture.media',
        string='Medio de Cultivo',
        required=True
    )
    
    # Tipo de medio
    media_type = fields.Selection([
        ('prepared', 'Preparado en laboratorio'),
        ('dehydrated', 'Deshidratado comercial')
    ], string='Tipo de Medio', required=True, default='prepared')
    
    # Fechas
    preparation_date = fields.Date(
        string='Fecha de Preparación',
        default=fields.Date.context_today,
        required=True
    )
    expiry_date = fields.Date(
        string='Fecha de Vencimiento'
    )
    
    analyst_id = fields.Many2one(
        'lims.analyst',
        string='Preparado por (Analista)',
        help='Analista responsable que preparó el medio'
    )

    # DEPRECADO: Campo de texto libre
    prepared_by = fields.Char(
        string='Preparado por (Texto)',
        help='DEPRECADO: Use el campo Analista'
    )
    
    # Datos técnicos
    volume_prepared = fields.Float(
        string='Volumen Preparado (mL)',
        help='Cantidad total preparada en mililitros'
    )
    ph_value = fields.Float(
        string='pH Medido',
        digits=(3, 2)
    )
    
    # Método de esterilización
    sterilization_method = fields.Selection([
        ('autoclave', 'Autoclave'),
        ('dry_heat', 'Calor seco'),
        ('filtration', 'Filtración'),
        ('none', 'Sin esterilización')
    ], string='Método de Esterilización')
    
    # Notas
    preparation_notes = fields.Text(
        string='Notas de Preparación'
    )
    
    @api.model_create_multi
    def create(self, vals_list):
        """Generar código de lote automáticamente"""
        for vals in vals_list:
            if vals.get('batch_code', '/') == '/':
                media = self.env['lims.culture.media'].browse(vals.get('culture_media_id'))
                if media:
                    # NUEVA LÓGICA: Usar batch_prefix si existe, sino extraer de internal_id
                    prefix_code = media.batch_prefix
                    if not prefix_code and media.internal_id:
                        # Extraer la parte después del último guión
                        if '-' in media.internal_id:
                            prefix_code = media.internal_id.split('-')[-1]
                        else:
                            prefix_code = media.internal_id
                    
                    if prefix_code:
                        # Formato mejorado: TSA-260825-1
                        prep_date = fields.Date.from_string(vals.get('preparation_date')) if vals.get('preparation_date') else fields.Date.context_today(self)
                        date_part = prep_date.strftime('%d%m%y')  # 260825
                        prefix = f"{prefix_code}-{date_part}"
                        
                        # Buscar consecutivo del día
                        existing = self.search([('batch_code', 'like', f'{prefix}-%')])
                        numbers = []
                        for code in existing.mapped('batch_code'):
                            try:
                                numbers.append(int(code.split('-')[-1]))
                            except (ValueError, IndexError):
                                pass
                        
                        next_num = max(numbers, default=0) + 1
                        vals['batch_code'] = f"{prefix}-{next_num}"
        
        return super().create(vals_list)
    
    def action_assign_analyst(self):
        """Abrir wizard para asignar analista responsable con verificación PIN"""
        self.ensure_one()
        
        return self.env['lims.analyst'].open_assignment_wizard(
            source_model='lims.culture.media.batch',
            source_record_id=self.id,
            source_field='analyst_id',
            action_description=f'Asignar responsable del lote {self.batch_code or "nuevo"}'
        )

    def action_change_analyst(self):
        """Cambiar analista responsable con verificación PIN"""
        self.ensure_one()
        
        return self.env['lims.analyst'].open_assignment_wizard(
            source_model='lims.culture.media.batch',
            source_record_id=self.id,
            source_field='analyst_id',
            action_description=f'Cambiar responsable del lote {self.batch_code}'
        )