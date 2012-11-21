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
    "name": "Chrome Save On blur",
    "description":
        """
        OpenERP Web module which makes chrome call an onchange upon window
        losing focus as opposed to calling onchange after window has regained
        focus. This is to prevent data being lost.
        """,
    "version": "1.0",
    "author" : "credativ Ltd",
    "website" : "http://credativ.co.uk",
    "category" : "Tools",
    "depends" : ["web"],
    "js": [
        "static/src/js/save_on_blur_chrome.js",
    ],
    "auto_install": False,
}
