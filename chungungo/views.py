from flask import render_template, redirect, url_for, request, session, flash, Markup
from flask_babel import gettext
from chungungo import app
from chungungo.validator import check_bc
from chungungo.network import *
from chungungo.forms import *
from os import urandom

@app.route('/')
def index():
	if 'address' in session:
		balance = getbalance(session['address'])
		return render_template('home.html', balance=balance)
	else:
		return redirect(url_for('login'))

@app.route('/tx/<txid>')
def tx(txid):
	try:
		tx = gettx(txid)
		return render_template('tx_viewer.html', tx=tx)
	except:
		flash('Error de lectura de transacción', 'is-danger')
		return redirect(url_for('index'))

@app.route('/paper')
def paper():
	rand_string = urandom(2048)
	privkey = sha256(rand_string)
	address = privtoaddr(privkey, 88)
	wallet = {'address' : address, 'privkey' : privkey}
	return render_template('wallet.html', wallet=wallet)


@app.route('/history')
def history():
	if 'address' in session:
		if request.args.get('page'):
			current_page = int(request.args.get('page')) - 1
		else:
			current_page = 0

		info = gethistory(session['address'], current_page)
		history = info[0]
		pages = info[1]

		return render_template('history.html', history=history, pages=pages, current_page=current_page)
	else:
		return render_template('index.html')


@app.route('/send', methods=['GET','POST'])
def send():
	if 'address' in session:
		form = sendform(request.form)
		balance = getbalance(session['address'])

		if form.validate_on_submit():

			address = session['address']
			privkey = session['privkey']

			receptor = request.form['address']
			op_return = request.form['msg']
			amount = float(request.form['amount'])

			verify = check_bc(receptor)

			if verify and receptor.startswith('c'):
				unspent = getunspent(address, amount)

				if amount <= unspent['used']:
					msg = broadcast(session, unspent, amount, receptor, op_return)

					try:
						flash('Transacción enviada', 'is-primary')
					except:
						msg = broadcasting.text
						flash(Markup('ERROR<br>%s' % msg), 'is-danger')
					
					return redirect(url_for('index'))

				else:
					flash('Monto - Saldo insuficiente', 'is-danger')
			else:
				flash('Dirección - Error de formato', 'is-danger')
			
	
			return redirect(url_for('send'))
		else:
			flash_errors(form)
			return render_template('send.html', balance=balance, form=form)
	else:
		return redirect(url_for('index'))



@app.route('/login', methods=['GET','POST'])
def login():
	form = privkeyform(request.form)
	if form.validate_on_submit():

		privkey = form.privkey.data

		try:
			address = privtoaddr(privkey, 88)
			session['address'] = address
			session['privkey'] = privkey
			return redirect(url_for('index'))
		
		except:
			flash('Llave Privada - Error de formato', 'is-danger')
	else:
		flash_errors(form)
	return render_template('login.html', form=form)


@app.route('/logout')
def logout():
	session.pop('address', None)
	session.pop('privkey', None)
	return redirect(url_for('index'))