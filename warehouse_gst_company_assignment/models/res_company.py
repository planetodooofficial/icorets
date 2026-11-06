# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    gst_code_matching_com = fields.Char(
        string="GST Matching Code",
        index=True,
        copy=False,
        help="Unique GST matching code for branch assignment (e.g. DL, CH, HR, MH).",
    )

    @api.constrains("gst_code_matching_com", "parent_id")
    def _check_gst_code_matching_com_unique(self):
        for company in self:
            code = (company.gst_code_matching_com or "").strip().upper()
            if not code:
                continue

            # Determine root parent company for this hierarchy
            root = company.root_id if hasattr(company, "root_id") and company.root_id else False
            if not root:
                root = company
                while root.parent_id:
                    root = root.parent_id

            duplicates = self.search([
                ("gst_code_matching_com", "=ilike", code),
                ("id", "!=", company.id),
                ("id", "child_of", root.id),
            ])
            if duplicates:
                raise ValidationError(
                    _(
                        "GST matching code '%(code)s' is already assigned to branch '%(branch)s' "
                        "under parent company '%(parent)s'. Each branch under the same parent company "
                        "must have a unique GST matching code.",
                        code=code,
                        branch=duplicates[0].display_name,
                        parent=root.display_name,
                    )
                )
