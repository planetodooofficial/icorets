# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'PO Stock Reports v15',
    'version': '16.0.0.1',
    'summary': 'Stock Reports',
    'sequence': 10,
    'description': """ """,
    'category': '',
    'website': 'https://www.planet-odoo.com',
    'depends': ["stock"],
    'data': [
        'security/ir.model.access.csv',
        'wizards/stock.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
