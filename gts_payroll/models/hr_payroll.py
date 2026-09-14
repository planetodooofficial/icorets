from odoo import models, fields, api, Command
from datetime import time
from odoo.exceptions import UserError


#
class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def _calculate_half_day_salary(self, employee):
        contract = employee.contract_id
        wage_per_month = contract.wage

        working_days_per_month = contract.total_wage_in_days or 30  # Default to 30 days if not set
        if working_days_per_month == 0:
            raise UserError("Working days per month cannot be zero.")

        wage_per_day = wage_per_month / working_days_per_month
        half_day_salary = wage_per_day / 2

        return half_day_salary

    @api.model
    def count_late_days(self, date_from, date_to):
        # Convert date_from and date_to to datetime if they're not already
        if isinstance(date_from, str):
            date_from = fields.Datetime.from_string(date_from)
        if isinstance(date_to, str):
            date_to = fields.Datetime.from_string(date_to)

        # Search for attendances within the specified date range
        attendances = self.env['hr.attendance'].search([
            ('employee_id', '=', self.employee_id.id),
            ('check_in', '>=', date_from),
            ('check_in', '<=', date_to),
        ])

        late_count = 0
        for attendance in attendances:
            # Check if the attendance record is marked as late
            if attendance.is_late:
                late_count += 1

        return late_count
        #         working_schedule = self.employee_id.resource_calendar_id
        # Compare check_in time with the fixed 8:00 AM time
        # local_checkin_time = fields.Datetime.context_timestamp(attendance, attendance.check_in)
        # checkin_time = local_checkin_time.time()
        # monday_start_hour = getattr(working_schedule, 'monday_morning', resource_calendar_id.hour_from)  # Default to 8 if not set
        # fixed_checkin_time = time(8, 0, 0)  # 8:00 AM
        #
        # # Count as late if check-in time is after 8:00 AM
        # if checkin_time > fixed_checkin_time:
        #     late_count += 1

    # @api.depends('employee_id', 'contract_id', 'struct_id', 'date_from', 'date_to')
    # def _compute_input_line_ids(self):
    #     # Call the super method to ensure other necessary computations are done
    #     res = super(HrPayslip, self)._compute_input_line_ids()
    #
    #     # Calculate late days
    #     late_count = self.count_late_days(self.date_from, self.date_to)  # Correct the repeated line
    #
    #     # Calculate half day salary
    #     half_day_salary = self._calculate_half_day_salary(self.employee_id)
    #
    #     # Set the deduction amount based on the number of late days
    #     if late_count >= 18:
    #         deduction_amount = 6 * half_day_salary
    #     elif late_count >= 15:
    #         deduction_amount = 5 * half_day_salary
    #     elif late_count >= 12:
    #         deduction_amount = 4 * half_day_salary
    #     elif late_count >= 9:
    #         deduction_amount = 3 * half_day_salary  # Deduct 3 half-day salaries
    #     elif late_count >= 6:
    #         deduction_amount = 2 * half_day_salary  # Deduct 2 half-day salaries
    #     elif late_count >= 3:
    #         deduction_amount = half_day_salary  # Deduct 1 half-day salary
    #     else:
    #         deduction_amount = 0 # No deduction
    #
    #
    #     # Update the input_line_ids with the late arrival deduction
    #
    #     if self.employee_id:
    #         if self.input_line_ids:
    #             self.input_line_ids = [(5, 0, 0)]
    #         self.write({
    #             'input_line_ids': [
    #                 (0, 0, {
    #                     'input_type_id': 1,  # Use the correct input type ID
    #                     'name': 'Late Arrival Deduction',
    #                     'amount': deduction_amount
    #                 })
    #             ]
    #         })
    #
    #     return res

    # def _compute_input_line_ids(self):
    #     res = super(HrPayslip, self)._compute_input_line_ids()
    #     input_line_vals.append(Command.create({
    #             'input_line_ids.name': "Late Deduction",
    #             'input_line_ids.input_type_id': 'Deduction',
    #             # 'amount' :
    #     }))
    #     slip.update({'input_line_ids': input_line_vals})
    #     # res.append((0, 0, input_line_vals))
    #     return res


class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'

    late_salary_amount = fields.Float(string="Late Salary Amount", compute="_compute_late_salary_amount")


    @api.depends('payslip_id', 'code')
    def _compute_late_salary_amount(self):
        for line in self:
            half_day_salary = line.payslip_id._calculate_half_day_salary(line.payslip_id.employee_id)
            late_count = line.number_of_days
            deduction_amount = 0
            if line.code == 'LATEATT':
                if late_count >= 18:
                    deduction_amount = 6 * half_day_salary
                elif late_count >= 15:
                    deduction_amount = 5 * half_day_salary
                elif late_count >= 12:
                    deduction_amount = 4 * half_day_salary
                elif late_count >= 9:
                    deduction_amount = 3 * half_day_salary  # Deduct 3 half-day salaries
                elif late_count >= 6:
                    deduction_amount = 2 * half_day_salary  # Deduct 2 half-day salaries
                elif late_count >= 3:
                    deduction_amount = half_day_salary  # Deduct 1 half-day salary
                else:
                    deduction_amount = 0 # No deduction
                line.late_salary_amount = deduction_amount
            else:
                line.late_salary_amount = deduction_amount

