import datetime
import pandas as pd
import streamlit as st
import altair as alt
import requests
import json
import base64

# ----------------------
# Streamlit Page Config
# ----------------------
st.set_page_config(page_title="Tickets de soporte", page_icon="🎫")

# ----------------------
# Title and Description
# ----------------------
st.title("🎫 Tickets de soporte")
st.write(
    """
    Esta aplicación permite crear, editar y analizar tickets de soporte.
    Los tickets se almacenan temporalmente en la sesión y se envían a n8n
    para persistencia en Supabase.
    """
)

# ----------------------
# Initialize DataFrame
# ----------------------
if "df" not in st.session_state:
    # Create an empty DataFrame with the required columns, but no rows.
    columns = ["ID", "Problema", "Estado", "Prioridad", "Fecha de envío"]
    empty_df = pd.DataFrame(columns=columns)
    st.session_state.df = empty_df
else:
    # If the DataFrame already exists, rename columns if previously used English names
    df = st.session_state.df
    if "Status" in df.columns:
        df = df.rename(
            columns={
                "Status": "Estado",
                "Priority": "Prioridad",
                "Date Submitted": "Fecha de envío",
                "Issue": "Problema"
            }
        )
        st.session_state.df = df

# ----------------------
# Reset Session Button
# ----------------------
if st.button("Resetear sesión"):
    st.session_state.clear()
    st.experimental_rerun()

# ----------------------
# Add New Ticket
# ----------------------
st.header("Agregar ticket")
with st.form("formulario_agregar_ticket"):
    problema = st.text_area("Describa el problema")
    prioridad = st.selectbox("Prioridad", ["Alta", "Media", "Baja"])
    enviado = st.form_submit_button("Enviar")

if enviado:
    # Generate a new ticket ID based on the highest existing ID or start from 1000 if none exist
    if len(st.session_state.df) == 0:
        last_ticket_number = 1000
    else:
        last_ticket_number = int(max(st.session_state.df["ID"]).split("-")[1])

    new_id = f"TICKET-{last_ticket_number + 1}"
    today_str = datetime.datetime.now().strftime("%d-%m-%Y")

    df_new = pd.DataFrame(
        [
            {
                "ID": new_id,
                "Problema": problema,
                "Estado": "Abierto",
                "Prioridad": prioridad,
                "Fecha de envío": today_str,
            }
        ]
    )

    # Show success message and new ticket details
    st.write("¡Ticket enviado! Detalles del ticket:")
    st.dataframe(df_new, use_container_width=True, hide_index=True)

    # Update local session DataFrame
    st.session_state.df = pd.concat([df_new, st.session_state.df], ignore_index=True)

    # ----------------------
    # Send to n8n Webhook
    # ----------------------
    webhook_url = "https://n8n.yourdomain.com/webhook/my-bug-ticket-webhook"
    username = "myWebhookUser"
    password = "superSecret123"

    auth_string = f"{username}:{password}"
    auth_bytes = auth_string.encode("utf-8")
    base64_auth = base64.b64encode(auth_bytes).decode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {base64_auth}"
    }

    payload = {
        "ticket_id": new_id,
        "problema": problema,
        "estado": "Abierto",
        "prioridad": prioridad,
        "fecha_envio": today_str
    }

    try:
        response = requests.post(webhook_url, headers=headers, json=payload)
        if response.status_code == 200:
            st.success("Ticket guardado en la base de datos (n8n -> Supabase).")
        else:
            st.error(f"Error al enviar a n8n: {response.text}")
    except Exception as e:
        st.error(f"Error al conectar con n8n: {e}")

# ----------------------
# Show Existing Tickets
# ----------------------
st.header("Tickets existentes")
st.write(f"Número de tickets: `{len(st.session_state.df)}`")
st.info(
    "Puede editar los tickets haciendo doble clic en una celda. "
    "Observe cómo los gráficos se actualizan automáticamente. "
    "También puede ordenar la tabla haciendo clic en los encabezados de las columnas.",
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

# Update session state with edited data
st.session_state.df = edited_df

# ----------------------
# Statistics and Charts
# ----------------------
st.header("Estadísticas")

col1, col2, col3 = st.columns(3)
num_tickets_abiertos = len(edited_df[edited_df["Estado"] == "Abierto"])
col1.metric(label="Tickets abiertos", value=num_tickets_abiertos, delta=10)
col2.metric(label="Tiempo de primera respuesta (horas)", value=5.2, delta=-1.5)
col3.metric(label="Tiempo promedio de resolución (horas)", value=16, delta=2)

# Chart: Ticket Status by Month
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

# Chart: Ticket Priority
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
