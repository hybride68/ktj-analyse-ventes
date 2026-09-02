import streamlit as st


def _format_value(key: str, value: float) -> str:
    if key in {"ca_total", "ca_total_annee"}:
        if value >= 1_000_000_000:
            return f"{value / 1_000_000_000:,.1f} Mds FCFA"
        if value >= 1_000_000:
            return f"{value / 1_000_000:,.1f} M FCFA"
        return f"{value:,.0f} FCFA"
    if key in {"panier_moyen"}:
        return f"{value:,.0f} FCFA"
    return f"{value:,.0f}"


def render_kpi_cards(kpis: dict, monthly_data: list, year=None) -> None:
    """Render premium KPI cards matching the dashboard mockup."""
    if not kpis:
        return

    if year and year != "Tout":
        st.markdown(f"<div style='display:flex;align-items:center;gap:10px;margin:22px 0 18px;'><span style='display:inline-block;width:14px;height:14px;background:#d7b02e;border-radius:4px;box-shadow:0 0 0 1px rgba(215,176,46,.25);'></span><span style='font-size:1.1rem;font-weight:600;color:#eef3ff;'>KPIs — Année {year}</span></div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='display:flex;align-items:center;gap:10px;margin:22px 0 18px;'><span style='display:inline-block;width:14px;height:14px;background:#d7b02e;border-radius:4px;box-shadow:0 0 0 1px rgba(215,176,46,.25);'></span><span style='font-size:1.1rem;font-weight:600;color:#eef3ff;'>KPIs — Toutes années</span></div>", unsafe_allow_html=True)

    cards = [
        {
            "key": "ca_total",
            "title": "CA Total",
            "icon": "💰",
            "color": "#d7b02e",
            "value": kpis.get("ca_total", 0),
            "desc": "Chiffre d'affaires global",
        },
        {
            "key": "nb_transactions",
            "title": "Transactions",
            "icon": "🧾",
            "color": "#d7b02e",
            "value": kpis.get("nb_transactions", 0),
            "desc": "Nombre total de ventes",
        },
        {
            "key": "panier_moyen",
            "title": "Panier Moyen",
            "icon": "🛒",
            "color": "#d7b02e",
            "value": kpis.get("panier_moyen", 0),
            "desc": "Valeur moyenne par vente",
        },
        {
            "key": "nb_clients_uniques",
            "title": "Clients",
            "icon": "👥",
            "color": "#d7b02e",
            "value": kpis.get("nb_clients_uniques", 0),
            "desc": "Clients distincts servis",
        },
        {
            "key": "nb_produits_uniques",
            "title": "Produits",
            "icon": "📦",
            "color": "#d7b02e",
            "value": kpis.get("nb_produits_uniques", 0),
            "desc": "Références vendues",
        },
    ]

    html_parts = []
    for card in cards:
        html_parts.append(
            f"""
            <div class="card" style="--accent:{card['color']};">
              <div class="card-icon" style="background:{card['color']}1a; border-color:{card['color']}55; color:{card['color']};">{card['icon']}</div>
              <div class="card-title">{card['title']}</div>
              <div class="card-value">{_format_value(card['key'], card['value'])}</div>
              <div class="card-desc">{card['desc']}</div>
            </div>
            """
        )

    html = f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
      .kpi-grid {{
        display: grid;
        grid-template-columns: repeat(5, minmax(150px, 1fr));
        gap: 18px;
        margin-top: 10px;
        width: 100%;
      }}
      .card {{
        position: relative;
        min-height: 184px;
        border-radius: 14px;
        padding: 20px 18px 14px;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        gap: 12px;
        background: rgba(28, 32, 38, 0.92);
        border: 1px solid rgba(143, 156, 176, 0.25);
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.02), 0 10px 22px rgba(0,0,0,0.18);
      }}
      .card-icon {{
        width: 36px;
        height: 36px;
        border-radius: 10px;
        display: grid;
        place-items: center;
        font-size: 20px;
        border: 1px solid rgba(255,255,255,0.08);
        background: rgba(255,255,255,0.03);
      }}
      .card-title {{
        font-size: 0.8rem;
        font-weight: 500;
        color: #dfe8f9;
        letter-spacing: 0.01em;
        opacity: 0.9;
      }}
      .card-value {{
        font-size: clamp(1.45rem, 2vw, 2.1rem);
        line-height: 1.15;
        font-weight: 700;
        color: #eff3ff;
        letter-spacing: -0.03em;
        font-family: 'Space Grotesk', sans-serif;
      }}
      .card-desc {{
        margin-top: auto;
        font-size: 0.72rem;
        line-height: 1.5;
        color: #8d98ac;
      }}
      @media (max-width: 1100px) {{
        .kpi-grid {{ grid-template-columns: repeat(3, minmax(150px, 1fr)); }}
      }}
      @media (max-width: 760px) {{
        .kpi-grid {{ grid-template-columns: repeat(2, minmax(140px, 1fr)); gap: 12px; }}
        .card {{ min-height: 168px; padding: 16px 14px 12px; }}
      }}
      @media (max-width: 480px) {{
        .kpi-grid {{ grid-template-columns: repeat(2, minmax(120px, 1fr)); }}
        .card-value {{ font-size: 1.15rem; }}
        .card-title {{ font-size: 0.72rem; }}
        .card-desc {{ font-size: 0.68rem; }}
      }}
    </style>
    <div class="kpi-grid">{''.join(html_parts)}</div>
    """

    st.components.v1.html(html, height=260)
