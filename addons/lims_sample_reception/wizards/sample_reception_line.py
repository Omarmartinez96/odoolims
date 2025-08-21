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
    
    custody_chain_code = fields.Char(
        string='Cadena de Custodia',
        related='sample_id.custody_chain_id.custody_chain_code',
        readonly=True
    )

    suggested_code = fields.Char(
        string='Código Sugerido',
        compute='_compute_suggested_code'
    )
    
    sample_code = fields.Char(
        string='Código de Muestra',
        required=False,
        help='Se genera automáticamente solo si el estado es "Recibida"'
    )
    
    @api.depends('sample_id')
    def _compute_suggested_code(self):
        for line in self:
            if line.sample_id and line.sample_id.cliente_id:
                client_code = line.sample_id.cliente_id.client_code or 'XXX'
                
                # Buscar el máximo número existente en la base de datos
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
                
                # IMPORTANTE: También considerar códigos ya asignados en este wizard
                if line.wizard_id and line.wizard_id.sample_lines:
                    for other_line in line.wizard_id.sample_lines:
                        if (other_line.sample_code and 
                            other_line.sample_code.startswith(f'{client_code}/') and
                            other_line.id != line.id):
                            try:
                                parts = other_line.sample_code.split('/')
                                if len(parts) == 2:
                                    num = int(parts[1])
                                    if num > max_num:
                                        max_num = num
                            except:
                                pass
                
                # Sugerir el siguiente número
                next_num = str(max_num + 1).zfill(4)
                line.suggested_code = f'{client_code}/{next_num}'
                
                # NO auto-asignar código - dejar vacío por defecto
                if not line.sample_code:
                    line.sample_code = ''  # Dejar vacío por defecto
            else:
                line.suggested_code = 'XXX/0001'
                # NO auto-asignar código por defecto
                if not line.sample_code:
                    line.sample_code = ''  # Dejar vacío