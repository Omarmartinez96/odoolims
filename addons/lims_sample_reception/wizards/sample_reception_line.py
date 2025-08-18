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
    
    @api.depends('sample_id', 'wizard_id.sample_lines')
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
                
                # Calcular el offset basado en la posición en el wizard
                if line.wizard_id and line.wizard_id.sample_lines:
                    # Filtrar líneas del mismo cliente ordenadas por create_date o id
                    same_client_lines = line.wizard_id.sample_lines.filtered(
                        lambda l: l.sample_id and l.sample_id.cliente_id == line.sample_id.cliente_id
                    )
                    
                    # Convertir a lista y ordenar para mantener orden consistente
                    same_client_lines_list = list(same_client_lines)
                    same_client_lines_list.sort(key=lambda x: x.id or 0)
                    
                    # Encontrar la posición de esta línea
                    line_position = 0
                    for i, other_line in enumerate(same_client_lines_list):
                        if other_line == line:
                            line_position = i
                            break
                    
                    # El número consecutivo considerando la posición
                    next_num = str(max_num + 1 + line_position).zfill(4)
                else:
                    next_num = str(max_num + 1).zfill(4)
                
                line.suggested_code = f'{client_code}/{next_num}'
                
                # Auto-asignar si está vacío O si es la primera vez que se calcula
                if not line.sample_code or line.sample_code == '/':
                    line.sample_code = line.suggested_code
            else:
                line.suggested_code = 'XXX/0001'
                if not line.sample_code or line.sample_code == '/':
                    line.sample_code = line.suggested_code

    @api.model_create_multi
    def create(self, vals_list):
        """Override create para asegurar códigos únicos al crear múltiples líneas"""
        lines = super().create(vals_list)
        
        # Reagrupar por wizard y cliente
        wizard_groups = {}
        for line in lines:
            if line.wizard_id:
                if line.wizard_id not in wizard_groups:
                    wizard_groups[line.wizard_id] = {}
                
                if line.sample_id and line.sample_id.cliente_id:
                    client_code = line.sample_id.cliente_id.client_code or 'XXX'
                    if client_code not in wizard_groups[line.wizard_id]:
                        wizard_groups[line.wizard_id][client_code] = []
                    wizard_groups[line.wizard_id][client_code].append(line)
        
        # Recalcular códigos para cada grupo
        for wizard, client_groups in wizard_groups.items():
            for client_code, client_lines in client_groups.items():
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
                
                # Ordenar por ID para mantener consistencia
                client_lines.sort(key=lambda x: x.id)
                
                # Asignar códigos secuenciales
                for i, line in enumerate(client_lines):
                    next_num = str(max_num + 1 + i).zfill(4)
                    new_code = f'{client_code}/{next_num}'
                    line.write({
                        'suggested_code': new_code,
                        'sample_code': new_code
                    })
        
        return lines