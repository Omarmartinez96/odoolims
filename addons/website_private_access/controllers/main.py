from odoo import http
from odoo.http import request

class WebsitePrivateAccess(http.Controller):

    @http.route('/', type='http', auth="user", website=True)
    def redirect_home(self, **kwargs):
        return request.render("website.homepage")

    @http.route(['/page/<path:page>'], type='http', auth="user", website=True)
    def redirect_pages(self, page, **kwargs):
        return request.render(f"website.{page}")
