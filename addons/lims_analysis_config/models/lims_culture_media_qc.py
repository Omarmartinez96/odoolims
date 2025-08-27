from odoo import models, fields, api

class LimsCultureMediaQC(models.Model):
    _name = 'lims.culture.media.qc'
    _description = 'Controles de Calidad por Medio de Cultivo'
    _order = 'sequence, id'
    
    culture_media_id = fields.Many2one(
        'lims.culture.media',
        string='Medio de Cultivo',
        required=True,
        ondelete='cascade'
    )
    
    qc_type_id = fields.Many2one(
        'lims.quality.control.type',
        string='Tipo de Control',
        required=True
    )
    
    expected_result = fields.Char(
        string='Resultado Esperado',
        required=True
    )
    
    is_mandatory = fields.Boolean(
        string='Obligatorio',
        default=True
    )
    
    sequence = fields.Integer(
        string='Secuencia',
        default=10
    )
    
    notes = fields.Text(
        string='Notas'
    )
    
    @api.onchange('qc_type_id')
    def _onchange_qc_type_id(self):
        """Auto-llenar resultado esperado desde el tipo de control"""
        if self.qc_type_id and self.qc_type_id.default_expected_result:
            self.expected_result = self.qc_type_id.default_expected_result


class LimsCultureMedia(models.Model):
    _inherit = 'lims.culture.media'
    
    # Extender el modelo existente
    media_qc_ids = fields.One2many(
        'lims.culture.media.qc',
        'culture_media_id',
        string='Controles de Calidad del Medio'
    )
    
    sequence = fields.Integer(
        string='Secuencia',
        help='Número secuencial automático del medio'
    )

    batch_prefix = fields.Char(
        string='Prefijo para Lotes',
        help='Código específico para generación de lotes (ej: TSA, MAC, BHI)'
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'sequence' not in vals or vals.get('sequence') == 1:
                # Buscar el último número de secuencia
                last_media = self.search([], order='sequence desc', limit=1)
                vals['sequence'] = (last_media.sequence + 1) if last_media else 1
            
            # Auto-generar prefijo para lotes si no existe
            if not vals.get('batch_prefix') and vals.get('internal_id'):
                # Extraer solo la parte después del último guión
                internal_id = vals['internal_id']
                if '-' in internal_id:
                    vals['batch_prefix'] = internal_id.split('-')[-1]  # Toma "TSA" de "24-TSA"
                else:
                    vals['batch_prefix'] = internal_id
                    
        return super().create(vals_list)


    def name_get(self):
        """
        Sobrescribir para mostrar si tiene controles de calidad
        """
        result = []
        for record in self:
            name = record.name
            if record.internal_id:
                name += f" ({record.internal_id})"
            if record.media_qc_ids:
                name += f" [{len(record.media_qc_ids)} QC]"
            result.append((record.id, name))
        return result
    
    def action_assign_sequences(self):
        """Método temporal para asignar secuencias a registros existentes"""
        medias_without_sequence = self.search([('sequence', '=', 1)])
        for i, media in enumerate(medias_without_sequence, start=1):
            media.sequence = i
        return True
    
    def action_recompute_batch_prefixes(self):
        """Recalcular prefijos de lote para todos los medios existentes"""
        all_medias = self.env['lims.culture.media'].search([])
        updated_count = 0
        
        for media in all_medias:
            if not media.batch_prefix and media.internal_id:
                # Extraer la parte después del último guión
                if '-' in media.internal_id:
                    new_prefix = media.internal_id.split('-')[-1]
                else:
                    new_prefix = media.internal_id
                
                media.batch_prefix = new_prefix
                updated_count += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Recomputo Completado',
                'message': f'Se actualizaron {updated_count} medios de cultivo con prefijos automáticos',
                'type': 'success',
            }
        }