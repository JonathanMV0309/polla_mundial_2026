import re
from flask import jsonify
from flask import Flask, render_template, redirect, url_for, request, flash
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config['SECRET_KEY'] = 'mundial2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

def recalcular_puntos():

    # REINICIAR PUNTOS
    usuarios = User.query.all()

    for usuario in usuarios:
        usuario.puntos = 0

    # RECORRER PRONÓSTICOS
    pronosticos = Pronostico.query.all()

    for pronostico in pronosticos:

        partido = Partido.query.get(
            pronostico.partido_id
        )

        if (
            partido.goles_local is not None
            and
            partido.goles_visitante is not None
        ):

            usuario = User.query.get(
                pronostico.usuario_id
            )

            puntos = 0

            # 5 puntos marcador exacto
            if (
                pronostico.pred_local == partido.goles_local
                and
                pronostico.pred_visitante == partido.goles_visitante
            ):
                puntos += 5

            # 2 puntos goles local
            if pronostico.pred_local == partido.goles_local:
                puntos += 2

            # 2 puntos goles visitante
            if pronostico.pred_visitante == partido.goles_visitante:
                puntos += 2

            # 3 puntos resultado correcto
            resultado_real = (
                1 if partido.goles_local > partido.goles_visitante
                else -1 if partido.goles_local < partido.goles_visitante
                else 0
            )

            resultado_pronostico = (
                1 if pronostico.pred_local > pronostico.pred_visitante
                else -1 if pronostico.pred_local < pronostico.pred_visitante
                else 0
            )

            if resultado_real == resultado_pronostico:
                puntos += 3

            usuario.puntos += puntos

    db.session.commit()

def actualizar_fases_finales():

    print("ACTUALIZANDO FASES FINALES")

def obtener_mejores_terceros():

    grupos_data = {}

    partidos = Partido.query.all()

    fases_finales = [
        "16avos",
        "Octavos",
        "Cuartos",
        "Semis",
        "Final",
        "3er Puesto"
    ]

    for partido in partidos:

        if partido.goles_local is None:
            continue

        grupo = partido.grupo

        # Ignorar todas las fases finales
        if grupo in fases_finales:
            continue

        if grupo not in grupos_data:
            grupos_data[grupo] = {}

        for equipo in [
            partido.equipo_local,
            partido.equipo_visitante
        ]:

            if equipo not in grupos_data[grupo]:

                grupos_data[grupo][equipo] = {
                    "pj": 0,
                    "pts": 0,
                    "gf": 0,
                    "gc": 0,
                    "dg": 0
                }

        local = grupos_data[grupo][partido.equipo_local]
        visitante = grupos_data[grupo][partido.equipo_visitante]

        local["pj"] += 1
        visitante["pj"] += 1

        local["gf"] += partido.goles_local
        local["gc"] += partido.goles_visitante

        visitante["gf"] += partido.goles_visitante
        visitante["gc"] += partido.goles_local

        if partido.goles_local > partido.goles_visitante:
            local["pts"] += 3

        elif partido.goles_local < partido.goles_visitante:
            visitante["pts"] += 3

        else:
            local["pts"] += 1
            visitante["pts"] += 1

    terceros = []

    for grupo in grupos_data:

        equipos = []

        for nombre, datos in grupos_data[grupo].items():

            datos["dg"] = datos["gf"] - datos["gc"]

            equipos.append((nombre, datos))

        equipos.sort(
            key=lambda x: (
                x[1]["pts"],
                x[1]["dg"],
                x[1]["gf"]
            ),
            reverse=True
        )

        if len(equipos) >= 3:

            terceros.append({
                "grupo": grupo,
                "equipo": equipos[2][0],
                "pts": equipos[2][1]["pts"],
                "dg": equipos[2][1]["dg"],
                "gf": equipos[2][1]["gf"]
            })

    terceros.sort(
        key=lambda x: (
            x["pts"],
            x["dg"],
            x["gf"]
        ),
        reverse=True
    )

    print("\n===== TERCEROS ORDENADOS =====")
    for t in terceros:
        print(
            t["grupo"],
            t["equipo"],
            "PTS:", t["pts"],
            "DG:", t["dg"]
        )
    print("=============================\n")

    return terceros[:8]

def obtener_clasificacion_grupo(grupo):

    partidos = Partido.query.filter_by(
        grupo=grupo
    ).all()

    tabla = {}

    for partido in partidos:

        if (
            partido.goles_local is None or
            partido.goles_visitante is None
        ):
            continue

        local = partido.equipo_local
        visitante = partido.equipo_visitante

        if local not in tabla:
            tabla[local] = {
                "equipo": local,
                "pts": 0,
                "gf": 0,
                "gc": 0,
                "dg": 0
            }

        if visitante not in tabla:
            tabla[visitante] = {
                "equipo": visitante,
                "pts": 0,
                "gf": 0,
                "gc": 0,
                "dg": 0
            }

        gl = partido.goles_local
        gv = partido.goles_visitante

        tabla[local]["gf"] += gl
        tabla[local]["gc"] += gv

        tabla[visitante]["gf"] += gv
        tabla[visitante]["gc"] += gl

        if gl > gv:
            tabla[local]["pts"] += 3

        elif gv > gl:
            tabla[visitante]["pts"] += 3

        else:
            tabla[local]["pts"] += 1
            tabla[visitante]["pts"] += 1

    for equipo in tabla.values():
        equipo["dg"] = (
            equipo["gf"] -
            equipo["gc"]
        )

    clasificacion = sorted(
        tabla.values(),
        key=lambda x: (
            x["pts"],
            x["dg"],
            x["gf"]
        ),
        reverse=True
    )

    return clasificacion
def actualizar_16avos():

    print("\n######### ENTRE A ACTUALIZAR_16AVOS #########\n")

    A = obtener_clasificacion_grupo("A")
    B = obtener_clasificacion_grupo("B")
    C = obtener_clasificacion_grupo("C")
    D = obtener_clasificacion_grupo("D")
    E = obtener_clasificacion_grupo("E")
    F = obtener_clasificacion_grupo("F")
    G = obtener_clasificacion_grupo("G")
    H = obtener_clasificacion_grupo("H")
    I = obtener_clasificacion_grupo("I")
    J = obtener_clasificacion_grupo("J")
    K = obtener_clasificacion_grupo("K")
    L = obtener_clasificacion_grupo("L")

    print("Clasificaciones cargadas")

    terceros = obtener_mejores_terceros()

    print("Cantidad terceros:", len(terceros))

    print("\n======== MEJORES TERCEROS ========")

    for i, t in enumerate(terceros):
        print(
            f"{i} | {t['grupo']} | {t['equipo']} | "
            f"PTS={t['pts']} | DG={t['dg']}"
        )

    print("==================================\n")

    if len(terceros) < 8:
        print("ERROR: NO HAY 8 TERCEROS")
        return

    cruces = {

        73: (A[0]["equipo"], B[1]["equipo"]),
        74: (C[0]["equipo"], D[1]["equipo"]),
        75: (E[0]["equipo"], F[1]["equipo"]),
        76: (G[0]["equipo"], H[1]["equipo"]),

        77: (I[0]["equipo"], J[1]["equipo"]),
        78: (K[0]["equipo"], L[1]["equipo"]),

        79: (B[0]["equipo"], A[1]["equipo"]),
        80: (D[0]["equipo"], C[1]["equipo"]),

        81: (F[0]["equipo"], E[1]["equipo"]),
        82: (H[0]["equipo"], G[1]["equipo"]),

        83: (J[0]["equipo"], I[1]["equipo"]),
        84: (L[0]["equipo"], K[1]["equipo"]),

        85: (terceros[0]["equipo"], terceros[1]["equipo"]),
        86: (terceros[2]["equipo"], terceros[3]["equipo"]),
        87: (terceros[4]["equipo"], terceros[5]["equipo"]),
        88: (terceros[6]["equipo"], terceros[7]["equipo"])
    }

    print("\nCRUCES DE TERCEROS:")
    print("85:", cruces[85])
    print("86:", cruces[86])
    print("87:", cruces[87])
    print("88:", cruces[88])
    print()

    for partido_id, equipos in cruces.items():

        partido = Partido.query.get(partido_id)

        if partido:

            partido.equipo_local = equipos[0]
            partido.equipo_visitante = equipos[1]

    db.session.commit()

    print("######### 16AVOS ACTUALIZADOS #########\n") 

    
