from flask import Flask, render_template, request, redirect, url_for, flash, Response, stream_with_context
from flaskext.mysql import MySQL
from decouple import config
import json
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql, hashlib

app = Flask(__name__)


mysql = MySQL()
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_USER'] = config('USER_DB')
app.config['MYSQL_DATABASE_PASSWORD'] = config('PASSWORD_DB')
app.config['MYSQL_DATABASE_DB'] = config('NAME_DB')
mysql.init_app(app)


def _datos(cur):
    cur.execute(
        'SELECT fecha_adquisicion, numero1 FROM datos_tiempo_real WHERE id = (SELECT MAX(id) FROM datos_tiempo_real)')
    datos_tiempo_real = cur.fetchall()

    json_data = json.dumps(
        {'fecha': datos_tiempo_real[0][0], 'numero1': datos_tiempo_real[0][1]})

    yield f"data:{json_data}\n\n"





@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registro')
def registro():
    return render_template('registro.html')

@app.route('/registro-exitoso', methods=['POST'])
def registro_exitoso():
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellidos']
        ID = request.form['ID']
        celular = request.form['celular']
        estatura = request.form['estatura']
        edad = request.form['edad']
        correo = request.form['correo']
        password = generate_password_hash(request.form['password'])
        admin = 0
        cur = mysql.get_db().cursor()
        query = 'INSERT INTO tabla_prueba (nombre, apellido, ID, edad, correo, password, admin, celular, estatura) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'
        cur.execute(query, (nombre, apellido, ID, edad, correo, password, admin, celular, estatura))
        cur.close()
        return render_template('registro-exitoso.html')


@app.route('/iniciar-sesion', methods=['GET', 'POST'])
def iniciar_sesion():
    if request.method == 'POST':
        print("ESTAS EN EL INICIO DE SESION")
        cur = mysql.get_db().cursor()
        query = "SELECT correo, password, nombre, admin, apellido FROM tabla_prueba WHERE correo = '{}'".format(request.form['usuario'])
        cur.execute(query)
        global row
        row = cur.fetchone()
        print(row)
        cur.close()
        if row != None:
            print("ENCONTRÒ CORREO")
            if check_password_hash(row[1], request.form['password']):
                print("SABE LA CONTRASEÑA")
                if row[3] == '1':
                    return redirect(url_for('super'))
                else:
                    return redirect(url_for('usuario'))
        else:
            print("No hay")
        return render_template('sesion.html')
    else:
        return render_template('sesion.html')

@app.route('/nosotros')
def nosotros():
    return render_template('nosotros.html')

@app.route('/contacto')
def contacto():
    return render_template('contacto.html')

@app.route('/planes')
def planes():
    return render_template('planes.html')

@app.route('/usuario', methods=['POST','GET'])
def usuario():
    if request.method == 'POST':
       print("Hola")
    return render_template('perfil.html',nombre=row[2], password=row[1], apellido=row[4])


@app.route('/super', methods=['POST', 'GET'])
def super():
    cur = mysql.get_db().cursor()
    query = "SELECT nombre, apellido, ID, edad, correo, celular FROM tabla_prueba WHERE admin = '0'"
    cur.execute(query)
    global datos
    datos = cur.fetchall()
    cur.close()
    print(datos)
    return render_template('perfilSuper.html', nombre=row[2], datos=datos, apellidos=row[4])

@app.route('/borrar', methods=['POST'])
def borrar():
    if request.method == 'POST':
        DU = int(request.form['btn-borrar'])-1
        cur = mysql.get_db().cursor()
        query = "DELETE FROM tabla_prueba WHERE ID = '{}'".format(datos[DU][2])
        cur.execute(query)
        cur.close()
        return redirect(url_for('super'))

@app.route('/editar', methods=['POST'])
def editar():
    if request.method == 'POST':
        print(request.form['btn-editar'])
    return redirect(url_for('super'))

@app.route('/registro-super', methods=['POST', 'GET'])
def registroSuper():
    if request.method == 'POST':
        cur = mysql.get_db().cursor()
        query= "SELECT correo, admin FROM tabla_prueba WHERE correo ='{}'".format(request.form['correoAdmin'])
        cur.execute(query)
        adminDb = cur.fetchone()
        if adminDb != None and adminDb[1] == '1':
            print(adminDb)
            passwordAdmin = generate_password_hash(request.form['passwordAdmin'])
            query = "UPDATE tabla_prueba set password = '{}' WHERE correo='{}'".format(passwordAdmin, adminDb[0])
            cur.execute(query)
            cur.close()
            return redirect(url_for('superExitoso'))
        else:
            print("No entres")
            cur.close()
            return redirect(url_for('superFallido'))
    else:
        return render_template('registroSuper.html')
    
@app.route('/superExitoso')
def superExitoso():
    return render_template('exitosoSuper.html')

@app.route('/superFallido')
def superFallido():
    return render_template('fallidoSuper.html')

@app.route('/datos_monitoreo')
def datos_monitoreo():
    cur = mysql.get_db().cursor()

    enviar = _datos(cur)

    return Response(stream_with_context(enviar), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True)
