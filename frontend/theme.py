import streamlit as st


def render_sidebar(active_page: str = "Descriptive") -> None:
  """Render the premium navigation shell for the real dashboard pages."""
  with st.sidebar:
    st.markdown(
      """
      <div class='premium-sidebar-shell'>
        <div class='side-brand'>
          <div class='brand-badge'>▥</div>
          <div>
            <strong>SID-Dream</strong>
            <small>KTJ Investment</small>
          </div>
        </div>
      </div>
      """,
      unsafe_allow_html=True,
    )

    st.markdown("<div class='sidebar-nav-label'>app</div>", unsafe_allow_html=True)
    if active_page == "app":
        st.markdown("<div class='active-nav-pill'>app</div>", unsafe_allow_html=True)
    else:
        if st.button("app", key="nav_app", use_container_width=True):
            st.session_state["selected_page"] = "app"
            st.rerun()

    st.markdown("<div class='sidebar-section-label'>ANALYSE</div>", unsafe_allow_html=True)
    pages = [
        "Descriptive",
        "Diagnostique",
        "Predictive",
        "Prescriptive",
    ]
    if st.session_state.get("role") == "admin":
      pages.append("Gestion Utilisateurs")
    for page_name in pages:
        if page_name == active_page:
            st.markdown(f"<div class='active-nav-pill'>{page_name}</div>", unsafe_allow_html=True)
        else:
            if st.button(page_name, key=f"nav_{page_name}", use_container_width=True):
                st.session_state["selected_page"] = page_name
                st.rerun()

    st.markdown("<div class='sidebar-spacer'></div>", unsafe_allow_html=True)


def render_account_card() -> None:
    """Render the user account block after filters in the sidebar."""
    account_label = "Administrateur" if st.session_state.get("role") == "admin" else "Utilisateur standard"
    with st.sidebar:
        st.markdown(
          f"""
          <div class='sidebar-user-card'>
            <div class='user-avatar'>G</div>
            <div>
              <strong>{account_label}</strong>
              <small>Compte connecté</small>
            </div>
          </div>
          """,
          unsafe_allow_html=True,
        )