def actualizar_fases_finales():

    print("=================================")
    print("ENTRO A ACTUALIZAR_FASES_FINALES")
    print("=================================")

    def ganador(partido):

        if (
            partido.goles_local is None or
            partido.goles_visitante is None
        ):
            return f"Ganador Partido {partido.id}"

        # Resultado normal

        if partido.goles_local > partido.goles_visitante:
            return partido.equipo_local

        if partido.goles_visitante > partido.goles_local:
            return partido.equipo_visitante

        # Empate -> Penales

        if (
            partido.penales_local is not None and
            partido.penales_visitante is not None
        ):

            if partido.penales_local > partido.penales_visitante:
                return partido.equipo_local

            if partido.penales_visitante > partido.penales_local:
                return partido.equipo_visitante

        return f"Ganador Partido {partido.id}"

    def perdedor(partido):

        if (
            partido.goles_local is None or
            partido.goles_visitante is None
        ):
            return f"Perdedor Partido {partido.id}"

        # Resultado normal

        if partido.goles_local > partido.goles_visitante:
            return partido.equipo_visitante

        if partido.goles_visitante > partido.goles_local:
            return partido.equipo_local

        # Empate -> Penales

        if (
            partido.penales_local is not None and
            partido.penales_visitante is not None
        ):

            if partido.penales_local > partido.penales_visitante:
                return partido.equipo_visitante

            if partido.penales_visitante > partido.penales_local:
                return partido.equipo_local

        return f"Perdedor Partido {partido.id}"

    # ===== OCTAVOS =====

    mapa_octavos = {
        89: (73, 74),
        90: (75, 76),
        91: (77, 78),
        92: (79, 80),
        93: (81, 82),
        94: (83, 84),
        95: (85, 86),
        96: (87, 88)
    }

    for destino, (a, b) in mapa_octavos.items():

        partido = Partido.query.get(destino)

        p1 = Partido.query.get(a)
        p2 = Partido.query.get(b)

        print(
            f"Octavos {destino}: "
            f"P{a}={p1.equipo_local} vs {p1.equipo_visitante} "
            f"({p1.goles_local}-{p1.goles_visitante}) | "
            f"P{b}={p2.equipo_local} vs {p2.equipo_visitante} "
            f"({p2.goles_local}-{p2.goles_visitante})"
        )

        partido.equipo_local = ganador(p1)
        partido.equipo_visitante = ganador(p2)

    # ===== CUARTOS =====

    mapa_cuartos = {
        97: (89, 90),
        98: (91, 92),
        99: (93, 94),
        100: (95, 96)
    }

    for destino, (a, b) in mapa_cuartos.items():

        partido = Partido.query.get(destino)

        p1 = Partido.query.get(a)
        p2 = Partido.query.get(b)

        partido.equipo_local = ganador(p1)
        partido.equipo_visitante = ganador(p2)

    # ===== SEMIFINALES =====

    mapa_semis = {
        101: (97, 98),
        102: (99, 100)
    }

    for destino, (a, b) in mapa_semis.items():

        partido = Partido.query.get(destino)

        p1 = Partido.query.get(a)
        p2 = Partido.query.get(b)

        partido.equipo_local = ganador(p1)
        partido.equipo_visitante = ganador(p2)

    # ===== TERCER PUESTO =====

    tercer = Partido.query.get(103)

    semi1 = Partido.query.get(101)
    semi2 = Partido.query.get(102)

    tercer.equipo_local = perdedor(semi1)
    tercer.equipo_visitante = perdedor(semi2)

    # ===== FINAL =====

    final = Partido.query.get(104)

    final.equipo_local = ganador(semi1)
    final.equipo_visitante = ganador(semi2)

    db.session.commit()

    

def clean_team_name(nombre):
    return nombre.replace("🇲🇽", "").replace("🇧🇷", "").strip()

def bandera(pais):
    mapa_banderas = {
        "méxico": "mx.png", "mexico": "mx.png",
        "sudáfrica": "za.png", "sudafrica": "za.png",
        "república de corea": "kr.png", "republica de corea": "kr.png", "corea del sur": "kr.png",
        "república checa": "cz.png", "republica checa": "cz.png",
        
        "canadá": "ca.png", "canada": "ca.png",
        "bosnia y herzegovina": "ba.png", "bosnia": "ba.png",
        "catar": "qa.png",
        "suiza": "ch.png",
        
        "brasil": "br.png",
        "marruecos": "ma.png",
        "haití": "ht.png", "haiti": "ht.png",
        "escocia": "gb-sct.png",
        
        "estados unidos": "us.png",
        "paraguay": "py.png",
        "australia": "au.png",
        "turquía": "tr.png", "turquia": "tr.png",
        
        "alemania": "de.png",
        "curazao": "cw.png",
        "costa de marfil": "ci.png",
        "ecuador": "ec.png",
        
        "países bajos": "nl.png", "paises bajos": "nl.png",
        "japón": "jp.png", "japon": "jp.png",
        "suecia": "se.png",
        "túnez": "tn.png", "tunez": "tn.png",
        
        "bélgica": "be.png", "belgica": "be.png",
        "egipto": "eg.png",
        "irán": "ir.png", "iran": "ir.png",
        "nueva zelanda": "nz.png",
        
        "españa": "es.png", "espana": "es.png",
        "cabo verde": "cv.png",
        "arabia saudí": "sa.png", "arabia saudita": "sa.png",
        "uruguay": "uy.png",
        
        "francia": "fr.png",
        "senegal": "sn.png",
        "irak": "iq.png",
        "noruega": "no.png",
        
        "argentina": "ar.png",
        "argelia": "dz.png",
        "austria": "at.png",
        "jordania": "jo.png",
        
        "portugal": "pt.png",
        "rd congo": "cd.png", "congo": "cd.png",
        "uzbekistán": "uz.png", "uzbekistan": "uz.png",
        "colombia": "co.png",
        
        "inglaterra": "gb-eng.png",
        "croacia": "hr.png",
        "ghana": "gh.png",
        "panamá": "pa.png", "panama": "pa.png"
    }
    
    pais_limpio = pais.lower().strip()
    
    # Si contiene palabras de fases eliminatorias muestra la bandera por definir
    if any(p in pais_limpio for p in ["partido", "ganador", "perdedor", "local", "visitante"]):
        return "tbd.png"
        
    for nombre, archivo in mapa_banderas.items():
        if nombre in pais_limpio:
            return archivo
            
    return "default.png"  # Por si acaso no encuentra coincidencia # Imagen de respaldo si no encuentra coincidencia




# Esto le avisa a Jinja que puede usar la función bandera() dentro de cualquier {{ }}
@app.context_processor
def inject_bandera():
    return dict(bandera=bandera)

def actualizar_llaves_fase_final():
    # 1. Diccionario para acumular puntos y goles de la fase de grupos
    stats = {}
    
    # Traemos todos los partidos de los 12 grupos (A al L)
    grupos_validos = [chr(i) for i in range(65, 77)] # ['A', 'B', 'C', ..., 'L']
    partidos_grupo = Partido.query.filter(Partido.grupo.in_(grupos_validos)).all()
    
    for p in partidos_grupo:
        # Inicializar estadísticas de los equipos si no existen
        if p.equipo_local not in stats:
            stats[p.equipo_local] = {"pts": 0, "dg": 0, "gf": 0, "grupo": p.grupo}
        if p.equipo_visitante not in stats:
            stats[p.equipo_visitante] = {"pts": 0, "dg": 0, "gf": 0, "grupo": p.grupo}
            
        # Si el admin ya digitó un marcador real, sumamos estadísticas
        if p.goles_local is not None and p.goles_visitante is not None:
            gl, gv = p.goles_local, p.goles_visitante
            stats[p.equipo_local]["gf"] += gl
            stats[p.equipo_visitante]["gf"] += gv
            stats[p.equipo_local]["dg"] += (gl - gv)
            stats[p.equipo_visitante]["dg"] += (gv - gl)
            
            if gl > gv:
                stats[p.equipo_local]["pts"] += 3
            elif gv > gl:
                stats[p.equipo_visitante]["pts"] += 3
            else:
                stats[p.equipo_local]["pts"] += 1
                stats[p.equipo_visitante]["pts"] += 1

    # 2. Agrupar los equipos por su respectivo grupo
    grupos = {g: [] for g in grupos_validos}
    for equipo, data in stats.items():
        if data["grupo"] in grupos:
            grupos[data["grupo"]].append({
                "nombre": equipo, "pts": data["pts"], "dg": data["dg"], "gf": data["gf"]
            })
            
    # 3. Ordenar cada grupo según los criterios de desempate de FIFA
    posiciones = {}
    mejores_terceros = []
    
    for g, equipos in grupos.items():
        # Ordena por Puntos, luego Diferencia de Goles, luego Goles a Favor
        equipos.sort(key=lambda x: (x["pts"], x["dg"], x["gf"]), reverse=True)
        posiciones[g] = equipos
        
        # El que quede de 3º en su grupo entra a la tómbola de mejores terceros
        if len(equipos) >= 3:
            mejores_terceros.append(equipos[2])

    # Ordenamos la tabla general de los terceros (Clasifican los 8 mejores)
    mejores_terceros.sort(key=lambda x: (x["pts"], x["dg"], x["gf"]), reverse=True)

    # Helper interno para extraer el nombre del equipo de forma segura
    def obtener_team(llave):
        try:
            if "TOP" in llave: # Ejemplo: "3_TOP1" (El mejor tercero de todos)
                idx = int(llave.split("TOP")[1]) - 1
                return mejores_terceros[idx]["nombre"] if idx < len(mejores_terceros) else f"3º Mejor Tercero {idx+1}"
            else:
                pos = int(llave[0]) - 1 # '1' -> 0, '2' -> 1
                letra_grupo = llave[1].upper()
                return posiciones[letra_grupo][pos]["nombre"] if pos < len(posiciones[letra_grupo]) else f"{llave[0]}º Grupo {letra_grupo}"
        except Exception:
            return "Por Definir"

    # =========================================================================
    # 4. MAPA DE DIECISEISAVOS DE FINAL (Partidos del 73 al 104)
    # Aquí asocias el ID del partido en tu base de datos con las posiciones fijas.
    # =========================================================================
    MAPA_DIECISEISAVOS = {
        73: ("1A", "3_TOP1"),  # El partido 73 lo juega el 1º del Grupo A vs el 1º Mejor Tercero
        74: ("2A", "2B"),      # El partido 74 lo juega el 2º del Grupo A vs el 2º del Grupo B
        75: ("1B", "3_TOP2"),  # Ajusta estos IDs y combinaciones según tu fixture real
        76: ("1C", "3_TOP3"),
        # ... Sigue agregando tus IDs de partidos hasta el 104 aquí ...
    }

    # Actualizar Dieciseisavos en la Base de Datos
    for p_id, (local_key, visitante_key) in MAPA_DIECISEISAVOS.items():
        partido_fase = db.session.get(Partido, p_id)
        if partido_fase:
            partido_fase.equipo_local = obtener_team(local_key)
            partido_fase.equipo_visitante = obtener_team(visitante_key)

    # =========================================================================
    # 5. MAPA DE SIGUIENTES FASES (Octavos, Cuartos, Semis, Final)
    # Se alimentan de los ganadores de los partidos anteriores
    # =========================================================================
    MAPA_PROGRESIVO = {
        105: (73, 74),  # El Partido 105 (Octavos) se juega entre Ganador del 73 vs Ganador del 74
        106: (75, 76),  # El Partido 106 se juega entre Ganador del 75 vs Ganador del 76
        # ... Sigue vinculando las llaves hasta la gran final ...
    }

    for p_id, (id_local_ant, id_visitante_ant) in MAPA_PROGRESIVO.items():
        partido_fase = db.session.get(Partido, p_id)
        if partido_fase:
            p_local_anterior = db.session.get(Partido, id_local_ant)
            p_vis_anterior = db.session.get(Partido, id_visitante_ant)
            
            # Si el partido anterior ya se jugó, avanza el ganador real
            if p_local_anterior and p_local_anterior.goles_local is not None and p_local_anterior.goles_visitante is not None:
                partido_fase.equipo_local = p_local_anterior.equipo_local if p_local_anterior.goles_local > p_local_anterior.goles_visitante else p_local_anterior.equipo_visitante
            else:
                partido_fase.equipo_local = f"Ganador {id_local_ant}"

            if p_vis_anterior and p_vis_anterior.goles_local is not None and p_vis_anterior.goles_visitante is not None:
                partido_fase.equipo_visitante = p_vis_anterior.equipo_local if p_vis_anterior.goles_local > p_vis_anterior.goles_visitante else p_vis_anterior.equipo_visitante
            else:
                partido_fase.equipo_visitante = f"Ganador {id_visitante_ant}"

    db.session.commit()


