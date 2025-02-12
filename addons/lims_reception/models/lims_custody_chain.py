from odoo import models, fields, api

class LimsCustodyChain(models.Model):
    _name = 'lims.custody_chain'
    _description = 'Cadena de Custodia'
    _rec_name = 'custody_chain_code'

    custody_chain_code = fields.Char(
        string="Código de Cadena de Custodia",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self._generate_custody_code()
    )

    cliente_id = fields.Many2one(
        'res.partner',
        string="Cliente",
        required=True,
        help="Cliente asociado con la cadena de custodia."
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

    date_created = fields.Datetime(
        string="Fecha de Creación",
        default=fields.Datetime.now,
        readonly=True
    )

    state = fields.Selection(
        [('draft', 'Borrador'),
         ('in_progress', 'En Proceso'),
         ('done', 'Finalizado')],
        string="Estado",
        default='draft',
        required=True,
        help="Estado de la cadena de custodia."
    )

    sample_ids = fields.One2many(
        'lims.sample',
        'custody_chain_id',
        string="Muestras Asociadas",
        help="Lista de muestras asociadas a esta cadena de custodia."
    )

    @api.model
    def _generate_custody_code(self):
        """Genera un código único para la cadena de custodia."""
        return self.env['ir.sequence'].next_by_code('lims.custody_chain') or 'CC-00000'
