from odoo import models, fields, api, Command
from datetime import time
from odoo.exceptions import UserError





class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    is_late = fields.Boolean(string="Late", compute="_compute_is_late", store=True)

    @api.depends('check_in', 'employee_id', 'employee_id.resource_calendar_id')
    def _compute_is_late(self):
        def float_to_time(float_value):
            hours = int(float_value)
            minutes = int((float_value - hours) * 60)
            return time(hours, minutes)

        for record in self:
            if record.check_in and record.employee_id:
                working_schedule = record.employee_id.resource_calendar_id
                monday_attendance = working_schedule.attendance_ids.filtered(lambda att: att.dayofweek == '1') if working_schedule else False
                hours_from = monday_attendance.mapped('hour_from') if monday_attendance else []
                fixed_checkin_hour = min(hours_from) if hours_from else 8.0

                local_checkin_time = fields.Datetime.context_timestamp(record, record.check_in)
                checkin_time = local_checkin_time.time()
                converted_time = float_to_time(fixed_checkin_hour)

                record.is_late = checkin_time > converted_time
            else:
                record.is_late = False