# LOGIN
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


# ==========================
# MODELOS
# ==========================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    correo = db.Column(db.String(150), unique=True)
    nombre_usuario = db.Column(db.String(50), unique=True, nullable=False) # <--- ESTO ES LO NUEVO
    password = db.Column(db.String(255))
    puntos = db.Column(db.Integer, default=0)
    admin = db.Column(db.Boolean, default=False)

    
    

class Partido(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    grupo = db.Column(db.String(10))
    fecha = db.Column(db.String(50))

    equipo_local = db.Column(db.String(100), nullable=False)
    equipo_visitante = db.Column(db.String(100), nullable=False)

    bandera_local = db.Column(db.String(200))
    bandera_visitante = db.Column(db.String(200))

    goles_local = db.Column(db.Integer)
    goles_visitante = db.Column(db.Integer)

    # NUEVO
    penales_local = db.Column(db.Integer)
    penales_visitante = db.Column(db.Integer)

    # partido siguiente
    siguiente_partido = db.Column(db.Integer)

    # posición en el siguiente partido
    posicion_siguiente = db.Column(db.String(10))

class Pronostico(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id')
    )

    partido_id = db.Column(
        db.Integer,
        db.ForeignKey('partido.id')
    )

    pred_local = db.Column(
        db.Integer
    )

    pred_visitante = db.Column(
        db.Integer
    )

    # NUEVO
    pred_penales_local = db.Column(
        db.Integer
    )

    pred_penales_visitante = db.Column(
        db.Integer
    )

    usuario = db.relationship(
        "User",
        backref="pronosticos"
    )

    partido = db.relationship(
        "Partido",
        backref="pronosticos"
    )

class PronosticoEliminatoria(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )

    partido_id = db.Column(
        db.Integer,
        db.ForeignKey("partido.id")
    )

    goles_local = db.Column(db.Integer)
    goles_visitante = db.Column(db.Integer)

    penales_local = db.Column(db.Integer)
    penales_visitante = db.Column(db.Integer)


class Configuracion(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    grupos_abiertos = db.Column(
        db.Boolean,
        default=True
    )

    llaves_abiertas = db.Column(
        db.Boolean,
        default=True
    )
   

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def crear_admin_inicial():
    email_admin = "jony@empresa.com"
    admin_encontrado = User.query.filter_by(correo=email_admin).first()
    
    if not admin_encontrado:
        password_segura = generate_password_hash("123456") 
        nuevo_admin = User(
            correo=email_admin,
            nombre_usuario="AdminJony",
            password=password_segura,
            admin=True
        )
        db.session.add(nuevo_admin)
        db.session.commit()
        print("Administrador creado.")

        


# ==========================
# HOME
# ==========================

@app.route("/")
def inicio():
    return render_template("index.html")


# ==========================
# REGISTRO
# ==========================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # 1. Capturamos los datos del formulario
        correo = request.form.get("correo").lower()
        nombre_usuario = request.form.get("nombre_usuario") # <--- AQUÍ ESTABA EL ERROR (Faltaba capturarlo)
        password = request.form.get("password")

        # 2. Verificamos si el usuario o correo ya existen
        usuario_existente = User.query.filter_by(correo=correo).first()
        nombre_existente = User.query.filter_by(nombre_usuario=nombre_usuario).first()
        
        if usuario_existente or nombre_existente:
            flash("El correo o el nombre de usuario ya están en uso.")
            return redirect(url_for("register"))

        # 3. Encriptamos y creamos el nuevo usuario con el nombre
        password_hash = generate_password_hash(password)
        
        nuevo_usuario = User(
            correo=correo, 
            nombre_usuario=nombre_usuario, # <--- AQUÍ ESTABA EL ERROR (Faltaba asignarlo)
            password=password_hash
        )
        
        db.session.add(nuevo_usuario)
        db.session.commit()

        flash("Registro exitoso. Ahora puedes iniciar sesión.")
        return redirect(url_for("login"))

    return render_template("register.html")
# ==========================
# LOGIN
# ==========================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form.get("correo").lower() # .lower() ayuda a evitar errores por mayúsculas
        password = request.form.get("password")

        # Buscamos al usuario por correo
        usuario = User.query.filter_by(correo=correo).first()

        # Verificamos si existe y si la contraseña es correcta
        if usuario and check_password_hash(usuario.password, password):
            login_user(usuario)
            return redirect(url_for("dashboard")) # Redirige al dashboard si es exitoso
        
        # Si algo falló, enviamos el mensaje de error
        flash("Correo o contraseña incorrectos")

    return render_template("login.html")


# ==========================
# DASHBOARD
# ==========================

from datetime import datetime

# ==========================
# DASHBOARD
# ==========================

from datetime import datetime

@app.route("/dashboard")
@login_required
def dashboard():

    # ==========================
    # PARTIDOS
    # ==========================

    partidos = Partido.query.all()

    for p in partidos:
        try:
            fecha_dt = datetime.strptime(
                p.fecha,
                '%d/%m/%Y'
            )

            p.fecha_iso = fecha_dt.strftime(
                '%Y-%m-%dT00:00:00'
            )

        except:
            p.fecha_iso = ""

    # ==========================
    # CIERRE GLOBAL PRONÓSTICOS
    # ==========================

    cierre_pronosticos = datetime(
        2026, 6, 11, 15, 0, 0
    )

    pronosticos_cerrados = (
        datetime.now() >= cierre_pronosticos
    )

    # ==========================
    # PRONÓSTICOS DEL USUARIO
    # ==========================

    pronosticos_usuario = Pronostico.query.filter_by(
        usuario_id=current_user.id
    ).all()

    pronosticados = [
        p.partido_id
        for p in pronosticos_usuario
    ]

    partidos_pronosticados = []
    partidos_pendientes = []

    for partido in partidos:

        if partido.id in pronosticados:

            partidos_pronosticados.append(
                partido
            )

        else:

            partidos_pendientes.append(
                partido
            )

    # ==========================
    # DICCIONARIO PRONÓSTICOS
    # ==========================

    pronosticos_dict = {}

    for p in pronosticos_usuario:

        pronosticos_dict[
            p.partido_id
        ] = p

    # ==========================
    # ESTADÍSTICAS
    # ==========================

    mis_pronosticos = Pronostico.query.filter_by(
        usuario_id=current_user.id
    ).count()

    ranking = User.query.order_by(
        User.puntos.desc()
    ).all()

    todos_pronosticos = Pronostico.query.all()

    # ==========================
    # DETALLE DE PUNTOS
    # ==========================

    detalles_puntos = {}

    for pronostico in pronosticos_usuario:

        partido = Partido.query.get(
            pronostico.partido_id
        )

        if (
            partido
            and partido.goles_local is not None
            and partido.goles_visitante is not None
        ):

            detalle = []
            total = 0

            # Marcador exacto
            if (
                pronostico.pred_local == partido.goles_local
                and
                pronostico.pred_visitante == partido.goles_visitante
            ):
                detalle.append(
                    "🎯 Marcador exacto (+5)"
                )
                total += 5

            # Goles local
            if (
                pronostico.pred_local
                == partido.goles_local
            ):
                detalle.append(
                    "⚽ Goles local correctos (+2)"
                )
                total += 2

            # Goles visitante
            if (
                pronostico.pred_visitante
                == partido.goles_visitante
            ):
                detalle.append(
                    "⚽ Goles visitante correctos (+2)"
                )
                total += 2

            resultado_real = (
                1 if partido.goles_local > partido.goles_visitante
                else -1 if partido.goles_local < partido.goles_visitante
                else 0
            )

            resultado_pronostico = (
                1 if pronostico.pred_local > pronostico.pred_visitante
                else -1 if pronostico.pred_local < pronostico.pred_visitante
                else 0
            )

            if resultado_real == resultado_pronostico:
                detalle.append(
                    "🏆 Equipo ganador o empate (+3)"
                )
                total += 3

            detalles_puntos[
                partido.id
            ] = {
                "detalle": detalle,
                "total": total
            }

    # ==========================
    # TEMPLATE
    # ==========================

    return render_template(

        "dashboard.html",

        ranking=ranking,
        usuario=current_user,

        partidos=partidos,

        partidos_pronosticados=
            partidos_pronosticados,

        partidos_pendientes=
            partidos_pendientes,

        pronosticados=
            pronosticados,

        pronosticos_dict=
            pronosticos_dict,

        puntos=current_user.puntos,

        mis_pronosticos=
            mis_pronosticos,

        todos_pronosticos=
            todos_pronosticos,

        pronosticos_cerrados=
            pronosticos_cerrados,

        detalles_puntos=
            detalles_puntos,

        bandera=bandera

    )

# CREAR PARTIDOS
# ==========================

@app.route("/crear_partidos")
def crear_partidos():

    partidos = [
        # ==========================================
        # FASE DE GRUPOS (72 Partidos)
        # ==========================================
        
        # ===== GRUPO A =====
        ("A", "11/06/2026 - 2:00 p.m.", "México", "Sudáfrica"),
        ("A", "11/06/2026 - 9:00 p.m.", "República de Corea", "República Checa"),
        ("A", "18/06/2026 - 11:00 a.m.", "República Checa", "Sudáfrica"),
        ("A", "18/06/2026 - 8:00 p.m.", "México", "República de Corea"),
        ("A", "24/06/2026 - 8:00 p.m.", "República Checa", "México"),
        ("A", "24/06/2026 - 8:00 p.m.", "Sudáfrica", "República de Corea"),

        # ===== GRUPO B =====
        ("B", "12/06/2026 - 2:00 p.m.", "Canadá", "Bosnia y Herzegovina"),
        ("B", "13/06/2026 - 2:00 p.m.", "Catar", "Suiza"),
        ("B", "18/06/2026 - 2:00 p.m.", "Suiza", "Bosnia y Herzegovina"),
        ("B", "18/06/2026 - 5:00 p.m.", "Canadá", "Catar"),
        ("B", "24/06/2026 - 2:00 p.m.", "Suiza", "Canadá"),
        ("B", "24/06/2026 - 2:00 p.m.", "Bosnia y Herzegovina", "Catar"),

        # ===== GRUPO C =====
        ("C", "13/06/2026 - 5:00 p.m.", "Brasil", "Marruecos"),
        ("C", "13/06/2026 - 8:00 p.m.", "Haití", "Escocia"),
        ("C", "19/06/2026 - 5:00 p.m.", "Escocia", "Marruecos"),
        ("C", "19/06/2026 - 8:00 p.m.", "Brasil", "Haití"),
        ("C", "24/06/2026 - 5:00 p.m.", "Escocia", "Brasil"),
        ("C", "24/06/2026 - 5:00 p.m.", "Marruecos", "Haití"),

        # ===== GRUPO D =====
        ("D", "12/06/2026 - 8:00 p.m.", "Estados Unidos", "Paraguay"),
        ("D", "13/06/2026 - 11:00 p.m.", "Australia", "Turquía"),
        ("D", "19/06/2026 - 2:00 p.m.", "Estados Unidos", "Australia"),
        ("D", "19/06/2026 - 11:00 p.m.", "Turquía", "Paraguay"),
        ("D", "25/06/2026 - 9:00 p.m.", "Turquía", "Estados Unidos"),
        ("D", "25/06/2026 - 9:00 p.m.", "Paraguay", "Australia"),

        # ===== GRUPO E =====
        ("E", "14/06/2026 - 12:00 p.m.", "Alemania", "Curazao"),
        ("E", "14/06/2026 - 6:00 p.m.", "Costa de Marfil", "Ecuador"),
        ("E", "20/06/2026 - 3:00 p.m.", "Alemania", "Costa de Marfil"),
        ("E", "20/06/2026 - 9:00 p.m.", "Ecuador", "Curazao"),
        ("E", "25/06/2026 - 3:00 p.m.", "Curazao", "Costa de Marfil"),
        ("E", "25/06/2026 - 3:00 p.m.", "Ecuador", "Alemania"),

        # ===== GRUPO F =====
        ("F", "14/06/2026 - 3:00 p.m.", "Países Bajos", "Japón"),
        ("F", "14/06/2026 - 9:00 p.m.", "Suecia", "Túnez"),
        ("F", "20/06/2026 - 12:00 p.m.", "Países Bajos", "Suecia"),
        ("F", "20/06/2026 - 11:00 p.m.", "Túnez", "Japón"),
        ("F", "25/06/2026 - 6:00 p.m.", "Japón", "Suecia"),
        ("F", "25/06/2026 - 6:00 p.m.", "Túnez", "Países Bajos"),

        # ===== GRUPO G =====
        ("G", "15/06/2026 - 2:00 p.m.", "Bélgica", "Egipto"),
        ("G", "15/06/2026 - 8:00 p.m.", "Irán", "Nueva Zelanda"),
        ("G", "21/06/2026 - 2:00 p.m.", "Bélgica", "Irán"),
        ("G", "21/06/2026 - 8:00 p.m.", "Nueva Zelanda", "Egipto"),
        ("G", "26/06/2026 - 10:00 p.m.", "Egipto", "Irán"),
        ("G", "26/06/2026 - 10:00 p.m.", "Nueva Zelanda", "Bélgica"),

        # ===== GRUPO H =====
        ("H", "15/06/2026 - 11:00 a.m.", "España", "Cabo Verde"),
        ("H", "15/06/2026 - 5:00 p.m.", "Arabia Saudí", "Uruguay"),
        ("H", "21/06/2026 - 11:00 a.m.", "España", "Arabia Saudí"),
        ("H", "21/06/2026 - 5:00 p.m.", "Uruguay", "Cabo Verde"),
        ("H", "26/06/2026 - 7:00 p.m.", "Cabo Verde", "Arabia Saudí"),
        ("H", "26/06/2026 - 7:00 p.m.", "Uruguay", "España"),

        # ===== GRUPO I =====
        ("I", "16/06/2026 - 2:00 p.m.", "Francia", "Senegal"),
        ("I", "16/06/2026 - 5:00 p.m.", "Irak", "Noruega"),
        ("I", "22/06/2026 - 4:00 p.m.", "Francia", "Irak"),
        ("I", "22/06/2026 - 7:00 p.m.", "Noruega", "Senegal"),
        ("I", "26/06/2026 - 2:00 p.m.", "Noruega", "Francia"),
        ("I", "26/06/2026 - 2:00 p.m.", "Senegal", "Irak"),

        # ===== GRUPO J =====
        ("J", "16/06/2026 - 8:00 p.m.", "Argentina", "Argelia"),
        ("J", "16/06/2026 - 11:00 p.m.", "Austria", "Jordania"),
        ("J", "22/06/2026 - 12:00 p.m.", "Argentina", "Austria"),
        ("J", "22/06/2026 - 10:00 p.m.", "Jordania", "Argelia"),
        ("J", "27/06/2026 - 9:00 p.m.", "Argelia", "Austria"),
        ("J", "27/06/2026 - 9:00 p.m.", "Jordania", "Argentina"),

        # ===== GRUPO K =====
        ("K", "17/06/2026 - 12:00 p.m.", "Portugal", "RD Congo"),
        ("K", "17/06/2026 - 9:00 p.m.", "Uzbekistán", "Colombia"),
        ("K", "23/06/2026 - 12:00 p.m.", "Portugal", "Uzbekistán"),
        ("K", "23/06/2026 - 9:00 p.m.", "Colombia", "RD Congo"),
        ("K", "27/06/2026 - 6:30 p.m.", "Colombia", "Portugal"),
        ("K", "27/06/2026 - 6:30 p.m.", "RD Congo", "Uzbekistán"),

        # ===== GRUPO L =====
        ("L", "17/06/2026 - 3:00 p.m.", "Inglaterra", "Croacia"),
        ("L", "17/06/2026 - 6:00 p.m.", "Ghana", "Panamá"),
        ("L", "23/06/2026 - 3:00 p.m.", "Inglaterra", "Ghana"),
        ("L", "23/06/2026 - 6:00 p.m.", "Panamá", "Croacia"),
        ("L", "27/06/2026 - 4:00 p.m.", "Panamá", "Inglaterra"),
        ("L", "27/06/2026 - 4:00 p.m.", "Croacia", "Ghana"),

        # ==========================================
        # DIECISEISAVOS DE FINAL (Ronda de 32)
        # ==========================================
        ("16avos", "28/06/2026 - 2:00 p.m.", "1A", "2B"),
("16avos", "29/06/2026 - 2:00 p.m.", "1C", "2D"),
("16avos", "29/06/2026 - 5:00 p.m.", "1E", "2F"),
("16avos", "29/06/2026 - 8:00 p.m.", "1G", "2H"),

("16avos", "30/06/2026 - 2:00 p.m.", "1I", "2J"),
("16avos", "30/06/2026 - 5:00 p.m.", "1K", "2L"),

("16avos", "30/06/2026 - 8:00 p.m.", "1B", "2A"),
("16avos", "01/07/2026 - 2:00 p.m.", "1D", "2C"),

("16avos", "01/07/2026 - 5:00 p.m.", "1F", "2E"),
("16avos", "01/07/2026 - 8:00 p.m.", "1H", "2G"),

("16avos", "02/07/2026 - 2:00 p.m.", "1J", "2I"),
("16avos", "02/07/2026 - 5:00 p.m.", "1L", "2K"),

        # ==========================================
        # OCTAVOS DE FINAL
        # ==========================================
        ("Octavos", "04/07/2026 - 2:00 p.m.", "Ganador Partido 73", "Ganador Partido 74"),
        ("Octavos", "04/07/2026 - 6:00 p.m.", "Ganador Partido 75", "Ganador Partido 76"),
        ("Octavos", "05/07/2026 - 2:00 p.m.", "Ganador Partido 77", "Ganador Partido 78"),
        ("Octavos", "05/07/2026 - 8:00 p.m.", "Ganador Partido 79", "Ganador Partido 80"),
        ("Octavos", "06/07/2026 - 2:00 p.m.", "Ganador Partido 81", "Ganador Partido 82"),
        ("Octavos", "06/07/2026 - 8:00 p.m.", "Ganador Partido 83", "Ganador Partido 84"),
        ("Octavos", "07/07/2026 - 2:00 p.m.", "Ganador Partido 85", "Ganador Partido 86"),
        ("Octavos", "07/07/2026 - 8:00 p.m.", "Ganador Partido 87", "Ganador Partido 88"),

        # ==========================================
        # CUARTOS DE FINAL
        # ==========================================
        ("Cuartos", "09/07/2026 - 2:00 p.m.", "Ganador Partido 89", "Ganador Partido 90"),
        ("Cuartos", "10/07/2026 - 2:00 p.m.", "Ganador Partido 91", "Ganador Partido 92"),
        ("Cuartos", "11/07/2026 - 2:00 p.m.", "Ganador Partido 93", "Ganador Partido 94"),
        ("Cuartos", "11/07/2026 - 8:00 p.m.", "Ganador Partido 95", "Ganador Partido 96"),

        # ==========================================
        # SEMIFINALES
        # ==========================================
        ("Semis", "14/07/2026 - 8:00 p.m.", "Ganador Partido 97", "Ganador Partido 98"),
        ("Semis", "15/07/2026 - 8:00 p.m.", "Ganador Partido 99", "Ganador Partido 100"),

        # ==========================================
        # TERCER PUESTO Y FINAL
        # ==========================================
        ("3er Puesto", "18/07/2026 - 7:00 p.m.", "Perdedor Partido 101", "Perdedor Partido 102"),
        ("Final", "19/07/2026 - 2:00 p.m.", "Ganador Partido 101", "Ganador Partido 102")
    ]

    # Insertar partidos evitando duplicidad
    for grupo, fecha, local, visitante in partidos:
        existe = Partido.query.filter_by(
            equipo_local=local,
            equipo_visitante=visitante
        ).first()

        if not existe:
            db.session.add(
                Partido(
                    grupo=grupo,
                    fecha=fecha,
                    equipo_local=local,
                    equipo_visitante=visitante
                )
            )

    db.session.commit()
    return f"¡Calendario oficial cargado con éxito! Total partidos: {len(partidos)}"





# ==========================
# VER PARTIDOS
# ==========================

@app.route("/ver_partidos")
def ver_partidos():

    partidos = Partido.query.all()

    texto = ""

    for p in partidos:

        texto += (
            f"{p.id} - "
            f"{p.equipo_local} vs "
            f"{p.equipo_visitante}<br>"
        )

    return texto

# ==========================
# TEST PUNTOS
# ==========================

@app.route("/test_puntos")
def test_puntos():

    usuario = User.query.first()

    if usuario:
        return f"Puntos: {usuario.puntos}"

    return "No hay usuarios"
# ==========================
# PRONOSTICOS
# ==========================


# ==========================
# VER PRONOSTICOS
# ==========================

@app.route("/mis_pronosticos")
@login_required
def mis_pronosticos():

    pronosticos = Pronostico.query.filter_by(
        usuario_id=current_user.id
    ).all()

    return render_template(
        "mis_pronosticos.html",
        pronosticos=pronosticos
    )


# ==========================
# LOGOUT
# ==========================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(
        url_for("login")
    )

  

# ==========================
# CREAR BASE DE DATOS
# ==========================

with app.app_context():

    db.create_all()


    


@app.route("/test")
def test():

    cantidad = Partido.query.count()

    return f"Partidos en BD: {cantidad}" 


@app.route("/db")
def db_info():
    return app.config["SQLALCHEMY_DATABASE_URI"]

@app.route("/debug_partidos")
def debug_partidos():

    partidos = Partido.query.all()

    resultado = f"Cantidad: {len(partidos)}<br><br>"

    for p in partidos:
        resultado += f"{p.id} - {p.equipo_local} vs {p.equipo_visitante}<br>"

    return resultado


@app.route("/reset_mundial")
def reset_mundial():

    partidos = [

        ("A","11/06/2026","🇲🇽 México","🇿🇦 Sudáfrica"),
        ("A","11/06/2026","🇰🇷 Corea del Sur","🇨🇿 República Checa"),
        ("B","12/06/2026","🇨🇦 Canadá","🇧🇦 Bosnia"),
        ("D","12/06/2026","🇺🇸 Estados Unidos","🇵🇾 Paraguay"),
        ("C","13/06/2026","🇧🇷 Brasil","🇲🇦 Marruecos"),
        ("C","13/06/2026","🇭🇹 Haití","🏴 Escocia"),
        ("K","17/06/2026","🇵🇹 Portugal","🇨🇴 Colombia"),
        ("J","16/06/2026","🇦🇷 Argentina","🇩🇿 Argelia"),
        ("L","17/06/2026","🏴 Inglaterra","🇭🇷 Croacia")

    ]

    for grupo, fecha, local, visitante in partidos:

        existe = Partido.query.filter_by(
            equipo_local=local,
            equipo_visitante=visitante
        ).first()

        if not existe:

            db.session.add(
                Partido(
                    grupo=grupo,
                    fecha=fecha,
                    equipo_local=local,
                    equipo_visitante=visitante
                )
            )

    db.session.commit()

    return "Mundial restaurado correctamente"


 # Asegúrate de tener jsonify importado arriba en tu app.py

@app.route("/resultado/<int:partido_id>", methods=["POST"])
@login_required
def resultado(partido_id):

    if not current_user.admin:
        return jsonify({
            "success": False,
            "message": "Acceso denegado"
        }), 403

    partido = db.session.get(Partido, partido_id)

    if not partido:
        return jsonify({
            "success": False,
            "message": "Partido no encontrado"
        }), 404

    data = request.get_json() or {}

    try:
        gl = data.get("goles_local")
        gv = data.get("goles_visitante")
        pl = data.get("penales_local")
        pv = data.get("penales_visitante")

        partido.goles_local = int(gl) if gl is not None and str(gl).strip() != "" else None
        partido.goles_visitante = int(gv) if gv is not None and str(gv).strip() != "" else None
        partido.penales_local = int(pl) if pl is not None and str(pl).strip() != "" else None
        partido.penales_visitante = int(pv) if pv is not None and str(pv).strip() != "" else None

        # Guardar resultado
        db.session.commit()

        # Actualizar estructura del torneo y puntos
        print("ACTUALIZANDO 16AVOS...")
        actualizar_16avos()

        print("ACTUALIZANDO FASES FINALES...")
        actualizar_fases_finales()

        # Recalcular puntos automáticamente
        recalcular_puntos()

        # Commit final por cualquier cambio realizado por las funciones de recálculo
        db.session.commit()

        return jsonify({
            "success": True
        })

    except Exception as e:
        db.session.rollback()
        print("ERROR:", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
    
@app.route("/ranking")
@login_required
def ranking():

    usuarios = User.query.all()

    texto = f"Usuarios encontrados: {len(usuarios)}<br><br>"

    for u in usuarios:
        texto += f"{u.correo} - {u.puntos} puntos<br>"

    return texto

@app.route("/reset_pronosticos")
def reset_pronosticos():

    # BORRAR TODOS LOS PRONOSTICOS
    Pronostico.query.delete()

    # RESETEAR PUNTOS
    usuarios = User.query.all()

    for usuario in usuarios:
        usuario.puntos = 0

    db.session.commit()

    return "✅ Todos los pronósticos y puntos fueron eliminados"

@app.route("/admin")
@login_required
def admin_panel():

    if not current_user.admin:
        return "Acceso denegado"

    usuarios = User.query.all()

    partidos = Partido.query.all()

    config = Configuracion.query.first()

    return render_template(
        "admin.html",
        usuarios=usuarios,
        partidos=partidos,
        config=config
    )
# =====


@app.route("/recalcular")
@login_required
def recalcular():

    if not current_user.admin:
        return "Acceso denegado"

    recalcular_puntos()

    return "✅ Puntos recalculados correctamente"

@app.route("/debug_users")
def debug_users():

    usuarios = User.query.all()

    texto = ""

    for u in usuarios:

        texto += f"""
        ID: {u.id}<br>
        Correo: {u.correo}<br>
        Puntos: {u.puntos}<br>
        Admin: {u.admin}<br>
        <hr>
        """

    return texto

@app.route("/limpiar_pronosticos")
def limpiar_pronosticos():

    pronosticos = Pronostico.query.all()

    eliminados = 0

    for p in pronosticos:

        usuario = User.query.get(p.usuario_id)

        if not usuario:

            db.session.delete(p)
            eliminados += 1

    db.session.commit()

    return f"Pronósticos eliminados: {eliminados}"

@app.route("/reset_total")
def reset_total():

    # BORRAR PRONOSTICOS
    Pronostico.query.delete()

    # RESETEAR PUNTOS
    usuarios = User.query.all()

    for usuario in usuarios:
        usuario.puntos = 0

    # BORRAR RESULTADOS OFICIALES
    partidos = Partido.query.all()

    for partido in partidos:

        partido.goles_local = None
        partido.goles_visitante = None

    db.session.commit()

    return "✅ Mundial reiniciado completamente"


@app.route("/grupos")
@login_required
def grupos():

    grupos_data = {}

    partidos = Partido.query.all()

    for partido in partidos:

        if partido.goles_local is None:
            continue

        grupo = partido.grupo

        if grupo not in grupos_data:
            grupos_data[grupo] = {}

        for equipo in [
            partido.equipo_local,
            partido.equipo_visitante
        ]:

            if equipo not in grupos_data[grupo]:

                grupos_data[grupo][equipo] = {
                    "pj": 0,
                    "pts": 0,
                    "gf": 0,
                    "gc": 0,
                    "dg": 0
                }

        local = grupos_data[grupo][partido.equipo_local]
        visitante = grupos_data[grupo][partido.equipo_visitante]

        local["pj"] += 1
        visitante["pj"] += 1

        local["gf"] += partido.goles_local
        local["gc"] += partido.goles_visitante

        visitante["gf"] += partido.goles_visitante
        visitante["gc"] += partido.goles_local

        if partido.goles_local > partido.goles_visitante:

            local["pts"] += 3

        elif partido.goles_local < partido.goles_visitante:

            visitante["pts"] += 3

        else:

            local["pts"] += 1
            visitante["pts"] += 1

    # CALCULAR DIFERENCIA DE GOL
    for grupo in grupos_data:

        for equipo in grupos_data[grupo]:

            datos = grupos_data[grupo][equipo]

            datos["dg"] = (
                datos["gf"]
                - datos["gc"]
            )

    # ORDENAR SEGÚN REGLAS FIFA
    for grupo in grupos_data:

        grupos_data[grupo] = dict(
            sorted(
                grupos_data[grupo].items(),
                key=lambda x: (
                    x[1]["pts"],
                    x[1]["dg"],
                    x[1]["gf"]
                ),
                reverse=True
            )
        )

    return render_template(
        "grupos.html",
        grupos=grupos_data
    )
 
@app.route("/terceros")
@login_required
def terceros():

    grupos_data = {}

    partidos = Partido.query.all()

    for partido in partidos:

        if partido.goles_local is None:
            continue

        grupo = partido.grupo

        if grupo not in grupos_data:
            grupos_data[grupo] = {}

        for equipo in [
            partido.equipo_local,
            partido.equipo_visitante
        ]:

            if equipo not in grupos_data[grupo]:

                grupos_data[grupo][equipo] = {
                    "pj": 0,
                    "pts": 0,
                    "gf": 0,
                    "gc": 0,
                    "dg": 0
                }

        local = grupos_data[grupo][partido.equipo_local]
        visitante = grupos_data[grupo][partido.equipo_visitante]

        local["pj"] += 1
        visitante["pj"] += 1

        local["gf"] += partido.goles_local
        local["gc"] += partido.goles_visitante

        visitante["gf"] += partido.goles_visitante
        visitante["gc"] += partido.goles_local

        if partido.goles_local > partido.goles_visitante:
            local["pts"] += 3

        elif partido.goles_local < partido.goles_visitante:
            visitante["pts"] += 3

        else:
            local["pts"] += 1
            visitante["pts"] += 1

    terceros = []

    for grupo in grupos_data:

        equipos = []

        for nombre, datos in grupos_data[grupo].items():

            datos["dg"] = (
                datos["gf"] - datos["gc"]
            )

            equipos.append(
                (nombre, datos)
            )

        equipos.sort(
            key=lambda x: (
                x[1]["pts"],
                x[1]["dg"],
                x[1]["gf"]
            ),
            reverse=True
        )

        if len(equipos) >= 3:

            terceros.append({
                "grupo": grupo,
                "equipo": equipos[2][0],
                "pts": equipos[2][1]["pts"],
                "dg": equipos[2][1]["dg"],
                "gf": equipos[2][1]["gf"]
            })

    terceros.sort(
        key=lambda x: (
            x["pts"],
            x["dg"],
            x["gf"]
        ),
        reverse=True
    )

    terceros = obtener_mejores_terceros()

    return render_template(
        "terceros.html",
        terceros=terceros
    )



# 1. PRIMERO: Definimos la función auxiliar, que debe estar arriba
def obtener_clasificados_y_terceros(tipo='real', usuario_id=None):
    grupos_data = {}
    partidos = Partido.query.all()
    
    pronosticos_dict = {}
    if tipo == 'pronostico' and usuario_id:
        pronosticos = Pronostico.query.filter_by(usuario_id=usuario_id).all()
        pronosticos_dict = {p.partido_id: p for p in pronosticos}

    for partido in partidos:
        if not partido.grupo or len(partido.grupo) != 1:
            continue
            
        # Dependiendo del tipo de visualización, leemos goles de la BD o de Pronosticos
        g_local, g_visitante = None, None
        if tipo == 'pronostico' and partido.id in pronosticos_dict:
            pr = pronosticos_dict[partido.id]
            # CORREGIDO: Usamos los nombres de columnas de tu tabla Pronostico
            g_local = pr.pred_local          
            g_visitante = pr.pred_visitante  
        else:
            g_local = partido.goles_local
            g_visitante = partido.goles_visitante
            
        if g_local is None or g_visitante is None:
            continue

        grupo = partido.grupo
        if grupo not in grupos_data:
            grupos_data[grupo] = {}

        for equipo in [partido.equipo_local, partido.equipo_visitante]:
            if equipo not in grupos_data[grupo]:
                grupos_data[grupo][equipo] = {"pts": 0, "gf": 0, "gc": 0, "dg": 0}

        local = grupos_data[grupo][partido.equipo_local]
        visitante = grupos_data[grupo][partido.equipo_visitante]

        local["gf"] += g_local
        local["gc"] += g_visitante
        visitante["gf"] += g_visitante
        visitante["gc"] += g_local

        if g_local > g_visitante:
            local["pts"] += 3
        elif g_local < g_visitante:
            visitante["pts"] += 3
        else:
            local["pts"] += 1
            visitante["pts"] += 1

    clasificados = {}
    todos_los_terceros = []

    for grupo in grupos_data:
        equipos = []
        for nombre, datos in grupos_data[grupo].items():
            datos["dg"] = datos["gf"] - datos["gc"]
            equipos.append((nombre, datos))

        equipos.sort(key=lambda x: (x[1]["pts"], x[1]["dg"], x[1]["gf"]), reverse=True)

        clasificados[grupo] = {
            "primero": equipos[0][0] if len(equipos) > 0 else f"1ro Grupo {grupo}",
            "segundo": equipos[1][0] if len(equipos) > 1 else f"2do Grupo {grupo}"
        }

        if len(equipos) > 2:
            todos_los_terceros.append({
                "nombre": equipos[2][0],
                "grupo": grupo,
                "pts": equipos[2][1]["pts"],
                "dg": equipos[2][1]["dg"],
                "gf": equipos[2][1]["gf"]
            })

    todos_los_terceros.sort(key=lambda x: (x["pts"], x["dg"], x["gf"]), reverse=True)

    return clasificados, todos_los_terceros



def calcular_llaves_simuladas(tipo, usuario_id):

    print(f"DEBUG: Calculando llaves para usuario {usuario_id} tipo {tipo}")

    banderas = {}
    
    for partido in Partido.query.all():
        banderas[partido.equipo_local] = partido.bandera_local
        banderas[partido.equipo_visitante] = partido.bandera_visitante

    clasificados_grupos, lista_terceros = obtener_clasificados_y_terceros(
        tipo,
        usuario_id
    )

    todos_los_partidos = Partido.query.order_by(Partido.id).all()

    # Paso 1: Pronósticos de grupos y eliminatorias separados
    pronosticos_grupos = Pronostico.query.filter_by(
        usuario_id=usuario_id
    ).all()

    pronosticos_grupos_dict = {
        p.partido_id: p
        for p in pronosticos_grupos
    }

    pronosticos_eliminatoria = PronosticoEliminatoria.query.filter_by(
        usuario_id=usuario_id
    ).all()

    pronosticos_eliminatoria_dict = {
        p.partido_id: p
        for p in pronosticos_eliminatoria
    }

    ganadores_knockout = {}
    perdedores_knockout = {}
    partidos_procesados = []
    terceros_asignados = []

    # -------------------------
    # MAPA DE LLAVES
    # -------------------------

    octavos_map = {
        89: (73, 74),
        90: (75, 76),
        91: (77, 78),
        92: (79, 80),
        93: (81, 82),
        94: (83, 84),
        95: (85, 86),
        96: (87, 88),
    }

    cuartos_map = {
        97: (89, 90),
        98: (91, 92),
        99: (93, 94),
        100: (95, 96),
    }

    semis_map = {
        101: (97, 98),
        102: (99, 100),
    }

    final_map = {
        104: (101, 102),
    }

    tercer_puesto_map = {
        103: (101, 102),
    }

    # -------------------------
    # FUNCIONES AUXILIARES
    # -------------------------

    def buscar_mejor_tercero(texto_marcador):

        if not texto_marcador:
            return None

        if (
            "Mejor 3" not in str(texto_marcador)
            and "M3" not in str(texto_marcador)
        ):
            return None

        grupos_permitidos = [
            letra
            for letra in [
                "A","B","C","D","E","F",
                "G","H","I","J","K","L"
            ]
            if letra in str(texto_marcador)
        ]

        if not grupos_permitidos:
            grupos_permitidos = [
                "A","B","C","D","E","F",
                "G","H","I","J","K","L"
            ]

        for t in lista_terceros:

            if (
                t["grupo"] in grupos_permitidos
                and t["nombre"] not in terceros_asignados
            ):

                terceros_asignados.append(
                    t["nombre"]
                )

                return t["nombre"]

        return texto_marcador

    # -------------------------
    # RECORRIDO PRINCIPAL
    # -------------------------

    for p in todos_los_partidos:

        # Paso 2: Leer grupos y eliminatorias por separado para los goles
        if tipo == "pronostico":

            if p.id < 73:

                if p.id in pronosticos_grupos_dict:

                    g_local = pronosticos_grupos_dict[p.id].pred_local
                    g_visitante = pronosticos_grupos_dict[p.id].pred_visitante

                else:

                    g_local = None
                    g_visitante = None

            else:

                if p.id in pronosticos_eliminatoria_dict:

                    g_local = pronosticos_eliminatoria_dict[p.id].goles_local
                    g_visitante = pronosticos_eliminatoria_dict[p.id].goles_visitante

                else:

                    g_local = None
                    g_visitante = None

        else:

            g_local = p.goles_local
            g_visitante = p.goles_visitante

        p_info = {
            "id": p.id,
            "grupo": p.grupo,
            "fecha": p.fecha,
            "equipo_local": p.equipo_local,
            "equipo_visitante": p.equipo_visitante,
            "bandera_local": "",
            "bandera_visitante": "",
            "goles_local": g_local,
            "goles_visitante": g_visitante
        }

        # -------------------------
        # ARMAR CRUCES AUTOMÁTICOS
        # -------------------------

        if p.id in octavos_map:
            a, b = octavos_map[p.id]
            p_info["equipo_local"] = ganadores_knockout.get(
                a,
                f"Ganador {a}"
            )
            p_info["equipo_visitante"] = ganadores_knockout.get(
                b,
                f"Ganador {b}"
            )

        elif p.id in cuartos_map:
            a, b = cuartos_map[p.id]
            p_info["equipo_local"] = ganadores_knockout.get(
                a,
                f"Ganador {a}"
            )
            p_info["equipo_visitante"] = ganadores_knockout.get(
                b,
                f"Ganador {b}"
            )

        elif p.id in semis_map:
            a, b = semis_map[p.id]
            p_info["equipo_local"] = ganadores_knockout.get(
                a,
                f"Ganador {a}"
            )
            p_info["equipo_visitante"] = ganadores_knockout.get(
                b,
                f"Ganador {b}"
            )

        elif p.id in final_map:
            a, b = final_map[p.id]
            p_info["equipo_local"] = ganadores_knockout.get(
                a,
                f"Ganador {a}"
            )
            p_info["equipo_visitante"] = ganadores_knockout.get(
                b,
                f"Ganador {b}"
            )

        elif p.id in tercer_puesto_map:
            a, b = tercer_puesto_map[p.id]
            p_info["equipo_local"] = perdedores_knockout.get(
                a,
                f"Perdedor {a}"
            )
            p_info["equipo_visitante"] = perdedores_knockout.get(
                b,
                f"Perdedor {b}"
            )

        # -------------------------
        # SUSTITUIR 1A, 2B, ETC
        # -------------------------

        for letra in [
            "A","B","C","D","E","F",
            "G","H","I","J","K","L"
        ]:

            if p_info["equipo_local"] in [
                f"1{letra}",
                f"1ro Grupo {letra}",
                f"1° Grupo {letra}"
            ]:
                p_info["equipo_local"] = clasificados_grupos.get(
                    letra,
                    {}
                ).get(
                    "primero",
                    p_info["equipo_local"]
                )

            elif p_info["equipo_local"] in [
                f"2{letra}",
                f"2do Grupo {letra}",
                f"2° Grupo {letra}"
            ]:
                p_info["equipo_local"] = clasificados_grupos.get(
                    letra,
                    {}
                ).get(
                    "segundo",
                    p_info["equipo_local"]
                )

            if p_info["equipo_visitante"] in [
                f"1{letra}",
                f"1ro Grupo {letra}",
                f"1° Grupo {letra}"
            ]:
                p_info["equipo_visitante"] = clasificados_grupos.get(
                    letra,
                    {}
                ).get(
                    "primero",
                    p_info["equipo_visitante"]
                )

            elif p_info["equipo_visitante"] in [
                f"2{letra}",
                f"2do Grupo {letra}",
                f"2° Grupo {letra}"
            ]:
                p_info["equipo_visitante"] = clasificados_grupos.get(
                    letra,
                    {}
                ).get(
                    "segundo",
                    p_info["equipo_visitante"]
                )

        res_3_local = buscar_mejor_tercero(
            p_info["equipo_local"]
        )

        if res_3_local:
            p_info["equipo_local"] = res_3_local

        res_3_vis = buscar_mejor_tercero(
            p_info["equipo_visitante"]
        )

        if res_3_vis:
            p_info["equipo_visitante"] = res_3_vis

        # -------------------------
        # CALCULAR GANADOR
        # -------------------------

        if (
            g_local is not None
            and g_visitante is not None
            and p_info["equipo_local"]
            and p_info["equipo_visitante"]
        ):

            if g_local > g_visitante:

                ganadores_knockout[p.id] = p_info["equipo_local"]
                perdedores_knockout[p.id] = p_info["equipo_visitante"]

            elif g_visitante > g_local:

                ganadores_knockout[p.id] = p_info["equipo_visitante"]
                perdedores_knockout[p.id] = p_info["equipo_local"]

            else:

                # Paso 3: Arreglar los penales
                if tipo == "pronostico":

                    if p.id in pronosticos_eliminatoria_dict:

                        pen_local = pronosticos_eliminatoria_dict[p.id].penales_local
                        pen_vis = pronosticos_eliminatoria_dict[p.id].penales_visitante

                    else:

                        pen_local = None
                        pen_vis = None

                else:
                    # Agregado el else para cuando no es pronóstico (manteniendo la lógica del código original)
                    pen_local = p.penales_local
                    pen_vis = p.penales_visitante

                if (
                    pen_local is not None
                    and pen_vis is not None
                ):

                    if pen_local > pen_vis:

                        ganadores_knockout[p.id] = p_info["equipo_local"]
                        perdedores_knockout[p.id] = p_info["equipo_visitante"]

                    elif pen_vis > pen_local:

                        ganadores_knockout[p.id] = p_info["equipo_visitante"]
                        perdedores_knockout[p.id] = p_info["equipo_local"]

        # Asignar banderas antes de agregarlo a procesados
        p_info["bandera_local"] = banderas.get(
            p_info["equipo_local"],
            ""
        )

        p_info["bandera_visitante"] = banderas.get(
            p_info["equipo_visitante"],
            ""
        )

        partidos_procesados.append(p_info)

    fases_finales = [
        "16avos",
        "Octavos",
        "Cuartos",
        "Semis",
        "Final",
        "3er Puesto"
    ]

    return [
        p
        for p in partidos_procesados
        if p["grupo"] in fases_finales
    ]

# 2. SEGUNDO: Ahora definimos la ruta que ya puede encontrar a la función de arriba
@app.route("/llaves")
@login_required
def llaves():
    # 1. Obtener el tipo de llave y el ID del usuario
    tipo = request.args.get("tipo", "real")
    usuario_id = request.args.get("usuario_id", None)
    
    # 2. Lógica para determinar el contexto de la llave
    if tipo == "pronostico":
        if usuario_id:
            # Si se pasa un usuario_id, buscamos ese usuario o damos 404
            usuario_visto = User.query.get_or_404(usuario_id)
            user_id = usuario_visto.id
        else:
            # Si no hay usuario_id, por defecto es el usuario logueado
            usuario_visto = current_user
            user_id = current_user.id

        # Calculamos partidos y filtramos pronósticos del usuario determinado
        partidos_llaves = calcular_llaves_simuladas("pronostico", user_id)
        
        pronosticos = PronosticoEliminatoria.query.filter_by(
            usuario_id=user_id
        ).all()
        
        # Convertimos la lista de pronósticos a un diccionario para el template
        pronosticos_dict = {p.partido_id: p for p in pronosticos}
    else:
        # Lógica para tipo "real" u otros casos
        usuario_visto = current_user
        partidos_llaves = calcular_llaves_simuladas(tipo, current_user.id)
        pronosticos_dict = {}

    return render_template(
        "llaves.html",
        partidos=partidos_llaves,
        pronosticos=pronosticos_dict,
        usuario=current_user,
        usuario_visto=usuario_visto,
        tipo=tipo
    )
     




@app.route("/admin/actualizar_marcador/<int:partido_id>", methods=["POST"])
@login_required
def actualizar_marcador(partido_id):

    if not current_user.admin:
        return jsonify({
            "success": False,
            "message": "Acceso denegado"
        }), 403

    try:

        partido = Partido.query.get_or_404(partido_id)

        data = request.get_json()

        goles_local = data.get("goles_local")
        goles_visitante = data.get("goles_visitante")

        if goles_local == "" or goles_visitante == "":
            return jsonify({
                "success": False,
                "message": "Debe ingresar ambos marcadores"
            })

        partido.goles_local = int(goles_local)
        partido.goles_visitante = int(goles_visitante)

        db.session.commit()

        # ACTUALIZAR LLAVES DEL TORNEO
        actualizar_16avos()
        actualizar_fases_finales()

        # REINICIAR PUNTOS
        usuarios = User.query.all()

        for usuario in usuarios:
            usuario.puntos = 0

        # RECALCULAR PUNTOS
        pronosticos = Pronostico.query.all()

        for pronostico in pronosticos:

            partido_actual = Partido.query.get(
                pronostico.partido_id
            )

            if not partido_actual:
                continue

            if (
                partido_actual.goles_local is not None
                and
                partido_actual.goles_visitante is not None
            ):

                if (
                    pronostico.pred_local == partido_actual.goles_local
                    and
                    pronostico.pred_visitante == partido_actual.goles_visitante
                ):

                    usuario = User.query.get(
                        pronostico.usuario_id
                    )

                    if usuario:
                        usuario.puntos += 5

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Marcador guardado"
        })

    except Exception as e:

        print("ERROR:", str(e))

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
    

