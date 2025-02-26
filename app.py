from flask import Flask, render_template, request, redirect, url_for
from models import db, Morador, Candidato, Apartamento, Urna
from validate_docbr import CPF

app = Flask(__name__, template_folder='template')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eleicao.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

def validar_cpf(cpf):
    """Valida o CPF de forma simples e confiável."""
    cpf_obj = CPF()
    return cpf_obj.validate(cpf)

@app.route('/')
@app.route('/home', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        nome = request.form['nome']
        cpf = request.form['cpf']
        apartamento_numero = int(request.form['apartamento'])
        candidato = 'candidato' in request.form  
        numero = request.form.get('numero', None)

        # 🔹 Valida o CPF antes de salvar
        if not validar_cpf(cpf):
            return render_template('home.html', mensagem="Erro: CPF inválido!")

        # 🔹 Verifica se o CPF já está cadastrado
        if Morador.query.filter_by(cpf=cpf).first():
            return render_template('home.html', mensagem="Erro: CPF já cadastrado!")

        apartamento = Apartamento.query.filter_by(numero=apartamento_numero).first()
        if not apartamento:
            apartamento = Apartamento(numero=apartamento_numero)
            db.session.add(apartamento)
            db.session.commit()

        if candidato:
            novo_morador = Candidato(nome=nome, cpf=cpf, apartamento_id=apartamento.id, candidato=True, numero=numero)
            mensagem = f"Candidato {nome} cadastrado com sucesso!"
        else:
            novo_morador = Morador(nome=nome, cpf=cpf, apartamento_id=apartamento.id, candidato=False)
            mensagem = f"Morador {nome} cadastrado com sucesso!"

        db.session.add(novo_morador)
        db.session.commit()

        return render_template('home.html', mensagem=mensagem)

    return render_template('home.html', mensagem=None)




@app.route('/urna', methods=['GET', 'POST'])
def urna():
    urna = Urna()
    apartamentos = Apartamento.query.all()
    mensagem_erro = None  # Variável para armazenar mensagens de erro
    exibir_urna = False  # Controla se a urna será exibida

    apartamento_selecionado = request.form.get('apartamento', None)
    cpf_digitado = request.form.get('cpf', '').strip()
    morador_id = request.form.get('morador', None)
    moradores = []

    if apartamento_selecionado and apartamento_selecionado.isdigit():
        apartamento = Apartamento.query.filter_by(numero=int(apartamento_selecionado)).first()
        if apartamento:
            moradores = [m for m in apartamento.moradores if not m.candidato and not m.votou]

    if request.method == 'POST' and 'validar_cpf' in request.form:
        if not apartamento_selecionado or not morador_id or not cpf_digitado:
            mensagem_erro = "Erro: Número do apartamento, CPF ou morador não pode estar vazio."
        elif not apartamento_selecionado.isdigit() or not morador_id.isdigit():
            mensagem_erro = "Erro: Valores inválidos."
        else:
            morador = Morador.query.get(int(morador_id))
            if not morador or morador.cpf != cpf_digitado:
                mensagem_erro = "Erro: CPF incorreto. Tente novamente."
            else:
                exibir_urna = True  # CPF correto, agora podemos exibir a urna

    candidatos = Candidato.query.all()
    return render_template(
        'urna.html',
        candidatos=candidatos,
        apartamentos=apartamentos,
        moradores=moradores,
        apartamento_selecionado=apartamento_selecionado,
        mensagem_erro=mensagem_erro,
        exibir_urna=exibir_urna
    )


@app.route('/resultados')
def resultados():
    urna = Urna()
    resultados = urna.resultados()
    return render_template('resultados.html', resultados=resultados)


if __name__ == '__main__':
    app.run(debug=True)