# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2013 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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

class deferred_action_notification(osv.osv_memory):
    '''
    This class implements a wizard used to display notifications at
    the start of deferred actions.
    '''
    _name = 'deferred.action.notification'

    _columns = {
        'title': fields.char(
            'Title',
            size=255,
            readonly=True),
        'message': fields.text(
            'Message',
            readonly=True),
    }

    def ok_button(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}

deferred_action_notification()
