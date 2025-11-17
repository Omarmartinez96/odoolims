from odoo import models, fields, api

class LimsCultureMedia(models.Model):
    _name = 'lims.culture.media'
    _description = 'Medios de Cultivo'
    _order = 'sequence, name'
    
    name = fields.Char(
        string='Nombre del Medio',
        required=True,
        translate=True
    )
    description = fields.Text(
        string='Descripción'
    )
    internal_id = fields.Char(
        string='Identificador Interno',
        help='Código o identificador interno del laboratorio'
    )
    
    # NUEVO: Campo para prefijos de lotes
    batch_prefix = fields.Char(
        string='Prefijo para Lotes',
        help='Código específico para generación de lotes (ej: TSA, MAC, BHI)'
    )
    
    sequence = fields.Integer(
        string='Secuencia',
        help='Número secuencial automático del medio'
    )
    
    active = fields.Boolean(
        string='Activo', 
        default=True
    )
    
    # Relación con controles de calidad
    media_qc_ids = fields.One2many(
        'lims.culture.media.qc',
        'culture_media_id',
        string='Controles de Calidad del Medio'
    )
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Auto-asignar secuencia
            if 'sequence' not in vals or vals.get('sequence') == 1:
                last_media = self.search([], order='sequence desc', limit=1)
                vals['sequence'] = (last_media.sequence + 1) if last_media else 1
            
            # Auto-generar prefijo para lotes si no existe
            if not vals.get('batch_prefix') and vals.get('internal_id'):
                internal_id = vals['internal_id']
                if '-' in internal_id:
                    vals['batch_prefix'] = internal_id.split('-')[-1]  # Toma "TSA" de "24-TSA"
                else:
                    vals['batch_prefix'] = internal_id
                    
        return super().create(vals_list)

    def name_get(self):
        """Personaliza cómo se muestra el medio en listas desplegables"""
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
        """Método para asignar secuencias a registros existentes"""
        medias_without_sequence = self.search([('sequence', '=', 1)])
        for i, media in enumerate(medias_without_sequence, start=1):
            media.sequence = i
        return True
        