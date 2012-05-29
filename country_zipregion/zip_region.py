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
from psycopg2 import DataError

class zip_region(osv.osv):
    _name = 'res.zip_region'
    _description = 'Zip Region'
    _columns = {
        'name': fields.char('Region Name', size=64, required=True),
        'country_id': fields.many2one('res.country', 'Country', required=True),
        'zip_csv': fields.char('Comma Separated Expression', size=256,
                    help="A list of ZIP code prefixes separated by commas. Letters will not be followed by another letter."\
                    "(Example 'CV,PE,S' will select all UK Postcodes beginning in CV, PE, S but not SW"),
        'regex_match': fields.boolean('Manual Regular Expression'),
        # The regex matching works best with NO index on the address zip field, starting with a ^ clamp, but NOT ending with a $ clamp
        'zip_regex': fields.char('Zip Regular Expression', size=1024,
                    help="A PostgreSQL Regular Expression (POSIX) to select ZIP codes. Leave blank to select all."\
                    "(Example '^CV[[:digit:]]{1,2}[[:blank:]]*[[:digit:]][[:alpha:]]{2}' will select all UK Postcodes for the Coventry region"),
        }
    _order = 'name'
    
    _defaults = {
        'regex_match' : lambda *a: False,
    }
    
    def _zip_regex_from_csv(self, csv):
        if not csv or not csv.strip():
            return ""
        else:
            reg_exp_vals = []
            vals = csv.strip().split(',')
            for v in vals:
                if len(v.strip()) == 0:
                    continue
                v = "^%s" % (v.strip(),)
                if v[-1].isalpha():
                    v = "%s[^[:alpha:]]" % (v,)
                reg_exp_vals.append(v)
            if len(reg_exp_vals) == 0:
                return ""
            elif len(reg_exp_vals) == 1:
                return reg_exp_vals[0]
            else:
                return "(%s)" % ("|".join(reg_exp_vals),)

    def onchange_zip_csv(self, cr, uid, ids, zip_csv, regex_match):
        if regex_match == False:
            return {'value': {'zip_regex': self._zip_regex_from_csv(zip_csv)}}
    
    def onchange_zip_regex(self, cr, uid, ids, zip_regex):
        return {'value': {'regex_match': False}}
    
    def _validate_reg_ex(self, cr, uid, ids, vals, context):
        if 'zip_regex' in vals:
            try:
                cr.execute("""select 1 where 'abc' ~ %s""", (vals['zip_regex'] or '',))
                cr.fetchall()
            except DataError, e:
                raise osv.except_osv("Error", "Invalid characters in Comma Separated Expression or Invalid PostgreSQL Regular Expression\n%s: %s" % (e.pgcode, e.pgerror,))
    
    def write(self, cr, uid, ids, vals, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids,]
        if 'zip_csv' in vals and 'regex_match' in vals and vals['regex_match'] == False:
            vals['zip_regex'] = self._zip_regex_from_csv(vals['zip_csv'])
        elif ('zip_csv' in vals) ^ ('regex_match' in vals):
            zr = self.browse(cr, uid, ids, context=context)[0]
            if ('regex_match' in vals and vals['regex_match'] == False) or ('regex_match' not in vals and zr.regex_match == False):
                vals['zip_regex'] = self._zip_regex_from_csv('zip_csv' in vals and vals['zip_csv'] or zr.zip_csv)
        self._validate_reg_ex(cr, uid, ids, vals, context)
        return super(zip_region, self).write(cr, uid, ids, vals, context)
    
    def create(self, cr, uid, vals, context=None):
        if vals.get('regex_match', False) == False:
            vals['zip_regex'] = self._zip_regex_from_csv(vals.get('zip_csv', ''))
        self._validate_reg_ex(cr, uid, None, vals, context)
        return super(zip_region, self).create(cr, uid, vals, context)


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
