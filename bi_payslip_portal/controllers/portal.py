# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields
from odoo import http, _
from odoo.http import request, content_disposition
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.osv.expression import OR, AND
from odoo.exceptions import AccessError, MissingError
from datetime import datetime


class PayslipPortal(CustomerPortal):

    def get_domain_my_payslip(self, user):
        return [
            ('employee_id', '=', user.employee_id.id)
        ]

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        user  = request.env.user
        if 'payslip_count' in counters:
            values['payslip_count'] = request.env['hr.payslip'].search_count(self.get_domain_my_payslip(request.env.user))
        return values

    def _payslip_get_page_view_values(self, payslip, access_token, **kwargs):
        values = {
            'page_name': 'payslips',
            'payslip': payslip,
        }
        return self._get_page_view_values(payslip, access_token, values, 'my_payslip_history', False, **kwargs)

    @http.route(['/my/payslips', '/my/payslips/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_payslips(self, page=1, date_begin=None, date_end=None, sortby=None, search=None, search_in='batch', **kw):
        values = self._prepare_portal_layout_values()
        HrPayslip = request.env['hr.payslip']
        domain = self.get_domain_my_payslip(request.env.user)

        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'asc': {'label': _('Ascending Order:Month'), 'order': 'batch_name asc'},
            'desc': {'label': _('Descending Order:Month'), 'order': 'batch_name desc'},
        }

        searchbar_inputs = {
            'from_to': {'input': 'from_to', 'label': _('Search In Date From - To')},
            'batch': {'input': 'batch', 'label': _('Search in Batch')},
        }

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        
        # search
        if search and search_in:
            search_domain = []
            if search_in in ('from_to'):
                search_data = search.split('-')
                if search_data:
                    start_date = search_data[0] if search_data[0] else False
                    end_date = search_data[1] if search_data[1] else False
                    date_from = datetime.strptime(start_date, '%m/%d/%Y')
                    date_to = datetime.strptime(end_date, '%m/%d/%Y')
                    search_domain = OR([search_domain, [('date_from', '>=', date_from), ('date_to', '<=', date_to)]])
            if search_in in ('batch'):
                search_domain = OR([search_domain, [('payslip_run_id.name', 'ilike', search)]])
            domain = AND([domain, search_domain])   

        # pager
        payslip_count = HrPayslip.search_count(domain)
        pager = portal_pager(
            url='/my/payslips',
            url_args={'date_begin': date_begin, 'date_end': date_end, 'search_in': search_in, 'sortby': sortby, 'search': search},
            total=payslip_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        payslips = HrPayslip.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
       
        values.update({
            'date': date_begin,
            'payslips': payslips,
            'page_name': 'payslips',
            'default_url': '/my/payslips',
            'pager': pager,
            'searchbar_inputs': searchbar_inputs,
            'searchbar_sortings' : searchbar_sortings,
            'search_in': search_in,
            'sortby': sortby,
        })
        return request.render("bi_payslip_portal.portal_my_payslips", values)


    @http.route([
        "/payslip/<int:payslip_id>",
        "/payslip/<int:payslip_id>/<access_token>",
        '/my/payslip/<int:payslip_id>',
        '/my/payslip/<int:payslip_id>/<access_token>'
    ], type='http', auth="public", website=True)
    def payslip_followup(self, payslip_id=None, access_token=None, **kw):
        try:
            payslip_sudo = self._document_check_access('hr.payslip', payslip_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = self._payslip_get_page_view_values(payslip_sudo, access_token, **kw)
        return request.render("bi_payslip_portal.payslip_followup", values)


    @http.route('/payslip/report/<int:payslip_id>', type='http', auth='user')
    def download_qweb_report(self, payslip_id=None, access_token=None, **kw):
        try:
            payslip_sudo = self._document_check_access('hr.payslip', payslip_id, access_token)
        except (AccessError, MissingError): 
            return request.redirect('/my')
        pdf = request.env["ir.actions.report"]._render_qweb_pdf('hr_payroll.action_report_payslip', payslip_sudo.id)[0]
        report_name = payslip_sudo.name +'.pdf'
        return request.make_response(pdf, headers=[('Content-Type', 'application/pdf'),('Content-Disposition', content_disposition(report_name))])