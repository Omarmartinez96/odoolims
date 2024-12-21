from odoo import models, fields, api

class LimsSample(models.Model):
    _name = 'lims.sample'
    _description = 'Recepción de Muestras'

    # Código único de muestra, editable
    sample_code = fields.Char(
        string="Código de Muestra",
        required=True,
        copy=False,
        default=lambda self: self._get_default_sample_code(),
        help="Identificación única para la muestra. Puede ser manual."
    )

    # Identificación descriptiva de la muestra (editable, ingresada por el usuario)
    sample_identifier = fields.Char(
        string="Identificación de Muestra",
        required=True,
        help="Descripción que identifica la muestra para el cliente. Ejemplo: 'Salsa habanero lote: 232498237487234'."
    )

    cliente_id = fields.Many2one(
        'res.partner',
        string="Cliente",
        required=True,
        help="Cliente asociado con la muestra."
    )
    
    sucursal_id = fields.Many2one(
        'res.sucursal',
        string="Sucursal",
        required=True,
        domain="[('cliente_id', '=', cliente_id)]",
        help="Sucursal asociada al cliente seleccionado."
    )
    
    departamento_id = fields.Many2one(
        'res.departamento',
        string="Departamento",
        domain="[('sucursal_id', '=', sucursal_id)]",
        help="Departamento asociado a la sucursal seleccionada."
    )
    
    sample_type = fields.Char(
        string="Tipo de Muestra",
        help="Tipo o descripción de la muestra."
    )
    
    state = fields.Selection(
        [('draft', 'Borrador'),
         ('in_analysis', 'En Análisis'),
         ('done', 'Finalizado')],
        string="Estado",
        default='draft',
        required=True,
        help="Estado actual de la muestra."
    )
    
    date_received = fields.Datetime(
        string="Fecha de Recepción",
        default=fields.Datetime.now,
        help="Fecha en la que se recibió la muestra."
    )
    
    attachment_ids = fields.Many2many(
        'ir.attachment',
        string="Adjuntos",
        help="Archivos relacionados con esta muestra."
    )

    @api.model
    def _get_default_sample_code(self):
        """
        Genera un valor predeterminado para 'sample_code' si no se proporciona manualmente.
        """
        return self.env['ir.sequence'].next_by_code('lims.sample') or "Nuevo"