@app.route("/pronostico/<int:partido_id>", methods=["POST"])
@login_required
def pronostico(partido_id):

    partido = Partido.query.get_or_404(partido_id)

    pred_local = int(request.form.get("pred_local"))
    pred_visitante = int(request.form.get("pred_visitante"))

    pred_penales_local = request.form.get("pred_penales_local")
    pred_penales_visitante = request.form.get("pred_penales_visitante")

    pred_penales_local = (
        int(pred_penales_local)
        if pred_penales_local and pred_penales_local.strip() != ""
        else None
    )

    pred_penales_visitante = (
        int(pred_penales_visitante)
        if pred_penales_visitante and pred_penales_visitante.strip() != ""
        else None
    )

    pronostico_existente = Pronostico.query.filter_by(
        usuario_id=current_user.id,
        partido_id=partido.id
    ).first()

    if pronostico_existente:

        pronostico_existente.pred_local = pred_local
        pronostico_existente.pred_visitante = pred_visitante

        pronostico_existente.pred_penales_local = pred_penales_local
        pronostico_existente.pred_penales_visitante = pred_penales_visitante

    else:

        nuevo_pronostico = Pronostico(

            usuario_id=current_user.id,
            partido_id=partido.id,

            pred_local=pred_local,
            pred_visitante=pred_visitante,

            pred_penales_local=pred_penales_local,
            pred_penales_visitante=pred_penales_visitante
        )

        db.session.add(nuevo_pronostico)

    db.session.commit()

    return {
        "success": True,
        "mensaje": "Pronóstico guardado"
    }

