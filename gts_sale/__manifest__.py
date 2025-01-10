
{
    'name': 'GTS Sale',
    'version': '16.0',
    'summary': 'GTS Sales',
    'description': 'Partner Ledger Report',
    'author': 'Geotechnosoft',
    'maintainer': 'Geotechnosoft',
    'company': 'Geotechnosoft',
    'website': 'https://planet-odoo.com/',
    'depends': ['base', 'account_reports', 'account', 'po_accounting_v16', 'register_reports_v16'],
    'category': 'Accounting',
    'demo': [],
    'data': [
            'views/sale_order_view.xml',
            'report/sale_report_inherit_views.xml',
             ],
    'installable': True,
    'images': [],
    'qweb': [],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
}
