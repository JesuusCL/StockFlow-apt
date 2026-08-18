from database.db import db
from models.categoria import Categoria


def listar_categorias(empresa_id):
    return (Categoria.query
            .filter_by(id_empresa=empresa_id)
            .order_by(Categoria.nombre)
            .all())


def crear_categoria(empresa_id, nombre, descripcion=None):
    categoria = Categoria(id_empresa=empresa_id, nombre=nombre, descripcion=descripcion)
    db.session.add(categoria)
    db.session.commit()
    return categoria


def obtener_categoria_de_empresa(categoria_id, empresa_id):
    """Devuelve la categoria solo si pertenece a la empresa indicada, o None."""
    return Categoria.query.filter_by(id_categoria=categoria_id, id_empresa=empresa_id).first()


def eliminar_categoria(categoria):
    # Los productos que usaban esta categoria quedan con id_categoria = NULL
    # (definido en el modelo fisico de la Fase 2: ON DELETE SET NULL)
    db.session.delete(categoria)
    db.session.commit()