@app.route("/ver_ids")
def ver_ids():

    partidos = Partido.query.all()

    salida = ""

    for p in partidos:
        salida += f"ID={p.id} | Grupo={p.grupo} | {p.equipo_local} vs {p.equipo_visitante}<br>"

    return salida

@app.route("/probar_grupos")
def probar_grupos():

    grupos = [
        "A","B","C","D","E","F",
        "G","H","I","J","K","L"
    ]

    resultado = ""

    for grupo in grupos:

        tabla = obtener_clasificacion_grupo(
            grupo
        )

        resultado += f"<h3>Grupo {grupo}</h3>"

        for equipo in tabla:

            resultado += (
                f"{equipo['equipo']} "
                f"({equipo['pts']} pts)<br>"
            )

    return resultado

@app.route("/generar_16avos")
def generar_16avos():

    actualizar_16avos()

    return "16avos actualizados"


@app.route("/debug_16avos")
def debug_16avos():

    for i in range(73, 89):

        p = Partido.query.get(i)

        print(
            i,
            p.equipo_local,
            p.equipo_visitante,
            p.goles_local,
            p.goles_visitante
        )

    return "ok"

@app.route("/debug_octavos")
def debug_octavos():

    for i in range(89, 97):

        p = Partido.query.get(i)

        print(
            i,
            p.equipo_local,
            "vs",
            p.equipo_visitante
        )

    return "ok"

