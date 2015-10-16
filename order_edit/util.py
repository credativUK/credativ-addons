# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 credativ Ltd (<http://credativ.co.uk>).
#    All Rights Reserved
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

import datetime
import logging
import sys

def get_id(cr, uid, pool, id_str):
    mod, id_str = id_str.split('.')
    result = pool.get('ir.model.data')._get_id(cr, uid, mod, id_str)
    return int(pool.get('ir.model.data').read(cr, uid, [result], ['res_id'])[0]['res_id'])

def get_date(s):
    return datetime.datetime.strptime(s, "%Y-%m-%d").date()

def log(self, msg, level=logging.INFO):
    logger = logging.getLogger(self._name)
    logger.log(level, "%s(): %s", sys._getframe(1).f_code.co_name, msg)
