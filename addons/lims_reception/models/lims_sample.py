from odoo import models, fields, api

class LimsSample(models.Model):
    _name = 'lims.sample'
    _description = 'Recepción de Muestras'

    cliente_id = fields.Many2one(
        'res.partner',
        string="Cliente",
        required=True,
        help="Cliente asociado con la muestra."
    )

    client_code = fields.Char(
        string="Código de Cliente",
        related='cliente_id.client_code',
        readonly=True,
        store=True,
        help="Código único del cliente asociado a la muestra."
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

    sample_identifier = fields.Char(
        string="Identificación de Muestra",
        required=True,
        help="Descripción con la que el cliente identifica la muestra (Ejemplo: 'Salsa habanero lote 232498237487234')."
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

    def action_register_sample(self):
        """
        Método actualizado para el botón "Registrar Muestra".
        Se cambia el efecto visual por uno más formal.
        """
        self.ensure_one()
        self.state = 'in_analysis'
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'La muestra ha sido registrada y está en proceso de análisis.',
                'type': 'notification',  # Cambio de 'rainbow_man' a 'notification' para mayor formalidad
            }
        }