@app.route("/reset_fases")
def reset_fases():

    partidos = Partido.query.filter(
        Partido.grupo.in_([
            "16avos",
            "Octavos",
            "Cuartos",
            "Semis",
            "3er Puesto",
            "Final"
        ])
    ).all()

    for p in partidos:

        p.goles_local = None
        p.goles_visitante = None

        p.penales_local = None
        p.penales_visitante = None

        if p.grupo != "16avos":
            p.equipo_local = ""
            p.equipo_visitante = ""

    db.session.commit()

    return "FASES FINALES RESETEADAS"

@app.route("/reset_pronosticos_total")
@login_required
def reset_pronosticos_total():

    if not current_user.admin:
        return "Acceso denegado"

    Pronostico.query.delete()

    for usuario in User.query.all():
        usuario.puntos = 0

    db.session.commit()

    return "Pronósticos eliminados"

@app.route("/fase-grupos")
@login_required
def fase_grupos():

    letras_grupos = [chr(i) for i in range(65, 77)]

    partidos_por_grupo = {}

    for letra in letras_grupos:
        partidos_por_grupo[letra] = (
            Partido.query
            .filter_by(grupo=letra)
            .order_by(Partido.id)
            .all()
        )

    pronosticos_usuario = Pronostico.query.filter_by(
        usuario_id=current_user.id
    ).all()

    pronosticos_dict = {
        p.partido_id: p
        for p in pronosticos_usuario
    }

    # ==========================
    # CIERRE DE EDICIONES
    # ==========================
    
    config = Configuracion.query.first()
    # Mantenemos el "if config else False" por seguridad
    edicion_habilitada = config.grupos_abiertos if config else False

    return render_template(
        "admin_grupos_rapido.html",
        partidos_por_grupo=partidos_por_grupo,
        pronosticos_dict=pronosticos_dict,
        bandera=bandera,
        edicion_habilitada=edicion_habilitada
    )
