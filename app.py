from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import fields
from sqlalchemy.orm import relationship
from marshmallow_sqlalchemy import ModelSchema
import enum
import requests as req

## Initial config for Flask and MySQL ##
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='mysql+pymysql://root:root@:3306/orcamento_python'
db = SQLAlchemy(app)

base_url_produtos = "http://localhost:8080/produtos"

## Models ##
class Endereco(db.Model):
    __tableName__ = "endereco"
    idEndereco = db.Column(db.Integer, primary_key=True)
    cep = db.Column(db.String(11))
    logradouro = db.Column(db.String(70))
    numero = db.Column(db.Integer)
    cidade = db.Column(db.String(90))
    estado = db.Column(db.String(2))
    clientes = db.relationship("Cliente", back_populates="endereco")
    def _init_(self, cep, logradouro, numero, cidade, estado):
        self.cep = cep
        self.logradouro = logradouro
        self.numero = numero
        self.cidade = cidade
        self.estado = estado
    def create(self):
        db.session.add(self)
        db.session.commit()
        return self    
    def __repr__(self):
        return '' % self.idEndereco
        
class Cliente(db.Model):
    __tableName__ = "cliente"
    idCliente = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    telefone = db.Column(db.String(15))
    email = db.Column(db.String(90))
    orcamentos = db.relationship("Orcamento", back_populates="cliente")
    idEndereco = db.Column(db.Integer, db.ForeignKey('endereco.idEndereco'))
    endereco = db.relationship("Endereco", back_populates="clientes", uselist=False)
    def create(self):
        db.session.add(self)
        db.session.commit()
        return self
    def _init_(self, nome, telefone, email):
        self.nome = nome
        self.telefone = telefone
        self.email = email
    def __repr__(self):
        return '' % self.idCliente

class OrcamentoStatus(enum.Enum):
    CRIADA = 1
    CONFIRMADA = 2
    CANCELADA = 3

class Orcamento(db.Model):
    __tableName__ = "orcamento"
    idOrcamento = db.Column(db.Integer, primary_key=True)
    createDate = db.Column(db.Date)
    total = db.Column(db.Float)
    status = db.Column(db.Integer)
    idCliente = db.Column(db.Integer, db.ForeignKey('cliente.idCliente'))
    cliente = db.relationship("Cliente", back_populates="orcamentos", uselist=False)
    detalhesOrcamento = db.relationship("DetalheOrcamento", back_populates="orcamento")
    def create(self):
        db.session.add(self)
        db.session.commit()
        return self
    def _init_(self, createDate, total, status):
        self.createDate = createDate
        self.total = total
        self.status = status
    def __repr__(self):
        return '' % self.idOrcamento

class DetalheOrcamento(db.Model):
    __tableName__ = "detalheOrcamento"
    idDetalhe = db.Column(db.Integer, primary_key=True)
    qty = db.Column(db.Integer)
    custoTotal = db.Column(db.Float)
    idProduto = db.Column(db.Integer)
    nome = db.Column(db.String(100))
    preco = db.Column(db.Float)
    idOrcamento = db.Column(db.Integer, db.ForeignKey('orcamento.idOrcamento'))
    orcamento = db.relationship("Orcamento", back_populates="detalhesOrcamento", uselist=False)
    def create(self):
        db.session.add(self)
        db.session.commit()
        return self
    def _init_(self, qty, custoTotal, idProduto, nome, preco):
        self.qty = qty
        self.custoTotal = custoTotal
        self.idProduto = idProduto
        self.nome = nome
        self.preco = preco
    def __repr__(self):
        return '' % self.idDetalhe
       
db.create_all()  

## Schemas ##
class DetalheOrcamentoSchema(ModelSchema):
    class Meta:
        model = DetalheOrcamento
        sqla_session = db.session
    idDetalhe = fields.Integer(dump_only=True)
    qty = fields.Number(required=True)
    custoTotal = fields.Number(required=True)
    idProduto = fields.Integer(required=True)
    nome = fields.String(required=True)
    preco = fields.Number(required=True)

class OrcamentoSchema(ModelSchema):
    class Meta:
        model = Orcamento
        sqla_session = db.session
    idOrcamento = fields.Integer(dump_only=True)
    createDate = fields.Date(required=True)
    total = fields.Number(required=True)
    status = fields.Number(required=True)
    detalhesOrcamento = fields.List(fields.Nested(DetalheOrcamentoSchema))

class ClienteSchema(ModelSchema):
    class Meta:
        model = Cliente
        sqla_session = db.session
    idCliente = fields.Integer(dump_only=True)
    nome = fields.String(required=True)
    telefone = fields.String(required=True)
    email = fields.String(required=True)
    idEndereco = fields.Integer(dump_only=True)
    orcamentos = fields.List(fields.Nested(OrcamentoSchema))

class EnderecoSchema(ModelSchema):
    class Meta:
        model = Endereco
        sqla_session = db.session
    idEndereco = fields.Integer(dump_only=True)
    cep = fields.String(required=True)
    logradouro = fields.String(required=True)
    numero = fields.Number(required=True)
    cidade = fields.String(required=True)
    estado = fields.String(required=True)
    clientes = fields.List(fields.Nested(ClienteSchema))


