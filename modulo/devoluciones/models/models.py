# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, date, timedelta
class Devoluciones(models.Model):
	_name = 'model.devo'

	referencia = fields.Char(string="Numero", readonly=True, copy=False)
	state = fields.Selection([('draft', 'Borrador'),('approve','Aprovado'),('done','Heho'),('reject','Rechazado')], default="draft")
	tipo_usuario = fields.Selection([('cliente', 'Cliente'),('proveedor', 'Proveedor')], string="Tipo de usuario")
	serie = fields.Char(string="Serie del producto")
	nombre_responsable = fields.Many2one('res.partner', string="Nombre del responsable")
	numero_responsable = fields.Char(string="Numero del resposable")
	estado_procedencia = fields.Many2one('res.country.state', string="Estado de procedencia")
	ciudad_procedencia = fields.Char(string="Ciudad de procedencia")
	codigo_postal = fields.Char(string="Codigo Postal")
	fecha_devolucion = fields.Date(string="Fecha de devolucion", default=fields.Date.today())
	nombre_cancelo = fields.Many2one('res.user', string="Cancelo")
	lineas = fields.Integer(string="Lineas", default=0, compute="_get_lines")
	salida = fields.Char(string="Salida")
	num_aprovados = fields.Integer(string="Productos aprovados", compute="_get_result")
	num_rechazados = fields.Integer(string="Productos rechazados", compute="_get_result")
	total_productos = fields.Integer(string="Total productos escaneados", compute="_get_result")
	tabla_devo = fields.One2many('tabla.devo', 'devolucion_id')

	@api.depends('tabla_devo')
	def _get_result(self):
		if self.tabla_devo:
			numero_a = 0
			numero_r = 0
			total = 0
			for num in self.tabla_devo:
				total += 1
				self.total_productos = total
				if num.estatus == 'Aprovado':
					numero_a += 1
					self.num_aprovados = numero_a
				if num.estatus == 'Rechazado por tiempo':
					numero_r += 1
					self.num_rechazados = numero_r 	

	@api.depends('tabla_devo')
	def _get_lines(self):
		for record in self:
			if record.tabla_devo:
				self.lineas = 1

	@api.model
	def create(self, vals):
		if vals.get('referencia', 'New') == 'New':
			vals['referencia'] = self.env['ir.sequence'].next_by_code('model.devo') or 'New'
			result = super(Devoluciones, self).create(vals)
		return result	

	@api.one
	def buscar(self):
		if self.tipo_usuario == 'cliente':
			serie_pro_venta = self.env['stock.move.line'].search([('lot_id', '=', self.serie),('reference', 'like', 'WH/OUT')], limit=1)
			if serie_pro_venta:
				stock_venta = self.env['stock.picking'].search([('name', '=', serie_pro_venta.reference)], limit=1)
				if stock_venta:
					self.nombre_responsable = stock_venta.partner_id.id
					self.estado_procedencia = stock_venta.partner_id.state_id.id
					self.ciudad_procedencia = stock_venta.partner_id.city
					self.codigo_postal = stock_venta.partner_id.zip

					venta = self.env['sale.order'].search([('name','=', stock_venta.origin)], limit=1)
					if venta:
						if venta.partner_id.id == self.nombre_responsable.id:
							if stock_venta.picking_type_code == 'outgoing':
								igual = 0
								for record in self.tabla_devo:
									if record.serie == serie_pro_venta.lot_id:
										igual +=1
									else:
										igual = 0	
								if igual == 0:
									status = ''
									if venta.plazo_devo > self.fecha_devolucion:
										status = 'Aprovado'
									else:
										status = 'Rechazado por tiempo'			
									registro_devo = self.env['tabla.devo']
									for pri in venta:
										price = self.env['sale.order.line'].search([('product_id', '=', serie_pro_venta.product_id.id)], limit=1)
										registro_devo_value = {
											'producto': serie_pro_venta.product_id.id,
											'serie': serie_pro_venta.lot_id.id,
											'pedido': stock_venta.origin,
											'fecha': serie_pro_venta.date,
											'estatus': status,
											'precio_unico':price.price_unit,
											'devolucion_id': self.id,
										}
									registro_devo_id = registro_devo.create(registro_devo_value)
								else:
									raise ValidationError('Este numero de serie ya se agrego a tu tabla...')	
						else:
							raise ValidationError('Esta orden de pedido no pertenece al mismo proveedor')	
					else:
						raise ValidationError('No existe un compra para este numero de serie')
				else:
					raise ValidationError('Lo sentimos no se encotro un stock de venta para esta serie')	
			else:
				raise ValidationError('El numero de serie no se encotro, por favor intente con otro.')
		else:
			buscar_serie = self.env['stock.move.line'].search([('lot_id', '=', self.serie)], limit=1)
			if buscar_serie:
				buscar_ref = self.env['stock.picking'].search([('name', '=', buscar_serie.reference)], limit=1)
				if buscar_ref:
					self.write({'salida': buscar_ref.name})
					buscar_compra = self.env['purchase.order'].search([('name','=', buscar_ref.origin)], limit=1)
					if buscar_compra:
						if buscar_compra.partner_id.id == self.nombre_responsable.id:
							if buscar_ref.picking_type_code == 'incoming':

								self.numero_responsable = buscar_ref.partner_id.ref
								self.estado_procedencia = buscar_ref.partner_id.state_id.id
								self.ciudad_procedencia = buscar_ref.partner_id.city
								self.codigo_postal = buscar_ref.partner_id.zip

								igual = 0
					
								for record in self.tabla_devo:
									if record.serie == buscar_serie.lot_id:
										igual +=1
									else:
										igual = 0	
								if igual == 0:
									status = ''
									if buscar_compra.plazo_devo > self.fecha_devolucion:
										status = 'Aprovado'
									else:
										status = 'Rechazado por tiempo'			
									registro_devo = self.env['tabla.devo']

									for pri in buscar_compra:
										price = self.env['purchase.order.line'].search([('product_id', '=', buscar_serie.product_id.id)], limit=1)

										registro_devo_value = {
											'producto': buscar_serie.product_id.id,
											'serie': buscar_serie.lot_id.id,
											'pedido': buscar_ref.origin,
											'fecha': buscar_serie.date,
											'estatus': status,
											'precio_unico':price.price_unit,
											'devolucion_id': self.id,
										}
									registro_devo_id = registro_devo.create(registro_devo_value)
								else:
									raise ValidationError('Este numero de serie ya se agrego a tu tabla...')	
						else:
							raise ValidationError('Esta orden de pedido no pertenece al mismo proveedor')	
					else:
						raise ValidationError('No existe un compra para este numero de serie')		
				else:
					raise ValidationError('No se encotro una referencia para este numero de serie')
			else:
				raise ValidationError('No se encontro el numero de serie, intente con otro por favor.')

	@api.one
	def aprovar(self):
		for record in self:
			productos_aprovados = 0
			productos_rechazados = 0
			for line in record.tabla_devo:
				if line.estatus == 'Aprovado':
					pedido = line.pedido
					seriea = self.env['stock.move.line'].search([('lot_id', '=', line.serie.name)])
					productos_aprovados = self.env['tabla.devo'].search([('estatus', '=', 'Aprovado'),('devolucion_id', '=', self.id)])
				if line.estatus == 'Rechazado por tiempo':
					serier = self.env['stock.move.line'].search([('lot_id', '=', line.serie.name)])
					productos_rechazados = self.env['tabla.devo'].search([('estatus', '=', 'Rechazado por tiempo'),('devolucion_id', '=', self.id)])		
			if productos_aprovados != 0:
				unit = self.env['product.uom'].search([('name', '=', 'Unidad(es)')])
				type_devo = self.env['stock.picking.type'].search([('devo_proveedor', '=', True)])
				reference = self.env['stock.picking'].search([('name', '=', seriea.reference)], limit=1)
				stock_obj = self.env['stock.picking']
				stock_values = {
					'partner_id': self.nombre_responsable.id,
					'location_id': reference.location_id.id,
					'location_dest_id': reference.location_dest_id.id,
					'picking_type_id': type_devo.return_picking_type_id.id,
					'origin': self.referencia,
				}
				stock_id = stock_obj.create(stock_values)
				if stock_id:
					for line in productos_aprovados:
						qty = 1
						self.env['stock.move'].create({
							'location_id': reference.location_id.id,
							'location_dest_id': reference.location_dest_id.id,
							'product_uom_qty': qty,
							'name': line.producto.name,
							'product_id': line.producto.id,
							'state': 'draft',
							'product_uom': unit.id,
							'picking_id': stock_id.id,
							'company_id': reference.company_id.id, 
						})		

			if productos_rechazados != 0:
				unit = self.env['product.uom'].search([('name', '=', 'Unidad(es)')])
				type_devo = self.env['stock.picking.type'].search([('devo_rechazadas', '=', True)])
				reference = self.env['stock.picking'].search([('name', '=', serier.reference)], limit=1)
				stock_obj = self.env['stock.picking']
				stock_values = {
					'partner_id': self.nombre_responsable.id,
					'location_id': reference.location_id.id,
					'location_dest_id': reference.location_dest_id.id,
					'picking_type_id': type_devo.return_picking_type_id.id,
					'origin': self.referencia,
				}
				stock_id = stock_obj.create(stock_values)
				if stock_id:
					for line in productos_rechazados:
						qty = 1
						self.env['stock.move'].create({
							'location_id': reference.location_id.id,
							'location_dest_id': reference.location_dest_id.id,
							'product_uom_qty': qty,
							'name': line.producto.name,
							'product_id': line.producto.id,
							'state': 'draft',
							'product_uom': unit.id,
							'picking_id': stock_id.id,
							'company_id': reference.company_id.id, 
						})
				
			

