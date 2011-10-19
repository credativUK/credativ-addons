# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution   
#    Copyright (C) 2011 credativ Ltd (<http://credativ.co.uk>).
#    All Rights Reserved
#    $Id$
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

import wizard
import netsvc
import pooler

import time
from osv import osv
from tools.translate import _

create_dispatch_form = '''<?xml version="1.0"?>
<form string="Create Dispatch">
  <field name="carrier_id"/>
  <newline/>
  <field name="dispatch_date"/>
</form>
'''
fields = {
        'carrier_id': {
            'string': 'Carrier',
            'type': 'many2one',
            'relation': 'res.partner',
            'required': True,
        },
        'dispatch_date': {
            'string': 'Planned Dispatch Date',
            'type': 'date',
            'default': time.strftime('%Y-%m-%d'),
            'required': True,
        }
}

def _check_moves(self, cr, uid, data, context):
    pool = pooler.get_pool(cr.dbname)
    move_string = ''
    error = False

    for move in pool.get('stock.move').browse(cr, uid, data['ids']):
        if move.dispatch_id and move.dispatch_id.id != id:
            error = True
            move_string += ' (id:%d,dispatch_id:%d)' % (move.id, move.dispatch_id.id)

    if error:
        raise wizard.except_wizard(_('UserError'), _('One or more moves are already part of another dispatch and' \
                             ' can not been added to a new one:%s' % (move_string)))

    return data['form']

def _create_dispatch(self, cr, uid, data, context):
    pool = pooler.get_pool(cr.dbname)

    dispatch_data = {
                    'carrier_id': data['form']['carrier_id'],
                    'dispatch_date': data['form']['dispatch_date'],
                    'stock_moves': ([6, 0, data['ids']],),
            }

    dispatch = pool.get('stock.dispatch').create(cr, uid, dispatch_data)

    return {
            'name': 'Dispatch',
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'stock.dispatch',
            'view_id': False,
            'res_id': dispatch,
            'type': 'ir.actions.act_window',
        }

class wizard_create_dispatch(wizard.interface):
    states = {
        'init': {
            'actions': [_check_moves],
            'result': {'type': 'form', 'arch': create_dispatch_form, 'fields': fields, 'state': [('end', 'Cancel', 'gtk-cancel'), ('create_dispatch', 'Ok', 'gtk-ok')]},
            },
        'create_dispatch': {
            'actions': [],
            'result': {'type':'action', 'action': _create_dispatch, 'state':'end'}
        }
    }

wizard_create_dispatch('stock.move.create_dispatch')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