## Controller ##
    ## Endereco ##
    @app.route('/enderecos', methods = ['GET'])
    def getEnderecos():
        get_endereco = Endereco.query.all()
        endereco_schema = EnderecoSchema(many=True)
        enderecos = endereco_schema.dump(get_endereco)
        return make_response(jsonify({"enderecos": enderecos}))
    
    @app.route('/enderecos', methods = ['POST'])
    def postEndereco():
        data = request.get_json()
        endereco_schema = EnderecoSchema()
        endereco = endereco_schema.load(data)
        result = endereco_schema.dump(endereco.create())
        return make_response(jsonify({"endereco": result}),200)
    

    ## Cliente ##
    @app.route('/clientes', methods = ['GET'])
    def getClientes():
        get_clientes = Cliente.query.all()
        cliente_schema = ClienteSchema(many=True)
        clientes = cliente_schema.dump(get_clientes)
        return make_response(jsonify({"clientes": clientes}))
        
        
    @app.route('/clientes', methods = ['POST'])
    def postCliente():
        data = request.get_json()
        cliente_schema = ClienteSchema()
        cliente = cliente_schema.load(data)
        result = cliente_schema.dump(cliente.create())
        return make_response(jsonify({"cliente": result}),200)
        
        
    @app.route('/clientes/<id>', methods = ['PUT'])
    def putCliente(id):
        data = request.get_json()
        get_cliente = Cliente.query.get(id)
        if data.get('nome'):
            get_cliente.nome = data['nome']
        if data.get('telefone'):
            get_cliente.telefone = data['telefone']
        if data.get('email'):
            get_cliente.email = data['email']  
        db.session.add(get_cliente)
        db.session.commit()
        cliente_schema = ClienteSchema(only=['idCliente', 'nome', 'telefone','email'])
        cliente = cliente_schema.dump(get_cliente)
        return make_response(jsonify({"cliente": cliente}))
    
    ## Produtos(externa) ##
    @app.route('/produtos', methods = ['GET'])
    def getProdutos():
        response = req.get(base_url_produtos)
        data = response.json()
        return make_response(jsonify({"produtos": data}))
    
    ## Orçamento ##
    @app.route('/orcamentos', methods = ['GET'])
    def getOrcamento():
        get_orcamento = Orcamento.query.all()
        orcamento_schema = OrcamentoSchema(many=True)
        orcamentos = orcamento_schema.dump(get_orcamento)
        return make_response(jsonify({"orcamentos": orcamentos}))
        
    @app.route('/orcamentos', methods = ['POST'])
    def postOrcamento():
        data = request.get_json()
        orcamento_schema = OrcamentoSchema()
        orcamento = orcamento_schema.load(data)
        result = orcamento_schema.dump(orcamento.create())
        return make_response(jsonify({"orcamento": result}),200)
         
    @app.route('/orcamentos/<id>', methods = ['PUT'])
    def putOrcamento(id):
        data = request.get_json()
        get_orcamento = Orcamento.query.get(id)
        if data.get('createDate'):
            get_orcamento.createDate = data['createDate']
        if data.get('total'):
            get_orcamento.total = data['total']
        if data.get('status'):
            get_orcamento.status = data['status']
        db.session.add(get_orcamento)
        db.session.commit()
        orcamento_schema = OrcamentoSchema(only=['idOrcamento', 'createDate', 'total','status'])
        orcamento = orcamento_schema.dump(get_orcamento)
        return make_response(jsonify({"orcamento": orcamento}))
    
    ## Detalhe Orcamento  ##
    @app.route('/orcamentos/<id>', methods = ['DELETE'])
    def deleteOrcamentoById(id):
        get_orcamento = Orcamento.query.get(id)
        if get_orcamento:
            db.session.delete(get_orcamento)
            db.session.commit()
            return make_response(jsonify({"status": "success"}),200)
        return make_response("",204)
    
    ## Detalhe Orçamento ##
    @app.route('/orcamentos/detalhe/<id>', methods = ['PUT'])
    def putDetalheOrcamento(id):
        data = request.get_json()
        get_detalhe_orcamento = DetalheOrcamento.query.get(id)
        if data.get('qty'):
            get_detalhe_orcamento.qty = data['qty']
        if data.get('custoTotal'):
            get_detalhe_orcamento.custoTotal = data['custoTotal']
        if data.get('idProduto'):
            get_detalhe_orcamento.idProduto = data['idProduto']
        if data.get('nome'):
            get_detalhe_orcamento.nome = data['nome']
        if data.get('preco'):
            get_detalhe_orcamento.preco = data['preco']
        db.session.add(get_detalhe_orcamento)
        db.session.commit()
        detalhe_orcamento_schema = DetalheOrcamentoSchema(only=['idDetalhe', 'qty', 'custoTotal','idProduto', 'nome', 'preco'])
        detalhe_orcamento = detalhe_orcamento_schema.dump(get_detalhe_orcamento)
        return make_response(jsonify({"detalhe_orcamento": detalhe_orcamento}))
        
    @app.route('/orcamentos/detalhe/<id>', methods = ['DELETE'])
    def deleteOrcamentoDetalheById(id):
        get_detalhe_orcamento = DetalheOrcamento.query.get(id)
        if get_detalhe_orcamento:
            db.session.delete(get_detalhe_orcamento)
            db.session.commit()
            return make_response(jsonify({"status": "success"}),200)
        return make_response("",204)
    