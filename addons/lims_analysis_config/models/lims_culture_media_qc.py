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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'sequence' not in vals or vals.get('sequence') == 1:
                # Buscar el último número de secuencia
                last_media = self.search([], order='sequence desc', limit=1)
                vals['sequence'] = (last_media.sequence + 1) if last_media else 1
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