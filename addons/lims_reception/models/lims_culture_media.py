from odoo import models, fields

class LimsCultureMedia(models.Model):
    _name = 'lims.culture.media'
    _description = 'Medios de Cultivo'
    _order = 'name'
    
    name = fields.Char(
        string='Nombre del Medio',
        required=True,
        translate=True
    )
    description = fields.Text(
        string='Descripción'
    )
    internal_id = fields.Char(
        string='Identificador',
        help='Código o identificador interno del laboratorio'
    )
    active = fields.Boolean(
        string='Activo', 
        default=True
    )
    
    def name_get(self):
        """
        FUNCIÓN: Personaliza cómo se muestra el medio en listas desplegables
        PARA QUE: En lugar de mostrar solo "Agar MacConkey", 
                 muestra "Agar MacConkey (MAC-001)"
        CUÁNDO SE USA: Automáticamente en campos Many2one
        """
        result = []
        for record in self:
            name = record.name
            if record.internal_id:
                name += f" ({record.internal_id})"
            result.append((record.id, name))
        return result