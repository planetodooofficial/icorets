from odoo import models, fields, api, _


class InheritApprovalRequest(models.Model):
    _inherit = "approval.request"

    cust_partner_id = fields.Many2one("res.partner")
    vendor_count = fields.Integer("Vendor Count")

    def action_show_contact(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'res_id': self.cust_partner_id.id,
            'name': self.cust_partner_id.name,
            'view_mode': 'form',
            'views': [(False, "form")],
        }

    def action_approve(self, approver=None):
        if self.cust_partner_id:
            self._ensure_can_approve()
            if not isinstance(approver, models.BaseModel):
                approver = self.mapped('approver_ids').filtered(
                    lambda approver: approver.user_id == self.env.user
                )
            approver.write({'status': 'approved'})
            self.sudo()._update_next_approvers('pending', approver, only_next_approver=True)
            self.sudo()._get_user_approval_activities(user=self.env.user).action_feedback()
            self.cust_partner_id.write({'active': True})
