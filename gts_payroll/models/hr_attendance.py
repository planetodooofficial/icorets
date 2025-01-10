from odoo import models, fields, api, Command
from datetime import time
from odoo.exceptions import UserError





class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    is_late = fields.Boolean(string="Late", compute="_compute_is_late",)

    @api.depends('check_in', 'employee_id')

    def _compute_is_late(self):
        working_schedule = self.employee_id.resource_calendar_id
        monday_attendance = working_schedule.attendance_ids.filtered(lambda att: att.dayofweek == '1')
        monday_start_hour = min(monday_attendance.mapped('hour_from'))

        for record in self:
            if record.check_in:
                # Convert check_in to the local time zone of the user
                local_checkin_time = fields.Datetime.context_timestamp(record, record.check_in)

                # Extract the time part for comparison
                checkin_time = local_checkin_time.time()
                fixed_checkin_time =  monday_start_hour  #time(8, 0, 0)  # 8:00 AM

                # Compare the times
                def float_to_time(float_value):
                    # Split the float into hours and minutes
                    hours = int(float_value)  # Integer part represents hours
                    minutes = int((float_value - hours) * 60)  # Fractional part represents minutes
                    return time(hours, minutes)

                converted_time = float_to_time(fixed_checkin_time)

                record.is_late = checkin_time > converted_time
            else:
                record.is_late = False








