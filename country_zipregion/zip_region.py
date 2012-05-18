# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 credativ Ltd (<http://credativ.co.uk>).
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv, fields

class zip_region(osv.osv):
    _name = 'res.zip_region'
    _description = 'Zip Region'
    _columns = {
        'name': fields.char('Region Name', size=64, required=True),
        'country_id': fields.many2one('res.country', 'Country', required=True),
        # The regex matching works best with NO index on the address zip field, starting with a ^ clamp, but NOT ending with a $ clamp
        'zip_regex': fields.char('Zip Regular Expression', size=1024,
                    help="A PostgreSQL Regular Expression (POSIX) to select ZIP codes. Leave blank to select all."\
                    "(Example '^CV[[:digit:]]{1,2}[[:blank:]]*[[:digit:]][[:alpha:]]{2}' will select all UK Postcodes for the Coventry region"),
        }
    _order = 'name'

zip_region()

class zip_region_group(osv.osv):
    _name = 'res.zip_region_group'
    _description = 'Zip Region Group'
    _columns = {
        'name': fields.char('Region Group Name', size=64, required=True),
        'region_ids': fields.many2many('res.zip_region', 'res_zip_region_rel', 'region_group_id', 'region_id', 'Zip Regions'),
        }
    _order = 'name'

zip_region_group()

# Both sides of a many2many field must exist before it can be created
class zip_region_2(osv.osv):
    _inherit = 'res.zip_region'
    _columns = {
        'group_ids': fields.many2many('res.zip_region_group', 'res_zip_region_rel', 'region_id', 'region_group_id', 'Zip Region Groups'),
        }

zip_region_2()
