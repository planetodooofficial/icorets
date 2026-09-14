# -*- coding: utf-8 -*-
{
    'name': 'GTS E-Invoice & E-Waybill',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Multi-Unit E-Invoice and E-Waybill Fields & Models',
    'description': """
GTS E-Invoice and E-Waybill Module
==================================
This module defines the models and fields required for multi-unit E-Invoice and E-Waybill integration.
    """,
    'author': 'Geotechnosoft',
    'website': 'https://geotechnosoft.com',
    'depends': ['base', 'account', 'stock', 'l10n_in'],
    'data': [
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