@app.route("/guardar_pronostico/<int:partido_id>", methods=["POST"])
@login_required
def guardar_pronostico(partido_id):
    try:
        data = request.get_json()
        
        # Validación simple por si llegan vacíos
        gl = data.get("goles_local")
        gv = data.get("goles_visitante")
        if gl == "" or gv == "" or gl is None or gv is None:
            return jsonify({"success": False, "message": "Los campos no pueden estar vacíos"}), 400

        # Busca si el usuario ya tiene un pronóstico para este partido
        pronostico = Pronostico.query.filter_by(usuario_id=current_user.id, partido_id=partido_id).first()
        
        if not pronostico:
            pronostico = Pronostico(usuario_id=current_user.id, partido_id=partido_id)
            db.session.add(pronostico)
        
        # Guarda los valores convirtiéndolos a entero de forma segura
        pronostico.pred_local = int(gl)
        pronostico.pred_visitante = int(gv)
        
        db.session.commit()
        return jsonify({"success": True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Error en el servidor: {str(e)}"}), 500
    
@app.route("/mis-llaves", methods=["GET", "POST"])
@login_required
def mis_llaves():

    if request.method == "POST":

        for partido in Partido.query.filter(
            Partido.id >= 73
        ).all():

            goles_local = request.form.get(
                f"local_{partido.id}"
            )

            goles_visitante = request.form.get(
                f"visitante_{partido.id}"
            )

            penales_local = request.form.get(
                f"pen_local_{partido.id}"
            )

            penales_visitante = request.form.get(
                f"pen_vis_{partido.id}"
            )

            pronostico = PronosticoEliminatoria.query.filter_by(
                usuario_id=current_user.id,
                partido_id=partido.id
            ).first()

            if not pronostico:

                pronostico = PronosticoEliminatoria(
                    usuario_id=current_user.id,
                    partido_id=partido.id
                )

                db.session.add(pronostico)

            pronostico.goles_local = (
                int(goles_local)
                if goles_local not in ["", None]
                else None
            )

            pronostico.goles_visitante = (
                int(goles_visitante)
                if goles_visitante not in ["", None]
                else None
            )

            pronostico.penales_local = (
                int(penales_local)
                if penales_local not in ["", None]
                else None
            )

            pronostico.penales_visitante = (
                int(penales_visitante)
                if penales_visitante not in ["", None]
                else None
            )

        db.session.commit()

    partidos = calcular_llaves_simuladas(
        "pronostico",
        current_user.id
    )

    pronosticos_eliminatoria = PronosticoEliminatoria.query.filter_by(
        usuario_id=current_user.id
    ).all()

    pronosticos_dict = {
        p.partido_id: p
        for p in pronosticos_eliminatoria
    }

    # ==========================
    # CIERRE DE EDICIONES
    # ==========================
    config = Configuracion.query.first()
    edicion_habilitada = config.llaves_abiertas if config else False

    return render_template(
        "mis_llaves.html",
        partidos=partidos,
        pronosticos=pronosticos_dict,
        usuario=current_user,
        edicion_habilitada=edicion_habilitada
    )

@app.route("/guardar_pronostico_eliminatoria/<int:partido_id>", methods=["POST"])
@login_required
def guardar_pronostico_eliminatoria(partido_id):

    try:

        data = request.get_json()

        gl = data.get("goles_local")
        gv = data.get("goles_visitante")

        pl = data.get("penales_local")
        pv = data.get("penales_visitante")

        if (
            gl == "" or gv == ""
            or gl is None or gv is None
        ):
            return jsonify({
                "success": False,
                "message": "Los campos no pueden estar vacíos"
            }), 400

        pronostico = PronosticoEliminatoria.query.filter_by(
            usuario_id=current_user.id,
            partido_id=partido_id
        ).first()

        if not pronostico:

            pronostico = PronosticoEliminatoria(
                usuario_id=current_user.id,
                partido_id=partido_id
            )

            db.session.add(pronostico)

        pronostico.goles_local = int(gl)
        pronostico.goles_visitante = int(gv)

        if pl not in [None, ""]:
            pronostico.penales_local = int(pl)

        if pv not in [None, ""]:
            pronostico.penales_visitante = int(pv)

        db.session.commit()

        return jsonify({
            "success": True
        })

    except Exception as e:

        db.session.rollback()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
    

@app.route("/crear-config")
def crear_config():

    db.create_all()

    config = Configuracion.query.first()

    if not config:

        config = Configuracion(
            grupos_abiertos=True,
            llaves_abiertas=True
        )

        db.session.add(config)
        db.session.commit()

    return "Configuración creada"

@app.route("/toggle-grupos")
@login_required
def toggle_grupos():

    if not current_user.admin:
        return "Acceso denegado"

    config = Configuracion.query.first()

    config.grupos_abiertos = (
        not config.grupos_abiertos
    )

    db.session.commit()

    return redirect("/admin")

@app.route("/toggle-llaves")
@login_required
def toggle_llaves():

    if not current_user.admin:
        return "Acceso denegado"

    config = Configuracion.query.first()

    config.llaves_abiertas = (
        not config.llaves_abiertas
    )

    db.session.commit()

    return redirect("/admin")

@app.route("/llaves-usuario/<int:usuario_id>")
@login_required
def llaves_usuario(usuario_id):

    usuario = User.query.get_or_404(usuario_id)

    partidos = calcular_llaves_simuladas(
        "pronostico",
        usuario.id
    )

    pronosticos_eliminatoria = PronosticoEliminatoria.query.filter_by(
        usuario_id=usuario.id
    ).all()

    pronosticos_dict = {
        p.partido_id: p
        for p in pronosticos_eliminatoria
    }

    return render_template(
        "llaves_usuario.html",
        partidos=partidos,
        pronosticos=pronosticos_dict,
        usuario_visto=usuario
    )


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        crear_admin_inicial()
    # Cambia esto:
    app.run(host='0.0.0.0', port=5000, debug=True)