def apply_theme(hide_sidebar: bool = False) -> None:
    """Apply the shared visual language to every Streamlit page."""
    sidebar_hide_css = "[data-testid='stSidebar'], [data-testid='stSidebarCollapsedControl'] { display: none !important; }" if hide_sidebar else ""
    st.markdown(
        f"""
        <style>
          @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

          :root {{
            --bg: #05070b;
            --panel: #0c1118;
            --panel-strong: #101924;
            --sidebar: #0a0d13;
            --line: #1d2838;
            --ink: #edf3ff;
            --muted: #8a98ab;
            --gold: #d1a85a;
            --gold-soft: rgba(209,168,90,.15);
            --gold-strong: rgba(209,168,90,.24);
            --cyan: #31d0b1;
            --shadow: rgba(0,0,0,.22);
          }}

          .stApp {{
            background: linear-gradient(180deg, #04070b 0%, #0a101a 100%);
            color: var(--ink);
            font-family: 'DM Sans', sans-serif;
          }}

          [data-testid='stHeader'] {{ background: transparent; }}
          [data-testid='stAppViewContainer'] {{
            background: var(--bg);
          }}
          [data-testid='stAppViewContainer'] > .main {{
            padding-top: 0.5rem;
            padding-left: 0;
            padding-right: 0;
          }}
          .block-container {{
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
            padding-top: 1.2rem !important;
            max-width: none !important;
          }}
          [data-testid='stSidebar'] {{
            background: var(--sidebar);
            border-right: 1px solid var(--line);
            padding: 1.1rem 1rem 1rem;
            box-shadow: 12px 0 30px rgba(0,0,0,.18);
          }}
          div[data-testid='stSidebarNav'] {{ display: none !important; }}
          {sidebar_hide_css}
          [data-testid='stSidebar'] * {{ color: var(--ink); }}

          h1, h2, h3, h4 {{
            font-family: 'Space Grotesk', sans-serif;
            letter-spacing: 0;
            color: var(--ink);
          }}
          h1 {{ font-size: clamp(1.8rem, 3vw, 2.6rem); }}
          p, label, [data-testid='stMarkdownContainer'] {{ color: var(--muted); }}

          [data-testid='stMetric'] {{
            background: linear-gradient(180deg, #0d141d 0%, #0e1521 100%);
            border: 1px solid var(--line);
            border-radius: 16px;
            padding: 1rem 1.05rem;
            box-shadow: 0 14px 32px var(--shadow);
          }}
          [data-testid='stMetricLabel'] {{ color: var(--muted); }}
          [data-testid='stMetricValue'] {{
            color: var(--ink);
            font-family: 'Space Grotesk', sans-serif;
          }}

          .stButton > button, .stFormSubmitButton > button {{
            border: 1px solid rgba(255,255,255,.08);
            border-radius: 10px;
            background: rgba(255,255,255,.02);
            color: #edf3ff;
            font-weight: 600;
            box-shadow: none;
          }}
          .stButton > button:hover, .stFormSubmitButton > button:hover {{
            border-color: rgba(255,255,255,.14);
            background: rgba(255,255,255,.04);
            color: #ffffff;
          }}
          .active-nav-pill {{
            display: block;
            width: 100%;
            margin: 0.15rem 0;
            padding: 0.72rem 0.85rem;
            border-radius: 10px;
            border: 1px solid rgba(209,168,90,.55);
            background: linear-gradient(180deg, rgba(209,168,90,.14), rgba(209,168,90,.08));
            color: #f7f1d8;
            font-weight: 700;
            letter-spacing: 0.01em;
            box-shadow: inset 0 0 0 1px rgba(209,168,90,.12);
          }}

          div[data-baseweb='input'] > div,
          div[data-baseweb='select'] > div,
          [data-testid='stFileUploaderDropzone'],
          [data-testid='stDataEditor'] {{
            background: var(--panel);
            border-color: var(--line);
            color: var(--ink);
            border-radius: 12px;
          }}

          [data-testid='stExpander'], [data-testid='stAlert'] {{
            background: var(--panel);
            border-color: var(--line);
            border-radius: 14px;
          }}

          hr {{ border-color: var(--line); }}

          .dashboard-kicker {{
            color: var(--cyan);
            font-size: .74rem;
            font-weight: 700;
            letter-spacing: .12em;
            text-transform: uppercase;
            margin-bottom: .5rem;
          }}

          .welcome-email {{
            color: #4fa9ff;
            font-weight: 800;
          }}
          .welcome-subtitle {{
            color: var(--muted);
            font-size: 1.05rem;
            margin: 0 0 1.5rem;
          }}
          .welcome-section-title {{
            margin-top: 2rem;
            margin-bottom: 1rem;
            font-size: 1.05rem;
            color: var(--ink);
            font-weight: 600;
          }}
          .welcome-panel {{
            border: 1px solid rgba(79,169,255,.22);
            border-radius: 16px;
            background: linear-gradient(180deg, rgba(18,29,40,.8), rgba(13,20,28,.8));
            padding: 1.1rem 1.2rem;
            color: var(--ink);
            margin-bottom: 1.5rem;
          }}
          .welcome-panel p {{
            margin: 0 0 .8rem;
            color: var(--muted);
            line-height: 1.6;
          }}
          .welcome-panel p:last-child {{ margin-bottom: 0; }}
          .welcome-feature {{
            margin-bottom: .35rem;
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--ink);
          }}

          .premium-sidebar-shell {{
            padding: .35rem .4rem 1.1rem;
          }}
          .side-brand {{
            display: flex;
            align-items: center;
            gap: .7rem;
            padding: .35rem .2rem .9rem;
            border-bottom: 1px solid rgba(255,255,255,.06);
          }}
          .brand-badge {{
            width: 2.2rem;
            height: 2.2rem;
            border-radius: 10px;
            background: linear-gradient(180deg, #f5db6d 0%, #d7b02e 100%);
            color: #0a0d12;
            display: grid;
            place-items: center;
            font-weight: 700;
            font-size: 1.15rem;
          }}
          .side-brand strong {{
            display: block;
            color: var(--ink);
            font-size: 1.15rem;
            font-family: 'Space Grotesk', sans-serif;
          }}
          .side-brand small {{
            display: block;
            color: var(--muted);
            font-size: .68rem;
          }}

          .sidebar-nav-label {{
            margin: .2rem .35rem .6rem;
            font-size: .66rem;
            letter-spacing: .08em;
            text-transform: lowercase;
            color: rgba(153, 168, 187, .8);
            font-weight: 600;
          }}
          .sidebar-section-label {{
            margin: 1.2rem .35rem .55rem;
            font-size: .62rem;
            letter-spacing: .18em;
            text-transform: uppercase;
            color: rgba(153, 168, 187, .75);
            font-weight: 700;
          }}

          .sidebar-nav-item {{
            display: flex;
            align-items: center;
            padding: .7rem .7rem;
            margin: .14rem 0;
            border-radius: 10px;
            color: #aab6c7;
            background: transparent;
            border-left: 2px solid transparent;
            transition: all .2s ease;
          }}
          .sidebar-nav-item.secondary {{
            color: #aab6c7;
          }}
          .premium-nav-item.active {{
            background: rgba(255,255,255,.04);
            border-left-color: var(--gold);
            color: var(--ink);
            box-shadow: inset 0 0 0 1px rgba(255,255,255,.02);
          }}

          .sidebar-divider {{
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,.08), transparent);
            margin: 1rem 0 .3rem;
          }}

          .sidebar-spacer {{ min-height: 8rem; }}
          .sidebar-user-card {{
            display: flex;
            align-items: center;
            gap: .75rem;
            padding: .8rem .6rem;
            border-top: 1px solid rgba(255,255,255,.08);
            margin-top: .5rem;
          }}
          .user-avatar {{
            width: 2.05rem;
            height: 2.05rem;
            border-radius: 50%;
            background: rgba(215,176,46,.12);
            color: var(--gold);
            display: grid;
            place-items: center;
            font-weight: 700;
          }}
          .sidebar-user-card strong {{
            display: block;
            color: var(--ink);
            font-size: .92rem;
          }}
          .sidebar-user-card small {{
            display: block;
            color: var(--muted);
            font-size: .65rem;
          }}

          .login-copy-hero {{
            min-height: 510px;
            padding: 3.5rem 3rem;
            background: #050505;
            clip-path: polygon(0 0, 100% 0, 72% 100%, 0 100%);
            color: #ffffff;
          }}
          .login-panel-wrap {{
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 500px;
            padding-top: 1rem;
          }}
          div[data-testid='stForm'] {{
            width: min(100%, 26rem);
            margin: 0 auto;
            padding: 2rem 2.5rem 1.5rem;
            background: #f5f5f3;
            border: 0;
            border-radius: 0;
          }}
          .login-panel-heading h3 {{
            margin: 0 0 .2rem;
            font-size: 1.8rem;
            color: #111111;
          }}
          .login-panel-heading p {{
            margin: 0 0 1.3rem;
            color: #666666;
          }}
          .login-panel {{
            width: 100%;
            max-width: 420px;
            border: 1px solid rgba(255,255,255,.08);
            border-radius: 18px;
            background: rgba(12,17,24,.82);
            padding: 1.4rem 1.15rem 1.2rem;
            box-shadow: 0 18px 40px rgba(0,0,0,.24);
            margin-top: 0.6rem;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
          }}
          .login-panel h3 {{
            margin: 0 0 .25rem;
            font-size: 1.9rem;
            color: var(--ink);
          }}
          .login-panel p {{
            margin: 0 0 1.3rem;
            color: var(--muted);
          }}
          .login-panel .stTextInput {{
            margin-top: 0.2rem;
          }}
          .login-panel .stTextInput > div > div {{
            background: rgba(12,17,24,.72);
            border-color: rgba(255,255,255,.08);
          }}

          .login-brand {{
            display: flex;
            align-items: center;
            gap: .8rem;
            margin-bottom: 3rem;
          }}
          .login-brand span {{
            display: grid;
            place-items: center;
            width: 2.8rem;
            height: 2.8rem;
            border-radius: 14px;
            background: linear-gradient(180deg, #f6d86d 0%, #d7b02e 100%);
            color: #090d12;
            font-size: 1.5rem;
            font-weight: 700;
          }}
          .login-brand strong {{ font-size: 1.1rem; color: var(--ink); }}
          .login-brand small {{ display: block; color: var(--muted); }}

          .login-copy h2 {{
            font-family: Georgia, serif;
            font-size: clamp(2.2rem, 4vw, 4rem);
            line-height: 1.04;
            margin: 0;
          }}
          .login-copy-hero h2 {{
            font-family: Georgia, serif;
            font-size: clamp(2.2rem, 4vw, 4rem);
            line-height: 1.04;
            margin: 0;
          }}
          .login-copy em {{ color: var(--gold); }}
          .login-copy p {{
            max-width: 31rem;
            line-height: 1.7;
            margin-top: 1.2rem;
            color: var(--muted);
          }}

          .login-stats {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: .8rem;
            margin-top: 3rem;
            max-width: 35rem;
          }}
          .login-stat {{
            background: rgba(15,21,28,.9);
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: .9rem .6rem;
            text-align: center;
            box-shadow: 0 12px 22px rgba(0,0,0,.14);
          }}
          .login-stat strong {{
            display: block;
            color: var(--gold);
            font-size: 1.1rem;
          }}
          .login-stat small {{ color: var(--muted); font-size: .63rem; }}

          .login-panel {{
            width: min(100%, 26rem);
            justify-self: end;
            background: #f5f5f3;
            border: 0;
            border-radius: 0;
            padding: 2rem 2.5rem 1rem;
            box-shadow: none;
          }}
          .login-panel h3 {{ font-size: 1.8rem; margin-bottom: .2rem; color: #111111; }}
          .login-panel p {{ margin-top: 0; color: #666666; }}

          /* Keep the login surface light while the authenticated app stays dark. */
          [data-testid='stAppViewContainer'] > .main:has(.login-page-marker) {{
            background: #f5f5f3;
          }}
          [data-testid='stAppViewContainer'] > .main:has(.login-page-marker) .block-container {{
            padding: 0 !important;
          }}
          [data-testid='stAppViewContainer'] > .main:has(.login-page-marker) div[data-testid='stForm'] {{
            box-shadow: none;
          }}
          [data-testid='stAppViewContainer'] > .main:has(.login-page-marker) [data-testid='stHorizontalBlock'] {{
            min-height: 100vh;
            align-items: stretch;
          }}
          [data-testid='stAppViewContainer'] > .main:has(.login-page-marker) [data-testid='stTextInput'] input {{
            background: transparent;
            border: 0;
            border-bottom: 1px solid #666666;
            border-radius: 0;
            color: #111111;
          }}
          [data-testid='stAppViewContainer'] > .main:has(.login-page-marker) [data-testid='stTextInput'] label {{
            color: #555555;
          }}
          [data-testid='stAppViewContainer'] > .main:has(.login-page-marker) .stButton > button {{
            background: #050505;
            border-color: #050505;
            border-radius: 999px;
            color: #ffffff;
            margin-top: .7rem;
          }}

          @media (max-width: 880px) {{
            .login-shell {{
              grid-template-columns: 1fr;
              gap: 2rem;
              padding: 1rem;
            }}
            .login-panel {{
              width: 100%;
              justify-self: stretch;
            }}
            .login-stats {{
              grid-template-columns: repeat(2, minmax(0, 1fr));
              max-width: none;
            }}
            .login-copy-hero {{
              min-height: auto;
              clip-path: none;
              padding: 2rem 1.5rem;
            }}
            .login-panel {{
              padding: 2rem 1.5rem;
            }}
            div[data-testid='stForm'] {{
              padding: 2rem 1.5rem 1.5rem;
            }}
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )