# -*- coding: utf-8 -*-
##############################################################################
#
#    odoo, Open Source Management Solution
#    Copyright (C) 2018-BroadTech IT Solutions (<http://www.broadtech-innovations.com/>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
##############################################################################

from odoo import api, fields, tools, models, _
from odoo.exceptions import Warning
from odoo.exceptions import ValidationError
from odoo import tools
import string

class BtAsset(models.Model):   
    _name = "bt.asset"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Activo" 
    
    @api.multi
    def _get_default_location(self):
        obj = self.env['bt.asset.location'].search([('default','=',True)])
        if not obj:
            raise Warning(_("Por favor, cree primero la ubicación del activo"))
        loc = obj[0]
        return loc 
    
    name = fields.Char(string='Nombre', required=True)
    purchase_date = fields.Date(string='Fecha de Compra',track_visibility='always')
    purchase_value = fields.Float(string='Valor', track_visibility='always')
    asset_code = fields.Char(string='Codigo de activo')
    is_created = fields.Boolean('Creado', copy=False)
    current_loc_id = fields.Many2one('bt.asset.location', string="Ubicación actual", default=_get_default_location, required=True)
    model_name = fields.Char(string='Modelo')
    serial_no = fields.Char(string='Serial No', track_visibility='always')
    manufacturer = fields.Char(string='Fabricante')
    warranty_start = fields.Date(string='Inicio garantia')
    warranty_end = fields.Date(string='Fin garantia')
    category_id = fields.Many2one('bt.asset.category', string='Categoria')
    note = fields.Text(string='Notas Internas')
    state = fields.Selection([
            ('active', 'Active'),
            ('scrapped', 'Scrapped')], string='Estado',track_visibility='onchange', default='active', copy=False)
    image = fields.Binary("Imagen", attachment=True,
        help="Este campo contiene la imagen utilizada como imagen para el activo, limitada a 1024x1024px.")
    image_medium = fields.Binary("Medium-sized image", attachment=True,
        help="Imagen mediana del activo. Es automáticamente "\
              "redimensionado como una imagen de 128x128px, con relación de aspecto conservada," \
              "solo cuando la imagen excede uno de esos tamaños. Use este campo en las vistas de formulario o en algunas vistas kanban".)
    image_small = fields.Binary("Small-sized image", attachment=True,
        help="Imagen de pequeño tamaño del activo. Es automáticamente "\
              "redimensionado como una imagen de 64x64px, con la relación de aspecto conservada".
              "Utilice este campo en cualquier lugar donde se requiera una imagen pequeña".)
    
    @api.model
    def create(self, vals):
        tools.image_resize_images(vals)
        vals.update({'is_created':True})
        lot = super(BtAsset, self).create(vals)
        lot.message_post(body=_("Activo %s creado con el codigo %s .")% (lot.name,lot.asset_code))
        return lot      
    
    @api.multi
    def write(self, vals):
        tools.image_resize_images(vals)
        lot = super(BtAsset, self).write(vals)
        return lot
    
    @api.multi
    def action_move_vals(self):
        for asset in self:
            location_obj = self.env['bt.asset.location'].search([('default_scrap','=',True)])
            if not location_obj:
                raise Warning(_("Por favor, establezca la ubicación de chatarra primero"))
            move_vals = {
                'from_loc_id' : asset.current_loc_id.id,
                'asset_id' : asset.id,
                'to_loc_id' : location_obj.id
                }
            asset_move = self.env['bt.asset.move'].create(move_vals)
            asset_move.action_move()
            asset.current_loc_id = location_obj.id
            asset.state = 'scrapped'
            if asset.state == 'scrapped':
                asset.message_post(body=_("Scrapped"))
        return True    

class BtAssetLocation(models.Model):   
    _name = "bt.asset.location"
    _description = "Asset Location" 
    
    name = fields.Char(string='Name', required=True)
    asset_ids = fields.One2many('bt.asset','current_loc_id', string='Activos')
    default = fields.Boolean('Default', copy=False)
    default_scrap = fields.Boolean('Scrap')
    
    @api.model
    def create(self, vals):
        result = super(BtAssetLocation, self).create(vals)
        obj = self.env['bt.asset.location'].search([('default','=',True)])
        asset_obj = self.env['bt.asset.location'].search([('default_scrap','=',True)])
        if len(obj) > 1 or len(asset_obj) > 1:
            raise ValidationError(_("La ubicación predeterminada ya se ha establecido."))
        return result
    
    @api.multi
    def write(self, vals):
        res = super(BtAssetLocation, self).write(vals)
        obj = self.env['bt.asset.location'].search([('default','=',True)])
        asset_obj = self.env['bt.asset.location'].search([('default_scrap','=',True)])
        if len(obj) > 1 or len(asset_obj) > 1:
            raise ValidationError(_("La ubicación predeterminada ya se ha establecido."))
        return res
    
class BtAssetCategory(models.Model): 
    _name = "bt.asset.category"
    _description = "Asset Category"
    
    name = fields.Char(string='Nombre', required=True)  
    categ_no = fields.Char(string='Category No')
    
# vim:expandtab:smartindent:tabstop=2:softtabstop=2:shiftwidth=2:  