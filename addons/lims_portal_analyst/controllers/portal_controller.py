from odoo import http, fields, _
from odoo.http import request
from odoo.exceptions import UserError, AccessError
from odoo.addons.portal.controllers.portal import CustomerPortal
import logging

_logger = logging.getLogger(__name__)

class LimsPortalBasicController(CustomerPortal):
    
    def _check_portal_access(self):
        """Verificación básica de acceso portal"""
        if not request.env.user.has_group('lims_portal_analyst.group_portal_analyst'):
            _logger.warning(f"Acceso denegado a portal LIMS para usuario {request.env.user.login}")
            return request.redirect('/my')
        return True

    def _get_analyst_parameters(self, status_filter=None):
        """Obtener parámetros del analista - VERSIÓN BÁSICA"""
        domain = [('analyst_assigned_id', '=', request.env.user.id)]
        
        if status_filter:
            domain.append(('portal_status', '=', status_filter))
        
        return request.env['lims.parameter.analysis.v2'].search(
            domain, order='portal_priority desc, assignment_date asc'
        )

    # ===============================================
    # === DASHBOARD BÁSICO ===
    # ===============================================
    @http.route('/my/lims', type='http', auth='user', website=True)
    def lims_dashboard_basic(self, **kwargs):
        """Dashboard básico del analista portal"""
        access_check = self._check_portal_access()
        if access_check is not True:
            return access_check
        
        try:
            # Estadísticas básicas
            all_params = self._get_analyst_parameters()
            pending_params = self._get_analyst_parameters('assigned')
            in_progress_params = self._get_analyst_parameters('in_progress')
            completed_params = self._get_analyst_parameters('completed')
            
            # Últimos 5 parámetros
            recent_params = all_params[:5]
            
            values = {
                'page_name': 'lims_dashboard',
                'user_name': request.env.user.name,
                'total_assigned': len(all_params),
                'pending_count': len(pending_params),
                'in_progress_count': len(in_progress_params),
                'completed_count': len(completed_params),
                'recent_parameters': recent_params,
            }
            
            return request.render('lims_portal_analyst.portal_dashboard_basic', values)
            
        except Exception as e:
            _logger.error(f"Error en dashboard básico: {str(e)}")
            values = {
                'error_message': 'Error al cargar el dashboard.',
                'page_name': 'lims_error'
            }
            return request.render('lims_portal_analyst.portal_error_basic', values)

    # ===============================================
    # === LISTA BÁSICA DE PARÁMETROS ===
    # ===============================================
    @http.route('/my/lims/pending', type='http', auth='user', website=True)
    def lims_pending_basic(self, status='assigned', **kwargs):
        """Lista básica de parámetros"""
        access_check = self._check_portal_access()
        if access_check is not True:
            return access_check
        
        try:
            parameters = self._get_analyst_parameters(status_filter=status)
            
            values = {
                'page_name': 'lims_pending',
                'parameters': parameters,
                'current_status': status,
                'total_count': len(parameters),
            }
            
            return request.render('lims_portal_analyst.portal_parameter_list_basic', values)
            
        except Exception as e:
            _logger.error(f"Error en lista básica: {str(e)}")
            return request.redirect('/my/lims?error=list_error')

    # ===============================================
    # === FORMULARIO BÁSICO DE PARÁMETRO ===
    # ===============================================
    @http.route('/my/lims/parameter/<int:param_id>', type='http', auth='user', website=True)
    def lims_parameter_form_basic(self, param_id, **kwargs):
        """Formulario básico de parámetro"""
        access_check = self._check_portal_access()
        if access_check is not True:
            return access_check
        
        try:
            parameter = request.env['lims.parameter.analysis.v2'].browse(param_id)
            
            # Verificar que existe y pertenece al analista
            if not parameter.exists():
                return request.redirect('/my/lims/pending?error=not_found')
            
            if parameter.analyst_assigned_id.id != request.env.user.id:
                return request.redirect('/my/lims/pending?error=access_denied')
            
            values = {
                'page_name': 'lims_parameter_form',
                'parameter': parameter,
                'analysis': parameter.analysis_id,
                'can_edit': True,  # Básico: siempre se puede editar
            }
            
            return request.render('lims_portal_analyst.portal_parameter_form_basic', values)
            
        except Exception as e:
            _logger.error(f"Error en formulario básico {param_id}: {str(e)}")
            return request.redirect('/my/lims/pending?error=form_error')

    # ===============================================
    # === GUARDAR PARÁMETRO BÁSICO ===
    # ===============================================
    @http.route('/my/lims/parameter/<int:param_id>/save', type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def lims_parameter_save_basic(self, param_id, **post):
        """Guardar cambios básicos en parámetro"""
        access_check = self._check_portal_access()
        if access_check is not True:
            return access_check
        
        try:
            parameter = request.env['lims.parameter.analysis.v2'].browse(param_id)
            
            # Verificaciones básicas
            if not parameter.exists():
                return request.redirect('/my/lims/pending?error=not_found')
            
            if parameter.analyst_assigned_id.id != request.env.user.id:
                return request.redirect('/my/lims/pending?error=access_denied')
            
            # Actualizar campos básicos
            update_vals = {}
            
            if 'result_value' in post:
                update_vals['result_value'] = post['result_value']
                # Si hay resultado, marcar como en proceso
                if post['result_value'].strip():
                    update_vals['portal_status'] = 'in_progress'
            
            if 'portal_notes' in post:
                update_vals['portal_notes'] = post['portal_notes']
            
            if 'portal_priority' in post:
                update_vals['portal_priority'] = post['portal_priority']
            
            # Realizar actualización
            parameter.write(update_vals)
            
            _logger.info(f"Parámetro {param_id} actualizado por {request.env.user.login}")
            
            # Redirección básica
            action = post.get('action', 'stay')
            
            if action == 'complete':
                try:
                    parameter.mark_completed()
                    return request.redirect('/my/lims?completed=1')
                except UserError as e:
                    return request.redirect(f'/my/lims/parameter/{param_id}?error={str(e)}')
            else:
                return request.redirect(f'/my/lims/parameter/{param_id}?saved=1')
                
        except Exception as e:
            _logger.error(f"Error guardando básico {param_id}: {str(e)}")
            return request.redirect(f'/my/lims/parameter/{param_id}?error=save_failed')

    # ===============================================
    # === PÁGINA DE ERROR BÁSICA ===
    # ===============================================
    @http.route('/my/lims/error', type='http', auth='user', website=True)
    def lims_error_basic(self, error_type='general', **kwargs):
        """Página de error básica"""
        error_messages = {
            'access_denied': 'No tienes permisos para acceder.',
            'not_found': 'Parámetro no encontrado.',
            'save_error': 'Error al guardar.',
            'general': 'Ha ocurrido un error.'
        }
        
        values = {
            'page_name': 'lims_error',
            'error_message': error_messages.get(error_type, error_messages['general'])
        }
        
        return request.render('lims_portal_analyst.portal_error_basic', values)