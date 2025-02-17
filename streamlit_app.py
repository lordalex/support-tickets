import datetime
import random

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

# Configurar la página.
st.set_page_config(page_title="Tickets de soporte", page_icon="🎫")
st.title("🎫 Tickets de soporte")
st.write(
    """
    Esta aplicación muestra cómo construir una herramienta interna en Streamlit. Aquí, 
    estamos implementando un flujo de trabajo para tickets de soporte. El usuario puede 
    crear un ticket, editar los tickets existentes y ver algunas estadísticas.
    """
)

# Crear o actualizar el DataFrame de tickets en session_state.
if "df" not in st.session_state:
    # Fijar la semilla para reproducibilidad.
    np.random.seed(42)

    # Crear algunas descripciones ficticias de problemas.
    descripciones_problemas = [
        "Problemas de conectividad en la oficina",
        "La aplicación se bloquea al iniciar",
        "La impresora no responde a los comandos de impresión",
        "Tiempo de inactividad del servidor de correo",
        "Falla en la copia de seguridad de datos",
        "Problemas de autenticación de inicio de sesión",
        "Degradación del rendimiento del sitio web",
        "Vulnerabilidad de seguridad identificada",
        "Falla de hardware en el cuarto de servidores",
        "Empleado no puede acceder a archivos compartidos",
        "Falla en la conexión a la base de datos",
        "La aplicación móvil no sincroniza datos",
        "Problemas en el sistema de telefonía VoIP",
        "Problemas de conexión VPN para empleados remotos",
        "Actualizaciones del sistema causando problemas de compatibilidad",
        "El servidor de archivos se está quedando sin espacio",
        "Alertas del sistema de detección de intrusiones",
        "Errores en el sistema de inventario",
        "Los datos del cliente no se cargan en el CRM",
        "La herramienta de colaboración no envía notificaciones",
    ]

    # Generar el DataFrame con 100 tickets.
    data = {
        "ID": [f"TICKET-{i}" for i in range(1100, 1000, -1)],
        "Problema": np.random.choice(descripciones_problemas, size=100),
        "Estado": np.random.choice(["Abierto", "En Progreso", "Cerrado"], size=100),
        "Prioridad": np.random.choice(["Alta", "Media", "Baja"], size=100),
        "Fecha de envío": [
            datetime.date(2023, 6, 1) + datetime.timedelta(days=random.randint(0, 182))
            for _ in range(100)
        ],
    }
    df = pd.DataFrame(data)
    st.session_state.df = df
else:
    # Si el DataFrame ya existe, verificar y renombrar columnas si es necesario.
    df = st.session_state.df
    if "Status" in df.columns:
        df = df.rename(columns={
            "Status": "Estado",
            "Priority": "Prioridad",
            "Date Submitted": "Fecha de envío",
            "Issue": "Problema"
        })
        st.session_state.df = df

# (Opcional) Botón para resetear la sesión si deseas comenzar de nuevo.
if st.button("Resetear sesión"):
    st.session_state.clear()
    st.experimental_rerun()

# Sección para agregar un ticket.
st.header("Agregar ticket")
with st.form("formulario_agregar_ticket"):
    problema = st.text_area("Describa el problema")
    prioridad = st.selectbox("Prioridad", ["Alta", "Media", "Baja"])
    enviado = st.form_submit_button("Enviar")

if enviado:
    # Crear un DataFrame para el nuevo ticket y agregarlo al DataFrame en session_state.
    ultimo_ticket_numero = int(max(st.session_state.df.ID).split("-")[1])
    hoy = datetime.datetime.now().strftime("%d-%m-%Y")
    df_nuevo = pd.DataFrame(
        [
            {
                "ID": f"TICKET-{ultimo_ticket_numero+1}",
                "Problema": problema,
                "Estado": "Abierto",
                "Prioridad": prioridad,
                "Fecha de envío": hoy,
            }
        ]
    )
    st.write("¡Ticket enviado! Detalles del ticket:")
    st.dataframe(df_nuevo, use_container_width=True, hide_index=True)
    st.session_state.df = pd.concat([df_nuevo, st.session_state.df], axis=0)

# Sección para ver y editar tickets existentes.
st.header("Tickets existentes")
st.write(f"Número de tickets: `{len(st.session_state.df)}`")
st.info(
    "Puede editar los tickets haciendo doble clic en una celda. Observe cómo los gráficos "
    "actualizan automáticamente. También puede ordenar la tabla haciendo clic en los encabezados "
    "de las columnas.",
    icon="✍️",
)

edited_df = st.data_editor(
    st.session_state.df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Estado": st.column_config.SelectboxColumn(
            "Estado",
            help="Estado del ticket",
            options=["Abierto", "En Progreso", "Cerrado"],
            required=True,
        ),
        "Prioridad": st.column_config.SelectboxColumn(
            "Prioridad",
            help="Prioridad del ticket",
            options=["Alta", "Media", "Baja"],
            required=True,
        ),
    },
    disabled=["ID", "Fecha de envío"],
)

# Sección para mostrar estadísticas y gráficos.
st.header("Estadísticas")
col1, col2, col3 = st.columns(3)
num_tickets_abiertos = len(st.session_state.df[st.session_state.df.Estado == "Abierto"])
col1.metric(label="Tickets abiertos", value=num_tickets_abiertos, delta=10)
col2.metric(label="Tiempo de primera respuesta (horas)", value=5.2, delta=-1.5)
col3.metric(label="Tiempo promedio de resolución (horas)", value=16, delta=2)

st.write("")
st.write("##### Estado de tickets por mes")
estado_grafico = (
    alt.Chart(edited_df)
    .mark_bar()
    .encode(
        x="month(`Fecha de envío`):O",
        y="count():Q",
        xOffset="Estado:N",
        color="Estado:N",
    )
    .configure_legend(
        orient="bottom", titleFontSize=14, labelFontSize=14, titlePadding=5
    )
)
st.altair_chart(estado_grafico, use_container_width=True, theme="streamlit")

st.write("##### Prioridades actuales de los tickets")
prioridad_grafico = (
    alt.Chart(edited_df)
    .mark_arc()
    .encode(theta="count():Q", color="Prioridad:N")
    .properties(height=300)
    .configure_legend(
        orient="bottom", titleFontSize=14, labelFontSize=14, titlePadding=5
    )
)
st.altair_chart(prioridad_grafico, use_container_width=True, theme="streamlit")
