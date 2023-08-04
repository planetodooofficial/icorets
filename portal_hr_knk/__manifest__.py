# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

{
    'name': 'Portal HR',
    'version': '16.0.1.0',
    'summary': 'This Module allows users to make employees as portal user and provides all portal features to employees',
    'description': """Portal HR
=================
=> Make Employee Portal User
=> Allow all portal features""",
    'license': 'OPL-1',
    'author': 'Kanak Infosystems LLP.',
    'website': 'https://www.kanakinfosystems.com',
    'category': 'Hidden',
    'depends': ['base', 'website', 'hr', 'portal'],
    'data': [
        'security/ir.model.access.csv',
        'security/hr_security.xml',
        'views/knk_res_config_view.xml',
    ],
    'images': ['static/description/Banner.png'],
    'installable': True,
}
