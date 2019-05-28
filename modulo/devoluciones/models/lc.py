		if self.tipo_usuario =='proveedor':
			for record in self:	
				productos_aprovadospr = 0
				productos_rechazadospr = 0

				fecha_devolucion = date.today()
				notap_obj = self.env['account.invoice']
				notapr_values = {
					'partner_id': self.nombre_responsable.id,
					'date_invoice': fecha_devolucion,
					'number': self.numero_responsable,
					'reference':self.referencia,
					'type':'in_refund'
					}
				notap_id = notap_obj.create(notapr_values)
				for lin in record.tabla_devo:					
					if lin.estatus == 'Aprovado':
						productos_aprovadospr = self.env['tabla.devo'].search([('estatus', '=', 'Aprovado'),('devolucion_id', '=', self.id)])
						if productos_aprovadospr !=0:
							if notap_id:
								line_notap_obj = self.env['account.invoice.line']
								line_notapr_values = {
									'product_id': lin.producto.id,
									'name': lin.producto.name,
									'account_id': 1,
									'quantity': 1,
		  							'price_unit': lin.precio_unico,
									'invoice_id': notap_id.id,
								}
								line_notap_id = line_notap_obj.create(line_notapr_values)						
								#notap_id.action_invoice_open()
							self.id_nota = notap_id.id
					else:
						raise ValidationError('no hay productos approvados no se puede hacer la devolucion')