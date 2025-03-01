from flask import Flask, render_template, request, redirect, url_for, session
from models import db, Morador, Candidato, Apartamento, Urna
from validate_docbr import CPF

app = Flask(__name__, template_folder='template')
app.secret_key = "chave_secreta_segura"

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

@app.route('/mesario', methods=['GET', 'POST'])
def mesario():
    apartamentos = Apartamento.query.all()
    moradores = []
    mensagem_erro = None

    apartamento_selecionado = request.form.get('apartamento')

    # 🔹 Certifique-se de que o apartamento_selecionado é um número válido
    if apartamento_selecionado and apartamento_selecionado.isdigit():
        apartamento_id = int(apartamento_selecionado)
        apartamento = Apartamento.query.filter_by(numero=apartamento_id).first()
        if apartamento:
            moradores = apartamento.moradores

    if request.method == 'POST' and 'validar_cpf' in request.form:
        morador_id = request.form.get('morador')
        cpf_digitado = request.form.get('cpf', '').strip()

        if not apartamento_selecionado or not morador_id or not cpf_digitado:
            mensagem_erro = "Erro: Todos os campos são obrigatórios."
        else:
            morador = Morador.query.get(int(morador_id))

            # 🔹 Certifique-se de que o apartamento do morador é válido
            if morador.votou:
                mensagem_erro = "Erro: Este morador já votou."
            elif morador.cpf != cpf_digitado:
                mensagem_erro = "Erro: CPF incorreto."
            elif morador.candidato:
                mensagem_erro = "Erro: Candidatos não podem votar."
            else:
                # ✅ Armazena os dados do morador na sessão e redireciona para a urna
                session['morador_id'] = morador.id
                session['apartamento'] = apartamento_id
                return redirect(url_for('urna'))

    return render_template('mesario.html', apartamentos=apartamentos, moradores=moradores, mensagem_erro=mensagem_erro)

@app.route('/urna', methods=['GET', 'POST'])
def urna():
    urna = Urna()
    mensagem_erro = None

    morador_id = session.get('morador_id')
    apartamento_selecionado = session.get('apartamento')

    if not morador_id:
        return redirect(url_for('mesario'))  # Se não tiver morador, volta para mesário

    morador = Morador.query.get(morador_id)
    if not morador or morador.votou:
        return redirect(url_for('mesario'))  # Se já votou, volta para mesário

    if request.method == 'POST' and 'candidato' in request.form:
        candidato_numero = request.form.get('candidato', '').strip()

        if not candidato_numero or not candidato_numero.isdigit():
            mensagem_erro = "Erro: Número do candidato inválido."
        else:
            resultado_final = urna.votar(morador.id, int(candidato_numero))

            if resultado_final:
                session.pop('morador_id', None)  # Remove o morador da sessão depois de votar
                return redirect(url_for('resultados'))  # ✅ Se todos votaram, vai para resultados
            else:
                session.pop('morador_id', None)  # Remove o morador da sessão depois de votar
                return redirect(url_for('mesario'))  # Se não, volta para mesário

    candidatos = Candidato.query.all()
    return render_template('urna.html', candidatos=candidatos, morador=morador, mensagem_erro=mensagem_erro)


@app.route('/resultados')
def resultados():
    urna = Urna()
    resultados = urna.resultados()
    return render_template('resultados.html', resultados=resultados)

if __name__ == '__main__':
    app.run(debug=True)
