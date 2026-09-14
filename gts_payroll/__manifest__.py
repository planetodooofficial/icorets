{
    'name': 'HR Attendance Late Field',
    'version': '19.0.1.0.0',
    'category': 'Human Resources',
    'description': 'Module to track late attendance for employees.',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'hr_attendance',
        'hr_payroll',
        'mail',
    ],
    'data': [
        'views/hr_attendance_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}

