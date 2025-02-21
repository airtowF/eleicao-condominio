from flask import Flask, render_template, request, redirect, url_for
from models import db, Morador, Candidato, Apartamento, Urna

app = Flask(__name__, template_folder='template')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eleicao.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
@app.route('/home', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        nome = request.form['nome']
        apartamento_numero = int(request.form['apartamento'])
        candidato = 'candidato' in request.form  
        numero = request.form.get('numero', None)

        apartamento = Apartamento.query.filter_by(numero=apartamento_numero).first()
        if not apartamento:
            apartamento = Apartamento(numero=apartamento_numero)
            db.session.add(apartamento)
            db.session.commit()

        if candidato:
            novo_morador = Candidato(nome=nome, apartamento_id=apartamento.id, candidato=True, numero=numero)
            mensagem = f"Candidato {nome} cadastrado com sucesso!"
        else:
            novo_morador = Morador(nome=nome, apartamento_id=apartamento.id, candidato=False)
            mensagem = f"Morador {nome} cadastrado com sucesso!"

        db.session.add(novo_morador)
        db.session.commit()

        return render_template('home.html', mensagem=mensagem)

    return render_template('home.html', mensagem=None)



@app.route('/urna', methods=['GET', 'POST'])
def urna():
    urna = Urna()
    apartamentos = Apartamento.query.all()

    apartamento_selecionado = request.form.get('apartamento', None)
    moradores = []
    if apartamento_selecionado and apartamento_selecionado.isdigit():
        apartamento = Apartamento.query.filter_by(numero=int(apartamento_selecionado)).first()
        if apartamento:
            # Exibir apenas moradores que não são candidatos e que ainda não votaram
            moradores = [m for m in apartamento.moradores if not m.candidato and not m.votou]

    if request.method == 'POST' and 'candidato' in request.form:
        candidato_numero = request.form.get('candidato', '').strip()
        morador_id = request.form.get('morador', None)

        if not apartamento_selecionado or not candidato_numero or not morador_id:
            return "Erro: Número do apartamento, morador ou candidato não pode estar vazio.", 400

        if not apartamento_selecionado.isdigit() or not candidato_numero.isdigit() or not morador_id.isdigit():
            return "Erro: Valores inválidos.", 400

        apartamento_numero = int(apartamento_selecionado)
        candidato_numero = int(candidato_numero)
        morador_id = int(morador_id)

        apartamento = Apartamento.query.filter_by(numero=apartamento_numero).first()
        if not apartamento:
            return "Erro: Apartamento não encontrado.", 404

        morador = Morador.query.get(morador_id)
        if not morador or morador.apartamento_id != apartamento.id:
            return "Erro: Morador inválido.", 400

        if morador.votou:
            return "Erro: Este morador já votou.", 400

        resultado_final = urna.votar(morador.id, candidato_numero)

        if not resultado_final:
            return "Erro: Voto não registrado. Candidato inválido.", 400

        return redirect(url_for('resultados'))

    # 🔹 Filtra apenas apartamentos com moradores que ainda não votaram
    apartamentos_disponiveis = [
        apt for apt in apartamentos if any(not m.votou for m in apt.moradores)
    ]

    candidatos = Candidato.query.all()
    return render_template(
        'urna.html', 
        candidatos=candidatos, 
        apartamentos=apartamentos_disponiveis, 
        moradores=moradores, 
        apartamento_selecionado=apartamento_selecionado
    )

@app.route('/resultados')
def resultados():
    urna = Urna()
    resultados = urna.resultados()
    return render_template('resultados.html', resultados=resultados)

if __name__ == '__main__':
    app.run(debug=True)