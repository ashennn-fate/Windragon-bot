```python
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import random
import sqlite3

import discord
from discord.ext import commands


# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

# Guarda el token en una variable de entorno llamada DISCORD_TOKEN.
# NO pongas el token real directamente en este archivo.
TOKEN = os.getenv("insertar_token")

DONACION_DIARIA = 500
INCURSIONES_DIARIAS = 2
EXCURSIONES_DIARIAS = 2

PRECIO_COFRE_BASE = 300

ZONA_HORARIA = ZoneInfo("America/Mexico_City")


# =========================================================
# ITEMS
# =========================================================

ITEMS_DATABASE = {
    "Espada de Madera": {
        "tipo": "arma",
        "atk": 10,
        "hp": 0,
        "rareza": "Común",
    },
    "Hacha de Hierro": {
        "tipo": "arma",
        "atk": 25,
        "hp": 0,
        "rareza": "Rara",
    },
    "Lanza Rúnica": {
        "tipo": "arma",
        "atk": 50,
        "hp": 10,
        "rareza": "Épica",
    },
    "Mandoble Dragón": {
        "tipo": "arma",
        "atk": 100,
        "hp": 25,
        "rareza": "Legendaria",
    },

    "Escudo de Cuero": {
        "tipo": "armadura",
        "atk": 0,
        "hp": 50,
        "rareza": "Común",
    },
    "Cota de Malla": {
        "tipo": "armadura",
        "atk": 5,
        "hp": 120,
        "rareza": "Rara",
    },
    "Armadura de Placas": {
        "tipo": "armadura",
        "atk": 10,
        "hp": 250,
        "rareza": "Épica",
    },
    "Coraza Divina": {
        "tipo": "armadura",
        "atk": 20,
        "hp": 500,
        "rareza": "Legendaria",
    },

    "Anillo de Vida": {
        "tipo": "accesorio",
        "atk": 10,
        "hp": 30,
        "rareza": "Común",
    },
    "Amuleto de Fuerza": {
        "tipo": "accesorio",
        "atk": 35,
        "hp": 20,
        "rareza": "Rara",
    },
    "Reliquia Antigua": {
        "tipo": "accesorio",
        "atk": 60,
        "hp": 100,
        "rareza": "Épica",
    },
    "Gema Celestial": {
        "tipo": "accesorio",
        "atk": 120,
        "hp": 300,
        "rareza": "Legendaria",
    },
}


# =========================================================
# PROBABILIDADES DE COFRES
# =========================================================

PROBABILIDADES_COFRE = {
    1: [
        ("Común", 0.70),
        ("Rara", 0.25),
        ("Épica", 0.05),
        ("Legendaria", 0.00),
    ],
    2: [
        ("Común", 0.40),
        ("Rara", 0.45),
        ("Épica", 0.13),
        ("Legendaria", 0.02),
    ],
    3: [
        ("Común", 0.20),
        ("Rara", 0.50),
        ("Épica", 0.25),
        ("Legendaria", 0.05),
    ],
    4: [
        ("Común", 0.05),
        ("Rara", 0.35),
        ("Épica", 0.45),
        ("Legendaria", 0.15),
    ],
    5: [
        ("Común", 0.00),
        ("Rara", 0.20),
        ("Épica", 0.50),
        ("Legendaria", 0.30),
    ],
}


# =========================================================
# JEFES
# =========================================================

JEFES = [
    {
        "nombre": "Goblin Rey",
        "emoji": "👹",
        "hp_base": 80,
        "atk_base": 10,
        "crit": 0.08,
    },
    {
        "nombre": "Caballero Maldito",
        "emoji": "💀",
        "hp_base": 120,
        "atk_base": 16,
        "crit": 0.10,
    },
    {
        "nombre": "Bestia de las Sombras",
        "emoji": "🐺",
        "hp_base": 170,
        "atk_base": 22,
        "crit": 0.15,
    },
    {
        "nombre": "Dragón Antiguo",
        "emoji": "🐉",
        "hp_base": 240,
        "atk_base": 30,
        "crit": 0.18,
    },
    {
        "nombre": "Dios de la Destrucción",
        "emoji": "☠️",
        "hp_base": 350,
        "atk_base": 42,
        "crit": 0.22,
    },
]


# =========================================================
# BOT
# =========================================================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("Wind ", "wind "),
    intents=intents,
    case_insensitive=True,
)


# =========================================================
# BASE DE DATOS
# =========================================================

def get_db():
    return sqlite3.connect("clan.db")


def init_db():
    with get_db() as conn:
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS miembros (
                guild_id INTEGER,
                usuario_id INTEGER,
                puntos_actuales INTEGER DEFAULT 0,
                puntos_inicio_dia INTEGER DEFAULT 0,
                fecha_inicio_dia TEXT,
                gemas INTEGER DEFAULT 0,
                nivel_cofre INTEGER DEFAULT 1,
                oleada_actual INTEGER DEFAULT 1,
                PRIMARY KEY (guild_id, usuario_id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS actividad_diaria (
                guild_id INTEGER,
                usuario_id INTEGER,
                fecha TEXT,
                incursiones INTEGER DEFAULT 0,
                excursiones INTEGER DEFAULT 0,
                PRIMARY KEY (guild_id, usuario_id, fecha)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS inventario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                usuario_id INTEGER,
                nombre_item TEXT,
                equipado INTEGER DEFAULT 0
            )
        """)

        # Migración sencilla para instalaciones antiguas.
        cur.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type='table' AND name='paneles'
        """)

        if cur.fetchone():
            cur.execute("PRAGMA table_info(paneles)")
            columnas = [col[1] for col in cur.fetchall()]

            if "tipo_panel" not in columnas:
                cur.execute("DROP TABLE paneles")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS paneles (
                guild_id INTEGER,
                tipo_panel TEXT,
                canal_id INTEGER,
                mensaje_id INTEGER,
                PRIMARY KEY (guild_id, tipo_panel)
            )
        """)

        conn.commit()


init_db()


# =========================================================
# FECHA CDMX
# =========================================================

def fecha_hoy():
    """
    Devuelve la fecha actual usando la zona horaria de Ciudad de México.
    """
    return datetime.now(ZONA_HORARIA).date().isoformat()


# =========================================================
# FUNCIONES DE USUARIO
# =========================================================

def asegurar_registro_usuario(guild_id: int, usuario_id: int):
    hoy = fecha_hoy()

    with get_db() as conn:
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO miembros (
                guild_id,
                usuario_id,
                puntos_actuales,
                puntos_inicio_dia,
                fecha_inicio_dia,
                gemas,
                nivel_cofre,
                oleada_actual
            )
            VALUES (?, ?, 0, 0, ?, 0, 1, 1)

            ON CONFLICT(guild_id, usuario_id)
            DO NOTHING
        """, (guild_id, usuario_id, hoy))

        conn.commit()


def obtener_datos_usuario(guild_id: int, usuario_id: int):
    asegurar_registro_usuario(guild_id, usuario_id)

    hoy = fecha_hoy()

    with get_db() as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT
                puntos_actuales,
                puntos_inicio_dia,
                fecha_inicio_dia,
                gemas,
                oleada_actual,
                nivel_cofre
            FROM miembros
            WHERE guild_id = ?
            AND usuario_id = ?
        """, (guild_id, usuario_id))

        m_datos = cur.fetchone()

        cur.execute("""
            SELECT
                incursiones,
                excursiones
            FROM actividad_diaria
            WHERE guild_id = ?
            AND usuario_id = ?
            AND fecha = ?
        """, (guild_id, usuario_id, hoy))

        a_datos = cur.fetchone()

    puntos_totales = m_datos[0]
    inicio_dia = m_datos[1]
    fecha_inicio = m_datos[2]
    gemas = m_datos[3]
    oleada = m_datos[4]
    nivel_cofre = m_datos[5]

    if fecha_inicio != hoy:
        ganados_hoy = 0
    else:
        ganados_hoy = max(
            0,
            puntos_totales - inicio_dia
        )

    inc = a_datos[0] if a_datos else 0
    exc = a_datos[1] if a_datos else 0

    return (
        puntos_totales,
        ganados_hoy,
        inc,
        exc,
        gemas,
        oleada,
        nivel_cofre,
    )


# =========================================================
# BÚSQUEDA DE MIEMBROS
# =========================================================

async def buscar_miembro(ctx, texto: str):
    """
    Permite buscar:
    - @usuario
    - ID
    - nombre exacto
    - display name exacto
    - comienzo del nombre
    - coincidencia parcial
    """

    texto = texto.strip()

    # Primero intentamos el convertidor oficial de Discord.
    try:
        return await commands.MemberConverter().convert(ctx, texto)
    except commands.MemberNotFound:
        pass

    texto_clean = (
        texto
        .lower()
        .replace("@", "")
        .strip()
    )

    if len(texto_clean) < 2:
        return None

    # Coincidencia exacta.
    for member in ctx.guild.members:
        if (
            member.display_name.lower() == texto_clean
            or member.name.lower() == texto_clean
        ):
            return member

    # Comienzo del nombre.
    for member in ctx.guild.members:
        if (
            member.display_name.lower().startswith(texto_clean)
            or member.name.lower().startswith(texto_clean)
        ):
            return member

    # Coincidencia parcial.
    for member in ctx.guild.members:
        if (
            texto_clean in member.display_name.lower()
            or texto_clean in member.name.lower()
        ):
            return member

    return None


# =========================================================
# STATS
# =========================================================

def calcular_stats(guild_id: int, usuario_id: int):
    atk_base = 20
    hp_base = 100

    with get_db() as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT nombre_item
            FROM inventario
            WHERE guild_id = ?
            AND usuario_id = ?
            AND equipado = 1
        """, (guild_id, usuario_id))

        items = cur.fetchall()

    for (nombre,) in items:
        if nombre in ITEMS_DATABASE:
            atk_base += ITEMS_DATABASE[nombre]["atk"]
            hp_base += ITEMS_DATABASE[nombre]["hp"]

    return atk_base, hp_base


# =========================================================
# BARRA DE PROGRESO
# =========================================================

def barra_progreso(actual: int, maximo: int, largo: int = 8):
    if maximo <= 0:
        return "░" * largo

    porcentaje = min(
        max(actual, 0) / maximo,
        1.0
    )

    llenos = round(
        porcentaje * largo
    )

    return (
        "█" * llenos
        + "░" * (largo - llenos)
    )


# =========================================================
# PANEL DE ACTIVIDAD
# =========================================================

async def generar_embed_actividad(guild):
    hoy = fecha_hoy()

    embed = discord.Embed(
        title="📊 PANEL DE ACTIVIDAD Y DONACIONES 📊",
        description=(
            f"📅 **Fecha:** `{hoy}`\n"
            "━━━━━━━⬍━━━━━━━"
        ),
        color=discord.Color.blue(),
    )

    with get_db() as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT usuario_id
            FROM miembros
            WHERE guild_id = ?
        """, (guild.id,))

        usuarios = cur.fetchall()

    if not usuarios:
        embed.add_field(
            name="⚠️ SIN REGISTROS",
            value="Aún no hay actividad registrada.",
            inline=False,
        )
        return embed

    for (u_id,) in usuarios:
        member = guild.get_member(u_id)

        nombre = (
            member.display_name
            if member
            else f"ID: {u_id}"
        )

        (
            totales,
            hoy_pts,
            inc,
            exc,
            _,
            _,
            _,
        ) = obtener_datos_usuario(
            guild.id,
            u_id
        )

        b_donacion = barra_progreso(
            hoy_pts,
            DONACION_DIARIA
        )

        b_inc = barra_progreso(
            inc,
            INCURSIONES_DIARIAS,
            largo=5
        )

        b_exc = barra_progreso(
            exc,
            EXCURSIONES_DIARIAS,
            largo=5
        )

        e_don = (
            "✅"
            if hoy_pts >= DONACION_DIARIA
            else "⏳"
        )

        e_inc = (
            "✅"
            if inc >= INCURSIONES_DIARIAS
            else "⏳"
        )

        e_exc = (
            "✅"
            if exc >= EXCURSIONES_DIARIAS
            else "⏳"
        )

        val = (
            f"🏆 **Puntos Totales:** `{totales:,}`\n"
            f"💰 **Donación Hoy:** "
            f"`{hoy_pts}/{DONACION_DIARIA}` {e_don}\n"
            f"`[{b_donacion}]`\n"
            f"⚔️ **Incursiones:** "
            f"`{inc}/{INCURSIONES_DIARIAS}` "
            f"{e_inc} `[{b_inc}]`\n"
            f"🧭 **Excursiones:** "
            f"`{exc}/{EXCURSIONES_DIARIAS}` "
            f"{e_exc} `[{b_exc}]`\n"
            "────────────────────"
        )

        embed.add_field(
            name=f"👤 {nombre}",
            value=val,
            inline=False,
        )

    return embed


# =========================================================
# PANEL RPG
# =========================================================

async def generar_embed_rpg(guild):
    embed = discord.Embed(
        title="⚔️ TABLA DE CLASIFICACIÓN Y STATS RPG ⚔️",
        description=(
            "Estado general de los guerreros del clan\n"
            "━━━━━━━⬍━━━━━━━"
        ),
        color=discord.Color.dark_red(),
    )

    with get_db() as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT usuario_id
            FROM miembros
            WHERE guild_id = ?
        """, (guild.id,))

        usuarios = cur.fetchall()

    if not usuarios:
        embed.add_field(
            name="⚠️ SIN REGISTROS",
            value="Aún no hay jugadores registrados.",
            inline=False,
        )
        return embed

    for (u_id,) in usuarios:
        member = guild.get_member(u_id)

        nombre = (
            member.display_name
            if member
            else f"ID: {u_id}"
        )

        (
            _,
            _,
            _,
            _,
            gemas,
            oleada,
            nivel_cofre,
        ) = obtener_datos_usuario(
            guild.id,
            u_id
        )

        atk, hp = calcular_stats(
            guild.id,
            u_id
        )

        val = (
            f"💎 **Gemas:** `{gemas}`\n"
            f"⚔️ **Ataque:** `{atk}`\n"
            f"❤️ **Vida:** `{hp}`\n"
            f"🌊 **Oleada Máxima:** `{oleada}`\n"
            f"🎁 **Nivel de Cofre:** `{nivel_cofre}`\n"
            "────────────────────"
        )

        embed.add_field(
            name=f"🛡️ {nombre}",
            value=val,
            inline=False,
        )

    return embed


# =========================================================
# REUBICAR / ACTUALIZAR PANEL
# =========================================================

async def reubicar_panel(guild, tipo_panel: str):
    with get_db() as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT canal_id, mensaje_id
            FROM paneles
            WHERE guild_id = ?
            AND tipo_panel = ?
        """, (guild.id, tipo_panel))

        panel = cur.fetchone()

    if not panel:
        return

    canal = guild.get_channel(panel[0])

    if not canal:
        return

    try:
        msg_viejo = await canal.fetch_message(
            panel[1]
        )
        await msg_viejo.delete()
    except Exception:
        pass

    if tipo_panel == "actividad":
        embed = await generar_embed_actividad(guild)
    else:
        embed = await generar_embed_rpg(guild)

    nuevo_msg = await canal.send(
        embed=embed
    )

    with get_db() as conn:
        cur = conn.cursor()

        cur.execute("""
            UPDATE paneles
            SET mensaje_id = ?
            WHERE guild_id = ?
            AND tipo_panel = ?
        """, (
            nuevo_msg.id,
            guild.id,
            tipo_panel,
        ))

        conn.commit()


# =========================================================
# COMANDOS ADMINISTRATIVOS
# =========================================================

@bot.command(name="cp")
@commands.has_permissions(administrator=True)
async def cp(ctx):
    """Crea el panel de actividad."""

    embed = await generar_embed_actividad(
        ctx.guild
    )

    msg = await ctx.channel.send(
        embed=embed
    )

    with get_db() as conn:
        cur = conn.cursor()

        cur.execute("""
            INSERT OR REPLACE INTO paneles (
                guild_id,
                tipo_panel,
                canal_id,
                mensaje_id
            )
            VALUES (?, 'actividad', ?, ?)
        """, (
            ctx.guild.id,
            ctx.channel.id,
            msg.id,
        ))

        conn.commit()

    await ctx.send(
        f"✅ Panel de actividad fijado en "
        f"{ctx.channel.mention}."
    )


@bot.command(name="panelrpg")
@commands.has_permissions(administrator=True)
async def panelrpg(ctx):
    """Crea el panel RPG."""

    embed = await generar_embed_rpg(
        ctx.guild
    )

    msg = await ctx.channel.send(
        embed=embed
    )

    with get_db() as conn:
        cur = conn.cursor()

        cur.execute("""
            INSERT OR REPLACE INTO paneles (
                guild_id,
                tipo_panel,
                canal_id,
                mensaje_id
            )
            VALUES (?, 'rpg', ?, ?)
        """, (
            ctx.guild.id,
            ctx.channel.id,
            msg.id,
        ))

        conn.commit()

    await ctx.send(
        f"✅ Panel RPG fijado en "
        f"{ctx.channel.mention}."
    )


# =========================================================
# RESET DIARIO
# =========================================================

@bot.command(name="r")
@commands.has_permissions(administrator=True)
async def reset_diario(ctx):
    """
    Reinicia manualmente la actividad diaria.
    Los puntos totales no se pierden.
    """

    hoy = fecha_hoy()

    with get_db() as conn:
        cur = conn.cursor()

        cur.execute("""
            UPDATE miembros
            SET
                puntos_inicio_dia = puntos_actuales,
                fecha_inicio_dia = ?
            WHERE guild_id = ?
        """, (
            hoy,
            ctx.guild.id,
        ))

        cur.execute("""
            DELETE FROM actividad_diaria
            WHERE guild_id = ?
            AND fecha = ?
        """, (
            ctx.guild.id,
            hoy,
        ))

        conn.commit()

    await ctx.send(
        "🔄 **Reinicio diario completado.**\n"
        "Las métricas de hoy se han limpiado "
        "y los puntos totales fueron preservados."
    )

    await reubicar_panel(
        ctx.guild,
        "actividad"
    )


# =========================================================
# PS - ESTABLECER PUNTOS BASE
# =========================================================

@bot.command(name="ps")
@commands.has_permissions(administrator=True)
async def ps(ctx, *, args: str = None):
    """
    Establece puntos iniciales del día.

    Ejemplos:

    Wind ps 500 @Usuario
    Wind ps 500 Usuario
    Wind ps 500 Juan
    Wind ps 500 Juan, Pedro
    """

    if not args:
        await ctx.send(
            "❌ Uso: `Wind ps <puntos> <usuario1> <usuario2>...`"
        )
        return

    partes = [
        p.strip()
        for p in args.replace(",", " ").split()
        if p.strip()
    ]

    puntos_base = None
    nombres = []

    for parte in partes:
        if parte.isdigit():
            puntos_base = int(parte)
        else:
            nombres.append(parte)

    if puntos_base is None:
        await ctx.send(
            "❌ Debes incluir una cantidad numérica de puntos."
        )
        return

    procesados = []
    hoy = fecha_hoy()

    for nombre in nombres:
        usuario = await buscar_miembro(
            ctx,
            nombre
        )

        if usuario and usuario.display_name not in procesados:

            asegurar_registro_usuario(
                ctx.guild.id,
                usuario.id
            )

            with get_db() as conn:
                cur = conn.cursor()

                cur.execute("""
                    UPDATE miembros
                    SET
                        puntos_actuales = ?,
                        puntos_inicio_dia = ?,
                        fecha_inicio_dia = ?
                    WHERE guild_id = ?
                    AND usuario_id = ?
                """, (
                    puntos_base,
                    puntos_base,
                    hoy,
                    ctx.guild.id,
                    usuario.id,
                ))

                conn.commit()

            procesados.append(
                usuario.display_name
            )

    if procesados:
        await ctx.send(
            f"⚙️ Puntos base establecidos en "
            f"`{puntos_base:,}` para: "
            f"{', '.join(procesados)}"
        )

        await reubicar_panel(
            ctx.guild,
            "actividad"
        )

    else:
        await ctx.send(
            "❌ No se encontró ningún miembro "
            "con esos nombres."
        )


# =========================================================
# P - AÑADIR PUNTOS
# =========================================================

@bot.command(name="p")
@commands.has_permissions(administrator=True)
async def p(ctx, *, args: str = None):
    """
    Añade puntos y 100 gemas por acción.

    Se permiten nombres sin @.
    """

    if not args:
        await ctx.send(
            "❌ Uso: `Wind p <puntos> <usuario1> <usuario2>...`"
        )
        return

    partes = [
        p.strip()
        for p in args.replace(",", " ").split()
        if p.strip()
    ]

    puntos = None
    nombres = []

    for parte in partes:
        if (
            parte.isdigit()
            or (
                parte.startswith("-")
                and parte[1:].isdigit()
            )
        ):
            puntos = int(parte)
        else:
            nombres.append(parte)

    if puntos is None:
        await ctx.send(
            "❌ Debes incluir la cantidad de puntos."
        )
        return

    procesados = []
    hoy = fecha_hoy()

    for nombre in nombres:
        usuario = await buscar_miembro(
            ctx,
            nombre
        )

        if (
            usuario
            and usuario.display_name not in procesados
        ):
            asegurar_registro_usuario(
                ctx.guild.id,
                usuario.id
            )

            with get_db() as conn:
                cur = conn.cursor()

                cur.execute("""
                    SELECT
                        puntos_actuales,
                        puntos_inicio_dia,
                        fecha_inicio_dia
                    FROM miembros
                    WHERE guild_id = ?
                    AND usuario_id = ?
                """, (
                    ctx.guild.id,
                    usuario.id,
                ))

                res = cur.fetchone()

                p_act = res[0]
                p_ini = res[1]
                f_ini = res[2]

                nuevos_pts = p_act + puntos

                if f_ini != hoy:
                    ini_dia = p_act
                else:
                    ini_dia = p_ini

                cur.execute("""
                    UPDATE miembros
                    SET
                        puntos_actuales = ?,
                        puntos_inicio_dia = ?,
                        fecha_inicio_dia = ?,
                        gemas = gemas + 100
                    WHERE guild_id = ?
                    AND usuario_id = ?
                """, (
                    nuevos_pts,
                    ini_dia,
                    hoy,
                    ctx.guild.id,
                    usuario.id,
                ))

                conn.commit()

            procesados.append(
                usuario.display_name
            )

    if procesados:
        signo = "+" if puntos >= 0 else ""

        await ctx.send(
            f"✨ {signo}{puntos:,} pts "
            f"y +100 gemas para: "
            f"{', '.join(procesados)}"
        )

        await reubicar_panel(
            ctx.guild,
            "actividad"
        )

        await reubicar_panel(
            ctx.guild,
            "rpg"
        )

    else:
        await ctx.send(
            "❌ No se encontró ningún miembro."
        )


# =========================================================
# INCURSIONES
# =========================================================

@bot.command(name="i")
@commands.has_permissions(administrator=True)
async def i(ctx, *, args: str = None):
    """
    Registra incursiones.

    Máximo diario:
    2 por usuario.
    """

    if not args:
        await ctx.send(
            "❌ Uso: `Wind i <cantidad> <usuario1> <usuario2>...`"
        )
        return

    partes = [
        p.strip()
        for p in args.replace(",", " ").split()
        if p.strip()
    ]

    cant = None
    nombres = []

    for parte in partes:
        if parte.isdigit():
            cant = int(parte)
        else:
            nombres.append(parte)

    if cant is None:
        cant = 1

    if cant <= 0:
        await ctx.send(
            "❌ La cantidad debe ser mayor que 0."
        )
        return

    procesados = []
    rechazados = []

    hoy = fecha_hoy()

    for nombre in nombres:
        usuario = await buscar_miembro(
            ctx,
            nombre
        )

        if not usuario:
            continue

        if usuario.display_name in procesados:
            continue

        asegurar_registro_usuario(
            ctx.guild.id,
            usuario.id
        )

        with get_db() as conn:
            cur = conn.cursor()

            cur.execute("""
                SELECT incursiones
                FROM actividad_diaria
                WHERE guild_id = ?
                AND usuario_id = ?
                AND fecha = ?
            """, (
                ctx.guild.id,
                usuario.id,
                hoy,
            ))

            resultado = cur.fetchone()

            actuales = (
                resultado[0]
                if resultado
                else 0
            )

            restantes = max(
                0,
                INCURSIONES_DIARIAS - actuales
            )

            if restantes <= 0:
                rechazados.append(
                    f"{usuario.display_name} (límite alcanzado)"
                )
                continue

            cantidad_real = min(
                cant,
                restantes
            )

            cur.execute("""
                INSERT INTO actividad_diaria (
                    guild_id,
                    usuario_id,
                    fecha,
                    incursiones
                )
                VALUES (?, ?, ?, ?)

                ON CONFLICT(
                    guild_id,
                    usuario_id,
                    fecha
                )
                DO UPDATE SET
                    incursiones =
                    incursiones + ?
            """, (
                ctx.guild.id,
                usuario.id,
                hoy,
                cantidad_real,
                cantidad_real,
            ))

            cur.execute("""
                UPDATE miembros
                SET gemas = gemas + ?
                WHERE guild_id = ?
                AND usuario_id = ?
            """, (
                cantidad_real * 50,
                ctx.guild.id,
                usuario.id,
            ))

            conn.commit()

        procesados.append(
            f"{usuario.display_name} (+{cantidad_real})"
        )

    mensaje = ""

    if procesados:
        mensaje += (
            f"⚔️ **Incursiones registradas:**\n"
            f"{', '.join(procesados)}\n"
        )

    if rechazados:
        mensaje += (
            f"\n🚫 **No registradas:**\n"
            f"{', '.join(rechazados)}"
        )

    if mensaje:
        await ctx.send(mensaje)

        await reubicar_panel(
            ctx.guild,
            "actividad"
        )

        await reubicar_panel(
            ctx.guild,
            "rpg"
        )
    else:
        await ctx.send(
            "❌ No se encontró ningún miembro."
        )


# =========================================================
# EXCURSIONES
# =========================================================

@bot.command(name="e")
@commands.has_permissions(administrator=True)
async def e(ctx, *, args: str = None):
    """
    Registra excursiones.

    Máximo diario:
    2 por usuario.
    """

    if not args:
        await ctx.send(
            "❌ Uso: `Wind e <cantidad> <usuario1> <usuario2>...`"
        )
        return

    partes = [
        p.strip()
        for p in args.replace(",", " ").split()
        if p.strip()
    ]

    cant = None
    nombres = []

    for parte in partes:
        if parte.isdigit():
            cant = int(parte)
        else:
            nombres.append(parte)

    if cant is None:
        cant = 1

    if cant <= 0:
        await ctx.send(
            "❌ La cantidad debe ser mayor que 0."
        )
        return

    procesados = []
    rechazados = []

    hoy = fecha_hoy()

    for nombre in nombres:
        usuario = await buscar_miembro(
            ctx,
            nombre
        )

        if not usuario:
            continue

        if usuario.display_name in procesados:
            continue

        asegurar_registro_usuario(
            ctx.guild.id,
            usuario.id
        )

        with get_db() as conn:
            cur = conn.cursor()

            cur.execute("""
                SELECT excursiones
                FROM actividad_diaria
                WHERE guild_id = ?
                AND usuario_id = ?
                AND fecha = ?
            """, (
                ctx.guild.id,
                usuario.id,
                hoy,
            ))

            resultado = cur.fetchone()

            actuales = (
                resultado[0]
                if resultado
                else 0
            )

            restantes = max(
                0,
                EXCURSIONES_DIARIAS - actuales
            )

            if restantes <= 0:
                rechazados.append(
                    f"{usuario.display_name} (límite alcanzado)"
                )
                continue

            cantidad_real = min(
                cant,
                restantes
            )

            cur.execute("""
                INSERT INTO actividad_diaria (
                    guild_id,
                    usuario_id,
                    fecha,
                    excursiones
                )
                VALUES (?, ?, ?, ?)

                ON CONFLICT(
                    guild_id,
                    usuario_id,
                    fecha
                )
                DO UPDATE SET
                    excursiones =
                    excursiones + ?
            """, (
                ctx.guild.id,
                usuario.id,
                hoy,
                cantidad_real,
                cantidad_real,
            ))

            cur.execute("""
                UPDATE miembros
                SET gemas = gemas + ?
                WHERE guild_id = ?
                AND usuario_id = ?
            """, (
                cantidad_real * 50,
                ctx.guild.id,
                usuario.id,
            ))

            conn.commit()

        procesados.append(
            f"{usuario.display_name} (+{cantidad_real})"
        )

    mensaje = ""

    if procesados:
        mensaje += (
            f"🧭 **Excursiones registradas:**\n"
            f"{', '.join(procesados)}\n"
        )

    if rechazados:
        mensaje += (
            f"\n🚫 **No registradas:**\n"
            f"{', '.join(rechazados)}"
        )

    if mensaje:
        await ctx.send(mensaje)

        await reubicar_panel(
            ctx.guild,
            "actividad"
        )

        await reubicar_panel(
            ctx.guild,
            "rpg"
        )

    else:
        await ctx.send(
            "❌ No se encontró ningún miembro."
        )


# =========================================================
# COFRE
# =========================================================

@bot.command(name="cofre")
async def cofre(ctx):
    asegurar_registro_usuario(
        ctx.guild.id,
        ctx.author.id
    )

    with get_db() as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT gemas, nivel_cofre
            FROM miembros
            WHERE guild_id = ?
            AND usuario_id = ?
        """, (
            ctx.guild.id,
            ctx.author.id,
        ))

        gemas, lvl = cur.fetchone()

    if gemas < PRECIO_COFRE_BASE:
        await ctx.send(
            f"❌ Necesitas `{PRECIO_COFRE_BASE}` "
            f"gemas para abrir un cofre.\n"
            f"💎 Tienes `{gemas}`."
        )
        return

    lvl = max(
        1,
        min(5, lvl)
    )

    probs = PROBABILIDADES_COFRE[lvl]

    rareza = random.choices(
        [p[0] for p in probs],
        weights=[p[1] for p in probs],
        k=1,
    )[0]

    items_posibles = [
        nombre
        for nombre, datos in ITEMS_DATABASE.items()
        if datos["rareza"] == rareza
    ]

    # Seguridad por si alguna rareza queda sin objetos.
    if not items_posibles:
        await ctx.send(
            "❌ No hay objetos disponibles "
            "para esta rareza."
        )
        return

    item_ganado = random.choice(
        items_posibles
    )

    with get_db() as conn:
        cur = conn.cursor()

        cur.execute("""
            UPDATE miembros
            SET gemas = gemas - ?
            WHERE guild_id = ?
            AND usuario_id = ?
        """, (
            PRECIO_COFRE_BASE,
            ctx.guild.id,
            ctx.author.id,
        ))

        cur.execute("""
            INSERT INTO inventario (
                guild_id,
                usuario_id,
                nombre_item,
                equipado
            )
            VALUES (?, ?, ?, 0)
        """, (
            ctx.guild.id,
            ctx.author.id,
            item_ganado,
        ))

        conn.commit()

    stats = ITEMS_DATABASE[
        item_ganado
    ]

    await ctx.send(
        f"🎁 **{ctx.author.display_name}** "
        f"ha abierto un **Cofre Nivel {lvl}**.\n\n"
        f"✨ **{item_ganado}**\n"
        f"⭐ Rareza: **{rareza}**\n"
        f"⚔️ +{stats['atk']} ATK\n"
        f"❤️ +{stats['hp']} HP"
    )

    await reubicar_panel(
        ctx.guild,
        "rpg"
    )


# =========================================================
# INVENTARIO
# =========================================================

@bot.command(name="inv")
async def inv(ctx):
    asegurar_registro_usuario(
        ctx.guild.id,
        ctx.author.id
    )

    with get_db() as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT
                id,
                nombre_item,
                equipado
            FROM inventario
            WHERE guild_id = ?
            AND usuario_id = ?
            ORDER BY id ASC
        """, (
            ctx.guild.id,
            ctx.author.id,
        ))

        items = cur.fetchall()

    if not items:
        await ctx.send(
            "🎒 Tu inventario está vacío.\n"
            "¡Usa `Wind cofre` para conseguir ítems!"
        )
        return

    desc = ""

    for item_id, nombre, equipado in items:
        st = ITEMS_DATABASE.get(
            nombre
        )

        if not st:
            continue

        eq_str = (
            " 🟢 **EQUIPADO**"
            if equipado
            else ""
        )

        desc += (
            f"`ID: {item_id}` | "
            f"**{nombre}** "
            f"[{st['rareza']}]\n"
            f"↳ ⚔️ +{st['atk']} ATK "
            f"| ❤️ +{st['hp']} HP"
            f"{eq_str}\n\n"
        )

    embed = discord.Embed(
        title=(
            f"🎒 Inventario de "
            f"{ctx.author.display_name}"
        ),
        description=desc,
        color=discord.Color.blue(),
    )

    await ctx.send(
        embed=embed
    )


# =========================================================
# EQUIPAR
# =========================================================

@bot.command(name="equipar")
async def equipar(ctx, item_id: int):
    asegurar_registro_usuario(
        ctx.guild.id,
        ctx.author.id
    )

    with get_db() as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT nombre_item
            FROM inventario
            WHERE id = ?
            AND guild_id = ?
            AND usuario_id = ?
        """, (
            item_id,
            ctx.guild.id,
            ctx.author.id,
        ))

        item = cur.fetchone()

        if not item:
            await ctx.send(
                "❌ No se encontró ese ítem "
                "en tu inventario."
            )
            return

        nombre_item = item[0]

        if nombre_item not in ITEMS_DATABASE:
            await ctx.send(
                "❌ Ese objeto ya no existe "
                "en la base de datos."
            )
            return

        tipo = ITEMS_DATABASE[
            nombre_item
        ]["tipo"]

        cur.execute("""
            SELECT
                id,
                nombre_item
            FROM inventario
            WHERE guild_id = ?
            AND usuario_id = ?
            AND equipado = 1
        """, (
            ctx.guild.id,
            ctx.author.id,
        ))

        equipados = cur.fetchall()

        for eq_id, eq_nombre in equipados:
            if (
                eq_nombre in ITEMS_DATABASE
                and ITEMS_DATABASE[eq_nombre]["tipo"]
                == tipo
            ):
                cur.execute("""
                    UPDATE inventario
                    SET equipado = 0
                    WHERE id = ?
                """, (eq_id,))

        cur.execute("""
            UPDATE inventario
            SET equipado = 1
            WHERE id = ?
            AND guild_id = ?
            AND usuario_id = ?
        """, (
            item_id,
            ctx.guild.id,
            ctx.author.id,
        ))

        conn.commit()

    await ctx.send(
        f"🛡️ Te has equipado "
        f"**{nombre_item}**."
    )

    await reubicar_panel(
        ctx.guild,
        "rpg"
    )


# =========================================================
# COMBATE
# =========================================================

@bot.command(name="combate")
async def combate(ctx):
    """
    Sistema de combate por turnos.

    Incluye:
    - daño aleatorio
    - golpes críticos
    - defensa
    - jefes diferentes
    - recompensas
    - subida de oleada
    """

    asegurar_registro_usuario(
        ctx.guild.id,
        ctx.author.id
    )

    atk, hp_max = calcular_stats(
        ctx.guild.id,
        ctx.author.id
    )

    with get_db() as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT oleada_actual
            FROM miembros
            WHERE guild_id = ?
            AND usuario_id = ?
        """, (
            ctx.guild.id,
            ctx.author.id,
        ))

        resultado = cur.fetchone()

    oleada = (
        resultado[0]
        if resultado
        else 1
    )

    jefe_base = JEFES[
        (oleada - 1) % len(JEFES)
    ]

    nombre_jefe = jefe_base["nombre"]
    emoji_jefe = jefe_base["emoji"]

    # Escalado según oleada.
    multiplicador = 1 + (
        (oleada - 1) * 0.20
    )

    boss_hp_max = int(
        jefe_base["hp_base"]
        * multiplicador
    )

    boss_atk = int(
        jefe_base["atk_base"]
        * multiplicador
    )

    boss_hp = boss_hp_max
    jugador_hp = hp_max

    turno = 1
    registro = []

    while jugador_hp > 0 and boss_hp > 0:
        # =================================================
        # TURNO DEL JUGADOR
        # =================================================

        variacion = random.uniform(
            0.80,
            1.20
        )

        dano_jugador = max(
            1,
            int(atk * variacion)
        )

        critico = (
            random.random() < 0.15
        )

        if critico:
            dano_jugador *= 2

        boss_hp -= dano_jugador

        if critico:
            registro.append(
                f"💥 **CRÍTICO:** "
                f"hiciste `{dano_jugador}` de daño."
            )
        else:
            registro.append(
                f"⚔️ Hiciste "
                f"`{dano_jugador}` de daño."
            )

        if boss_hp <= 0:
            break

        # =================================================
        # TURNO DEL JEFE
        # =================================================

        variacion_boss = random.uniform(
            0.80,
            1.20
        )

        dano_boss = max(
            1,
            int(boss_atk * variacion_boss)
        )

        critico_boss = (
            random.random()
            < jefe_base["crit"]
        )

        if critico_boss:
            dano_boss *= 2

        jugador_hp -= dano_boss

        if critico_boss:
            registro.append(
                f"💀 **CRÍTICO DEL JEFE:** "
                f"recibiste `{dano_boss}` de daño."
            )
        else:
            registro.append(
                f"{emoji_jefe} El jefe hizo "
                f"`{dano_boss}` de daño."
            )

        turno += 1

        # Seguridad.
        if turno > 100:
            break

    # =====================================================
    # VICTORIA
    # =====================================================

    if boss_hp <= 0 and jugador_hp > 0:

        ganancia = (
            100
            + (oleada * 20)
            + random.randint(0, 50)
        )

        # Cada 5 oleadas aumenta el nivel de cofre.
        nueva_oleada = oleada + 1

        nivel_cofre_nuevo = min(
            5,
            1 + (
                nueva_oleada // 5
            )
        )

        with get_db() as conn:
            cur = conn.cursor()

            cur.execute("""
                UPDATE miembros
                SET
                    oleada_actual = ?,
                    gemas = gemas + ?,
                    nivel_cofre = ?
                WHERE guild_id = ?
                AND usuario_id = ?
            """, (
                nueva_oleada,
                ganancia,
                nivel_cofre_nuevo,
                ctx.guild.id,
                ctx.author.id,
            ))

            conn.commit()

        # Mostramos máximo 10 líneas.
        resumen = "\n".join(
            registro[:10]
        )

        if len(registro) > 10:
            resumen += (
                "\n... y más movimientos."
            )

        await ctx.send(
            f"⚔️ **¡VICTORIA!**\n\n"
            f"{emoji_jefe} "
            f"**{nombre_jefe}** "
            f"— Oleada `{oleada}`\n"
            f"❤️ Vida restante: "
            f"`{max(jugador_hp, 0)}/{hp_max}`\n\n"
            f"{resumen}\n\n"
            f"🎉 **+{ganancia} gemas**\n"
            f"🌊 Nueva oleada: "
            f"**{nueva_oleada}**\n"
            f"🎁 Nivel de cofre: "
            f"**{nivel_cofre_nuevo}**"
        )

    # =====================================================
    # DERROTA
    # =====================================================

    else:

        resumen = "\n".join(
            registro[:10]
        )

        if len(registro) > 10:
            resumen += (
                "\n... y más movimientos."
            )

        await ctx.send(
            f"💀 **DERROTA**\n\n"
            f"{emoji_jefe} "
            f"**{nombre_jefe}** "
            f"— Oleada `{oleada}`\n"
            f"❤️ Tu vida llegó a "
            f"`{max(jugador_hp, 0)}/{hp_max}`\n\n"
            f"{resumen}\n\n"
            f"💡 Mejora tu equipo con "
            f"`Wind cofre` y `Wind equipar`."
        )

    await reubicar_panel(
        ctx.guild,
        "rpg"
    )


# =========================================================
# COMANDO STATS
# =========================================================

@bot.command(name="stats")
async def stats(ctx):
    asegurar_registro_usuario(
        ctx.guild.id,
        ctx.author.id
    )

    (
        _,
        _,
        _,
        _,
        gemas,
        oleada,
        nivel_cofre,
    ) = obtener_datos_usuario(
        ctx.guild.id,
        ctx.author.id
    )

    atk, hp = calcular_stats(
        ctx.guild.id,
        ctx.author.id
    )

    embed = discord.Embed(
        title=(
            f"⚔️ Stats de "
            f"{ctx.author.display_name}"
        ),
        color=discord.Color.dark_red(),
    )

    embed.add_field(
        name="⚔️ Ataque",
        value=f"`{atk}`",
        inline=True,
    )

    embed.add_field(
        name="❤️ Vida",
        value=f"`{hp}`",
        inline=True,
    )

    embed.add_field(
        name="💎 Gemas",
        value=f"`{gemas}`",
        inline=True,
    )

    embed.add_field(
        name="🌊 Oleada",
        value=f"`{oleada}`",
        inline=True,
    )

    embed.add_field(
        name="🎁 Cofre",
        value=f"`Nivel {nivel_cofre}`",
        inline=True,
    )

    await ctx.send(
        embed=embed
    )


# =========================================================
# ERRORES DE PERMISOS
# =========================================================

@bot.event
async def on_command_error(ctx, error):

    if isinstance(
        error,
        commands.MissingPermissions
    ):
        await ctx.send(
            "🚫 No tienes permisos suficientes "
            "para usar este comando."
        )
        return

    if isinstance(
        error,
        commands.MissingRequiredArgument
    ):
        await ctx.send(
            "❌ Faltan argumentos para este comando."
        )
        return

    if isinstance(
        error,
        commands.BadArgument
    ):
        await ctx.send(
            "❌ Uno de los argumentos no es válido."
        )
        return

    if isinstance(
        error,
        commands.CommandNotFound
    ):
        return

    print(
        f"⚠️ Error en comando "
        f"{ctx.command}: {error}"
    )


# =========================================================
# EVENTO BOT ONLINE
# =========================================================

@bot.event
async def on_ready():
    print(
        f"🟢 Bot online como {bot.user}"
    )
    print(
        f"🕐 Fecha CDMX: {fecha_hoy()}"
    )


# =========================================================
# INICIO
# =========================================================

if not TOKEN:
    raise RuntimeError(
        "❌ No se encontró DISCORD_TOKEN. "
        "Configura la variable de entorno antes "
        "de iniciar el bot."
    )

bot.run(TOKEN)
```
