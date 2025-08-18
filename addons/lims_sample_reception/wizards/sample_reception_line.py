from odoo import models, fields, api

class SampleReceptionLine(models.TransientModel):
    _name = 'lims.sample.reception.line'
    _description = 'Línea de Muestra para Recepción'
    
    wizard_id = fields.Many2one(
        'lims.sample.reception.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade'
    )
    
    sample_id = fields.Many2one(
        'lims.sample',
        string='Muestra',
        required=True
    )
    
    sample_identifier = fields.Char(
        string='Identificación',
        related='sample_id.sample_identifier',
        readonly=True
    )
    
    suggested_code = fields.Char(
        string='Código Sugerido',
        compute='_compute_suggested_code'
    )
    
    sample_code = fields.Char(
        string='Código de Muestra',
        required=True,
        help='Editable - se generará automáticamente pero puede modificarse'
    )
    
    @api.depends('sample_id')
    def _compute_suggested_code(self):
        for line in self:
            if line.sample_id and line.sample_id.cliente_id:
                client_code = line.sample_id.cliente_id.client_code or 'XXX'
                existing = self.env['lims.sample.reception'].search([
                    ('sample_code', 'like', f'{client_code}/%'),
                    ('sample_code', '!=', '/')
                ])
                max_num = 0
                for rec in existing:
                    try:
                        parts = rec.sample_code.split('/')
                        if len(parts) == 2:
                            num = int(parts[1])
                            if num > max_num:
                                max_num = num
                    except:
                        pass
                next_num = str(max_num + 1).zfill(4)
                line.suggested_code = f'{client_code}/{next_num}'
                # Auto-asignar si está vacío
                if not line.sample_code:
                    line.sample_code = line.suggested_code
            else:
                line.suggested_code = 'XXX/0001'
                if not line.sample_code:
                    line.sample_code = line.suggested_code