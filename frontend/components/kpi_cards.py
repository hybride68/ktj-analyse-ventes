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
    """Render a glassmorphism KPI card grid using embedded HTML/CSS."""
    if not kpis:
        return

    # Titre de section avec l'année sélectionnée
    if year and year != "Tout":
        st.markdown(f"### 📈 KPIs — Année {year}")
    else:
        st.markdown("### 📈 KPIs — Toutes années")

    cards = [
        {
            "key": "ca_total",
            "title": "CA Total",
            "icon": "💰",
            "color": "#8B5CF6",
            "value": kpis.get("ca_total", 0),
            "desc": "Chiffre d'affaires global",
        },
        {
            "key": "nb_transactions",
            "title": "Transactions",
            "icon": "🧾",
            "color": "#22D3EE",
            "value": kpis.get("nb_transactions", 0),
            "desc": "Nombre total de ventes",
        },
        {
            "key": "panier_moyen",
            "title": "Panier Moyen",
            "icon": "🛒",
            "color": "#F472B6",
            "value": kpis.get("panier_moyen", 0),
            "desc": "Valeur moyenne par vente",
        },
        {
            "key": "nb_clients_uniques",
            "title": "Clients",
            "icon": "👥",
            "color": "#FB923C",
            "value": kpis.get("nb_clients_uniques", 0),
            "desc": "Clients distincts servis",
        },
        {
            "key": "nb_produits_uniques",
            "title": "Produits",
            "icon": "📦",
            "color": "#34D399",
            "value": kpis.get("nb_produits_uniques", 0),
            "desc": "Références vendues",
        },
    ]

    html_parts = []
    for card in cards:
        html_parts.append(
            f"""
            <div class="card" style="--accent:{card['color']};">
              <div class="card-icon">{card['icon']}</div>
              <div class="card-title">{card['title']}</div>
              <div class="card-value">{_format_value(card['key'], card['value'])}</div>
              <div class="card-desc">{card['desc']}</div>
            </div>
            """
        )

    html = f"""
    <style>
      .kpi-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 14px;
        padding: 8px;
      }}
      .card {{
        position: relative;
        min-height: 200px;
        border-radius: 18px;
        padding: 16px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 6px;
        background: rgba(255,255,255,0.12);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(255,255,255,0.18);
        box-shadow: 0 8px 32px rgba(0,0,0,0.25);
        overflow: hidden;
        transition: all 0.3s ease;
      }}
      .card:hover {{
        box-shadow: 0 12px 40px rgba(255,255,255,0.15);
        transform: translateY(-4px);
        transition: all 0.3s ease;
      }}
      .card-icon {{ font-size: 26px; }}
      .card-title {{ font-size: 14px; font-weight: 600; opacity: 0.9; }}
      .card-value {{
        font-size: 20px;
        font-weight: 700;
        margin-top: 2px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }}
      .card-desc {{ font-size: 12px; opacity: 0.8; }}
      @media (max-width: 480px) {{
        .kpi-grid {{
          grid-template-columns: repeat(2, 1fr);
          gap: 10px;
          padding: 4px;
        }}
        .card {{
          min-height: 160px;
          padding: 12px;
        }}
        .card-icon {{ font-size: 22px; }}
        .card-title {{ font-size: 12px; }}
        .card-value {{
          font-size: 16px;
          white-space: normal;
          word-break: break-word;
        }}
        .card-desc {{ font-size: 11px; }}
      }}
    </style>
    <div class="kpi-grid">{''.join(html_parts)}</div>
    """

    st.components.v1.html(html, height=320)
