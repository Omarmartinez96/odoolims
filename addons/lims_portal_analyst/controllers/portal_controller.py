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

    def _get_analyst_parameters(self, filters=None):
        """Obtener parámetros con filtros - VERSIÓN AMPLIADA"""
        return request.env['lims.parameter.analysis.v2'].get_all_lab_parameters(filters)

    # ===============================================
    # === DASHBOARD BÁSICO ===
    # ===============================================
    @http.route('/my/lims', type='http', auth='user', website=True)
    def lims_dashboard_basic(self, **kwargs):
        """Dashboard mejorado con estadísticas globales"""
        access_check = self._check_portal_access()
        if access_check is not True:
            return access_check
        
        try:
            # Estadísticas globales del laboratorio
            stats = request.env['lims.parameter.analysis.v2'].get_lab_statistics()
            
            # Mis parámetros recientes
            my_params = self._get_analyst_parameters({'status_filter': 'my_assigned'})[:5]
            
            # Parámetros urgentes disponibles
            urgent_available = self._get_analyst_parameters({
                'status_filter': 'available', 
                'portal_priority': 'urgent'
            })[:3]
            
            values = {
                'page_name': 'lims_dashboard',
                'user_name': request.env.user.name,
                'stats': stats,
                'my_recent_parameters': my_params,
                'urgent_available': urgent_available,
            }
            
            return request.render('lims_portal_analyst.portal_dashboard_enhanced', values)
            
        except Exception as e:
            _logger.error(f"Error en dashboard mejorado: {str(e)}")
            values = {
                'error_message': 'Error al cargar el dashboard.',
                'page_name': 'lims_error'
            }
            return request.render('lims_portal_analyst.portal_error_basic', values)
            
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
    
    # ===============================================
    # === NUEVA RUTA: TOMAR PARÁMETRO ===
    # ===============================================
    @http.route('/my/lims/parameter/<int:param_id>/take', type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def lims_parameter_take(self, param_id, **post):
        """Tomar/asignar parámetro al analista actual"""
        access_check = self._check_portal_access()
        if access_check is not True:
            return access_check
        
        try:
            parameter = request.env['lims.parameter.analysis.v2'].browse(param_id)
            
            if not parameter.exists():
                return request.redirect('/my/lims/available?error=not_found')
            
            parameter.take_parameter()
            
            return request.redirect(f'/my/lims/parameter/{param_id}?taken=1')
            
        except UserError as e:
            return request.redirect(f'/my/lims/available?error={str(e)}')
        except Exception as e:
            _logger.error(f"Error tomando parámetro {param_id}: {str(e)}")
            return request.redirect('/my/lims/available?error=take_failed')

    # ===============================================
    # === NUEVA RUTA: LIBERAR PARÁMETRO ===
    # ===============================================
    @http.route('/my/lims/parameter/<int:param_id>/release', type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def lims_parameter_release(self, param_id, **post):
        """Liberar parámetro asignado"""
        access_check = self._check_portal_access()
        if access_check is not True:
            return access_check
        
        try:
            parameter = request.env['lims.parameter.analysis.v2'].browse(param_id)
            
            if not parameter.exists():
                return request.redirect('/my/lims/pending?error=not_found')
            
            parameter.release_parameter()
            
            return request.redirect('/my/lims/available?released=1')
            
        except UserError as e:
            return request.redirect(f'/my/lims/parameter/{param_id}?error={str(e)}')
        except Exception as e:
            _logger.error(f"Error liberando parámetro {param_id}: {str(e)}")
            return request.redirect(f'/my/lims/parameter/{param_id}?error=release_failed')

    # ===============================================
    # === NUEVA RUTA: PARÁMETROS DISPONIBLES ===
    # ===============================================
    @http.route('/my/lims/available', type='http', auth='user', website=True)
    def lims_available_parameters(self, page=1, sortby='date', search='', filterby='all', **kwargs):
        """Lista mejorada estilo backend con paginación y ordenamiento"""
        access_check = self._check_portal_access()
        if access_check is not True:
            return access_check
        
        try:
            # Configuración de paginación
            page = int(page)
            per_page = 20
            offset = (page - 1) * per_page
            
            # Opciones de ordenamiento
            sort_options = {
                'date': 'analysis_start_date desc, id desc',
                'name': 'name asc',
                'priority': 'portal_priority desc, name asc',
                'customer': 'analysis_id.customer_id, name asc',
                'status': 'analysis_status_checkbox, name asc'
            }
            order = sort_options.get(sortby, sort_options['date'])
            
            # Construcción de filtros
            domain = []
            
            # Filtro principal
            if filterby == 'available':
                domain.append(('analyst_assigned_id', '=', False))
            elif filterby == 'my_assigned':
                domain.append(('analyst_assigned_id', '=', request.env.user.id))
            elif filterby == 'urgent':
                domain.append(('portal_priority', '=', 'urgent'))
            elif filterby == 'completed':
                domain.append(('analysis_status_checkbox', '=', 'finalizado'))
            elif filterby == 'microbiological':
                domain.append(('category', '=', 'microbiological'))
            
            # Búsqueda de texto
            if search:
                domain.extend([
                    '|', '|', '|', 
                    ('name', 'ilike', search),
                    ('microorganism', 'ilike', search),
                    ('analysis_id.sample_code', 'ilike', search),
                    ('analysis_id.customer_id.name', 'ilike', search)
                ])
            
            # Obtener parámetros con paginación
            Parameter = request.env['lims.parameter.analysis.v2']
            total_count = Parameter.search_count(domain)
            parameters = Parameter.search(domain, order=order, limit=per_page, offset=offset)
            
            # Calcular paginación
            total_pages = (total_count + per_page - 1) // per_page
            
            # Obtener datos para filtros
            customers = request.env['res.partner'].search([('is_company', '=', True)], order='name')
            
            values = {
                'page_name': 'lims_parameters_advanced',
                'parameters': parameters,
                'customers': customers,
                'total_count': total_count,
                'page': page,
                'total_pages': total_pages,
                'per_page': per_page,
                'sortby': sortby,
                'search': search,
                'filterby': filterby,
                'has_previous': page > 1,
                'has_next': page < total_pages,
                'previous_page': page - 1 if page > 1 else 1,
                'next_page': page + 1 if page < total_pages else total_pages,
            }
            
            return request.render('lims_portal_analyst.portal_parameters_advanced_list', values)
            
        except Exception as e:
            _logger.error(f"Error en lista avanzada: {str(e)}")
            return request.redirect('/my/lims?error=list_error')