# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
{
    'name': "Download Payslip from Portal",
    'version': '16.0.0.0',
    'category': "Website",
    'summary': "Print portal payslip report download website payslip portal pdf report employee payslip on portal employee payslips from website portal employee payslip portal employee payslips website portal employee print payslip report download payslip report ",
    'description': """
		
		Payslip Portal Odoo App helps users to view and manage payslips from portal websites for portal users. Portal users can search payslip by date from-to and batch on portal view, Apply different sort by option like newest, ascending order:month and descending order:month. Portal user can download payslip report in PDF format and also send message and attachments using payslip chatter on portal view.

    """,
    'author': 'BrowseInfo',
    "price": 49,
    "currency": 'EUR',
    'website': 'https://www.browseinfo.com',
    'depends': ['base', 'portal','hr_payroll','web','website'],
    'assets': {

        'web.assets_frontend': [
            'bi_payslip_portal/static/src/js/payslip_portal.js',
            'bi_payslip_portal/static/src/scss/payslip_portal.scss',
        ],
    },
    'data': [
        'security/ir.model.access.csv',
        'templates/payslip_portal_template.xml',
    ],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'live_test_url':'https://youtu.be/TSofWMrwT8c',
    "images":['static/description/Download-Payslip-Portal-Banner.gif'],
}
