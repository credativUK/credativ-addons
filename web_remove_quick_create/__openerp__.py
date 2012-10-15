# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 credativ Ltd (<http://credativ.co.uk>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name": "Remove 'Create' and 'Create and Edit' Links",
    "description":
        """
        OpenERP Web module which removes options 'Create' and 'Create and Edit' from suggested results dropdown list on many2one fields.
        """,
    "version": "1.0",
    "author" : "credativ Ltd",
    "website" : "http://credativ.co.uk",
    "category" : "Tools",
    "depends" : ["web"],
    "js": [
        "static/src/js/view_form.js",
    ],
    "auto_install": False,
}
