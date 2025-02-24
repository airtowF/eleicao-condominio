from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Morador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(11), unique=True, nullable=False)  # 🔹 Novo campo
    apartamento_id = db.Column(db.Integer, db.ForeignKey('apartamento.id'), nullable=False)
    candidato = db.Column(db.Boolean, default=False)
    votou = db.Column(db.Boolean, default=False)
    apartamento = db.relationship('Apartamento', back_populates='moradores')
    type = db.Column(db.String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'morador',
        'polymorphic_on': type
    }

class Candidato(Morador):
    id = db.Column(db.Integer, db.ForeignKey('morador.id'), primary_key=True)
    numero = db.Column(db.Integer, unique=True, nullable=False)
    votos = db.Column(db.Integer, default=0)

    __mapper_args__ = {
        'polymorphic_identity': 'candidato',
    }




class Apartamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.Integer, unique=True, nullable=False)
    moradores = db.relationship('Morador', back_populates='apartamento', enable_typechecks=False)
    votou = db.Column(db.Boolean, default=False) 

class Urna:
    def __init__(self):
        self.candidatos = Candidato.query.all()

    def votar(self, morador_id, candidato_numero):
        morador = Morador.query.get(morador_id)
        if not morador:
            return "Erro: Morador não encontrado."

        if morador.votou:
            return "Erro: Este morador já votou."

        candidato = Candidato.query.filter_by(numero=candidato_numero).first()
        if not candidato:
            return "Erro: Número do candidato inválido."

        # Registra o voto
        candidato.votos += 1
        morador.votou = True  # Marca o morador como "já votou"

        # 🔹 Marca o apartamento como "votado" assim que QUALQUER morador (não candidato) votar
        apartamento = Apartamento.query.get(morador.apartamento_id)
        if any(not m.candidato and m.votou for m in apartamento.moradores):
            apartamento.votou = True

        db.session.commit()

        # 🔹 Verifica se TODOS os apartamentos com moradores aptos já votaram
        todos_votaram = all(
            apt.votou for apt in Apartamento.query.all() if any(not m.candidato for m in apt.moradores)
        )

        return todos_votaram  # 🔹 Retorna True SOMENTE se todos os apartamentos válidos votaram



    def resultados(self):
        return {candidato.nome: candidato.votos for candidato in self.candidatos}