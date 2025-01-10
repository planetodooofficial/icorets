{
    'name': 'HR Attendance Late Field',
    'version': '1.0',
    'category': 'Human Resources',
    'description': 'Module to track late attendance for employees.',
    'depends': ['hr_attendance','base','hr_payroll', 'note',
        'hr_work_entry_contract_enterprise',
        'mail',
        'web_editor'],
    'data': [
        'views/hr_attendance_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