class TablaDevoluciones(models.Model):
	_name = "tabla.devo"

	producto = fields.Many2one('product.product', string="Producto")
	talla = fields.Char(string="Talla")
	serie = fields.Many2one('stock.production.lot', string="Serie")
	pedido = fields.Char(string="Pedido de venta")
	fecha = fields.Datetime(string="Fecha de compra")
	estatus = fields.Char(string="Estatus")
	motivo = fields.Many2one('devo.motivo', string="Motivo")
	devolucion_id = fields.Many2one('model.devo', ondelete="cascade")
	precio_unico = fields.Float(string="Precio")

class DevoMotivo(models.Model):
	_name = "devo.motivo"
	_rec_name = 'name'

	name = fields.Char(string="Motivo")

class ProveedorCliente(models.Model):
	_inherit = 'stock.picking.type'	

	devo_cliente = fields.Boolean(string="Cliente")
	devo_proveedor = fields.Boolean(string="Proveedor")
	devo_rechazadas = fields.Boolean(string="Productos rechazados")
	devo_rechadoclientes = fields.Boolean(string="Productos rechazados a clientes")


class PlazoDevolucionSale(models.Model):
	_inherit = 'sale.order'

	intervalo_defecto = fields.Boolean(string="Usar plazo de devolucion por defecto", default=True, help="El plazo de devolucion por defecto es de 40 dias despues de la compra")
	intervalo_variante = fields.Integer(string="Nuevo plazo en dias")
	plazo_devo = fields.Date(string="Fecha limite de devolucion", compute="_compute_date_devo") 

	@api.one
	def _compute_date_devo(self):
		if self.confirmation_date:
			fecha = datetime.strptime(self.confirmation_date, '%Y-%m-%d %H:%M:%S') + timedelta(days=40)
			self.plazo_devo = fecha

class PlazoDevolucionPurchase(models.Model):
	_inherit = 'purchase.order'

	intervalo_defecto = fields.Boolean(string="Usar plazo de devolucion por defecto", default=True, help="El plazo de devolucion por defecto es de 40 dias despues de la compra")
	intervalo_variante = fields.Integer(string="Nuevo plazo en dias")
	plazo_devo = fields.Date(string="Fecha limite de devolucion", compute="_compute_date_devo") 

	@api.one
	def _compute_date_devo(self):
		if self.date_order:
			if self.intervalo_defecto == True:
				fecha = datetime.strptime(self.date_order, '%Y-%m-%d %H:%M:%S') + timedelta(days=40)
				self.plazo_devo = fecha
			else:
				intervalo = self.intervalo_variante 
				fecha = datetime.strptime(self.date_order, '%Y-%m-%d %H:%M:%S') + timedelta(days=intervalo)
				self.plazo_devo =fecha	

	@api.one
	def button_cancel(self):
		raise ValidationError(self.partner_id.property_stock_supplier.id)			


class StockPicking(models.Model):
	_inherit = 'stock.picking'

	@api.one
	def button_scrap(self):
		for line in self.move_lines:
			raise ValidationError(line.product_uom.id)		

		