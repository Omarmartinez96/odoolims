from odoo import models, fields

class LimsParameterCultureMedia(models.Model):
    _name = 'lims.parameter.culture.media'
    _description = 'Medios de Cultivo por Parámetro'
    _order = 'sequence, id'

    sequence = fields.Integer(
        string='Secuencia', 
        default=10
    )
    # FUNCIÓN: Conecta con el parámetro padre
    # PARA QUE: Saber a qué parámetro pertenece este medio
    parameter_id = fields.Many2one(
        'lims.sample.parameter',
        string='Parámetro',
        required=True,
        ondelete='cascade'  # Si se borra el parámetro, se borra esta relación
    )
    # FUNCIÓN: Conecta con el catálogo de medios
    # PARA QUE: Seleccionar un medio del catálogo maestro
    culture_media_id = fields.Many2one(
        'lims.culture.media',
        string='Medio de Cultivo',
        required=True
    )
    # FUNCIÓN: Notas específicas para este parámetro
    # PARA QUE: El mismo medio puede tener instrucciones diferentes 
    #          según el parámetro (ej: "Incubar 24h para Coliformes, 48h para Salmonella")
    notes = fields.Text(
        string='Notas'
    )