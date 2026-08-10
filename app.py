import streamlit as st
import subprocess
import time
import os
import json
import re

st.set_page_config(
    page_title="Analytics Stream Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    
    /* BADGES (ETIQUETAS) */
    .evt-badge {
        padding: 6px 12px; border-radius: 6px; font-weight: 800; font-size: 0.9rem;
        text-transform: uppercase; letter-spacing: 1px; display: inline-block; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.3); margin-bottom: 5px;
    }
    .badge-ecom { background: linear-gradient(135deg, #7209b7, #b5179e); color: #fff; border: 1px solid #f72585; }
    .badge-view { background: linear-gradient(135deg, #0077b6, #00b4d8); color: #fff; border: 1px solid #90e0ef; }
    .badge-intr { background: linear-gradient(135deg, #2a9d8f, #264653); color: #fff; border: 1px solid #2a9d8f; }
    .badge-err  { background: linear-gradient(135deg, #d00000, #9d0208); color: #fff; border: 1px solid #ffba08; }
    .badge-sys  { background: #343a40; color: #adb5bd; border: 1px solid #495057; }
    .badge-start { 
        background: #ffffff; color: #000000; border: 1px solid #e0e0e0; 
        box-shadow: 0 0 10px rgba(255,255,255,0.4); /* Brilho branco */
    }
    .badge-promo { 
        background: linear-gradient(135deg, #ff8800, #ffaa00); color: #000000; border: 1px solid #ffcc00; 
    }
    
    /* ALERTA DE LOG CORTADO */
    .badge-warn { 
        background: rgba(255, 166, 0, 0.15); color: #ff9f1c; 
        border: 1px dashed #ff9f1c; font-size: 0.7rem; padding: 4px 8px; margin-left: 10px;
        vertical-align: middle; border-radius: 4px;
    }

    /* ALERTA DE BUG (BADGE DO TÍTULO) */
    .badge-bug { 
        background: rgba(255, 77, 77, 0.2); color: #ff6b6b; 
        border: 1px dashed #ff6b6b; font-size: 0.75rem; padding: 4px 8px; margin-left: 10px;
        vertical-align: middle; font-weight: bold; border-radius: 4px;
        display: inline-flex; align-items: center; gap: 5px;
    }

    /* TIMESTAMP */
    .timestamp-label {
        font-family: 'Consolas', monospace; font-size: 0.75rem; color: #6c757d; 
        margin-bottom: 2px; display: block;
    }

    /* GRID DE PRODUTOS */
    .items-container { display: flex; flex-direction: column; gap: 12px; margin-top: 10px; }
    
    .glass-card {
        background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px; overflow: hidden;
    }
    
    .card-header {
        background: rgba(255, 255, 255, 0.05); padding: 8px 12px; font-size: 0.75rem;
        color: #ff9f1c; font-weight: 700; text-transform: uppercase;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1); display: flex; justify-content: space-between;
    }
    
    .grid-row {
        display: grid; grid-template-columns: 140px 1fr; 
        border-bottom: 1px solid rgba(255,255,255,0.05);
        font-family: 'Consolas', monospace; font-size: 0.8rem;
    }
    .grid-row:last-child { border-bottom: none; }
    
    .grid-key {
        padding: 6px 12px; color: #a8dadc; border-right: 1px solid rgba(255,255,255,0.05);
        background: rgba(0,0,0,0.1); display: flex; align-items: center; overflow-wrap: break-word;
    }
    
    .grid-val { padding: 6px 12px; color: #f1faee; word-break: break-word; align-self: center; }

    /* PARAMS NORMAIS */
    .param-row {
        display: flex; justify-content: space-between; padding: 6px 0; 
        border-bottom: 1px solid rgba(255,255,255,0.05);
        font-family: 'Consolas', monospace; font-size: 0.85rem;
    }
    .p-key { color: #8d99ae; font-weight: 600; }
    .p-val { color: #edf2f4; text-align: right; word-break: break-all; }

    /* PARAMS COM ERRO (DESTAQUE VERMELHO) */
    .param-row-error {
        display: flex; justify-content: space-between; padding: 8px 10px; 
        border: 1px solid #ff4d4d; /* Borda vermelha */
        background-color: rgba(255, 77, 77, 0.15); /* Fundo vermelho fraco */
        border-radius: 6px;
        margin-bottom: 6px; margin-top: 6px;
        font-family: 'Consolas', monospace; font-size: 0.9rem;
    }
    .param-row-error .p-key { color: #ff6b6b; font-weight: 800; display: flex; align-items: center; gap: 5px; } 
    .param-row-error .p-val { color: #ffffff; font-weight: 800; text-align: right; word-break: break-all; }

    /* BOTÃO DE DOCUMENTAÇÃO */
    .doc-btn {
        display: block; width: 100%; text-align: center;
        background: rgba(255, 77, 77, 0.1); border: 1px solid #ff4d4d; color: #ff6b6b;
        padding: 10px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 15px;
        transition: all 0.3s;
    }
    .doc-btn:hover { background: #ff4d4d; color: white; }

    div[data-testid="stExpander"] { border: 0; background-color: #1a1a1d; margin-bottom: 15px; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

def resgatar_log_quebrado(log_text):
    original = log_text
    is_truncated = False
    open_b = log_text.count("Bundle[{")
    close_b = log_text.count("}]")
    raw_opens = log_text.count("[")
    raw_closes = log_text.count("]")
    open_arr = raw_opens - open_b 
    if open_arr < 0: open_arr = raw_opens
    close_arr = raw_closes - close_b
    if close_arr < 0: close_arr = raw_closes

    if open_b > close_b or open_arr > close_arr:
        is_truncated = True
        last_comma = log_text.rfind(',')
        if last_comma != -1: log_text = log_text[:last_comma]
        curr_open_b = log_text.count("Bundle[{")
        curr_close_b = log_text.count("}]")
        curr_raw_opens = log_text.count("[")
        curr_open_arr = curr_raw_opens - curr_open_b
        if curr_open_arr < 0: curr_open_arr = curr_raw_opens
        curr_raw_closes = log_text.count("]")
        curr_close_arr = curr_raw_closes - curr_close_b
        if curr_close_arr < 0: curr_close_arr = curr_raw_closes
        diff_arr = curr_open_arr - curr_close_arr
        if diff_arr > 0: log_text += "]" * diff_arr
        diff_b = curr_open_b - curr_close_b
        if diff_b > 0: log_text += "}]" * diff_b

    return log_text, is_truncated

def parse_nested_structure(value):
    #arruma a desgraça do budle
    if isinstance(value, str):
        if value.startswith("Bundle[{") and value.endswith("}]"):
            content = value[7:-1]
            return parse_key_value_pairs(content)
        if value.startswith("[") and value.endswith("]"):  
            return [parse_nested_structure(item.strip()) for item in split_list_items(value[1:-1])]
    return value

def split_list_items(s):
    result = []
    stack = []
    current = ""
    for char in s:
        if char == "[": stack.append(char)
        elif char == "]": stack.pop()
        if char == "," and not stack:
            result.append(current); current = ""
        else: current += char
    if current: result.append(current)
    return result

def parse_key_value_pairs(s):
    result = []
    stack = []
    current = ""
    for char in s:
        if char == "[": stack.append(char)
        elif char == "]": stack.pop()
        if char == "," and not stack:
            result.append(current); current = ""
        else: current += char
    if current: result.append(current)

    parsed_dict = {}
    for pair in result:
        try:
            if "=" in pair:
                key, value = pair.split("=", 1)
                key = key.strip().replace("{","").replace("}","")
                value = value.strip()
                if not "Bundle[{" in value: value = value.replace("{","").replace("}","")
                if key in ["params", "items"]: parsed_dict[key] = [parse_nested_structure(value)]
                else: parsed_dict[key] = parse_nested_structure(value)
        except: pass
    return parsed_dict

def extract_target_keys(s, target_keys):
    parsed_dict = parse_key_value_pairs(s)
    return {key: parsed_dict[key] for key in target_keys if key in parsed_dict}

def render_items_complete(items_raw):
    items_list = items_raw
    if isinstance(items_raw, list) and len(items_raw) > 0:
        if isinstance(items_raw[0], list): items_list = items_raw[0]
            
    if not isinstance(items_list, list): return ""

    html_parts = ['<div class="items-container">']
    for idx, item in enumerate(items_list):
        if isinstance(item, dict):
            header_title = item.get('item_name', item.get('name', f'ITEM #{idx+1}'))
            item_id = item.get('item_id', '')
            header_sub = f"ID: {item_id}" if item_id else f"#{idx+1}"

            html_parts.append(f'<div class="glass-card">')
            html_parts.append(f'<div class="card-header"><span>{header_title}</span><span style="opacity:0.6">{header_sub}</span></div>')
            for k, v in item.items():
                val_display = str(v)
                if isinstance(v, (dict, list)): val_display = json.dumps(v)
                html_parts.append(f'<div class="grid-row"><div class="grid-key">{k}</div><div class="grid-val">{val_display}</div></div>')
            html_parts.append('</div>') 
    html_parts.append('</div>')
    return "".join(html_parts)

def iniciar_adb(package_name): 
    if 'processo_adb' in st.session_state and st.session_state['processo_adb'] is not None: return
    arquivo_log = "log_android.txt"

    subprocess.run(["adb", "logcat", "-c"], shell=True)
    subprocess.run(["adb", "logcat", "-G", "16M"], shell=True) 
    cmds = [
        ["adb", "shell", "setprop", "debug.firebase.analytics.app", package_name], 
        ["adb", "shell", "setprop", "log.tag.FA", "VERBOSE"],
        ["adb", "shell", "setprop", "log.tag.FA-SVC", "VERBOSE"]
    ]
    for c in cmds: subprocess.run(c, shell=True)
    open(arquivo_log, "w").close() 
    log_file = open(arquivo_log, "a")
    processo = subprocess.Popen(["adb", "logcat", "-v", "time", "-s", "FA", "FA-SVC"], stdout=log_file, stderr=subprocess.STDOUT, shell=True)
    st.session_state['processo_adb'] = processo
    st.session_state['arquivo_log_handle'] = log_file
    st.session_state['rodando'] = True

def parar_adb():
    if 'processo_adb' in st.session_state and st.session_state['processo_adb']:
        st.session_state['processo_adb'].terminate()
        st.session_state['processo_adb'] = None
    if 'arquivo_log_handle' in st.session_state and st.session_state['arquivo_log_handle']:
        st.session_state['arquivo_log_handle'].close()
        st.session_state['arquivo_log_handle'] = None
    st.session_state['rodando'] = False
    st.rerun()

with st.sidebar:
    st.markdown("### 🎛️ Controle Maneiro")
    
    package_input = st.text_input(
        "Nome do Pacote (Package Name):", 
        value="com.teste.seila",
        help="Ex: com.dominio.app"
    )

    if not st.session_state.get('rodando', False):
        if st.button("🔌 CONECTAR E INICIAR", type="primary", use_container_width=True):
            open("log_android.txt", "w").close()
            iniciar_adb(package_input) 
            st.rerun()
    else:
        st.markdown("<div style='text-align:center; color:#00ff00; margin:10px;'>● CAPTURANDO</div>", unsafe_allow_html=True)
        if st.button("❌ PARAR", type="secondary", use_container_width=True): parar_adb()
        if st.button("🗑️ LIMPAR", use_container_width=True):
            open("log_android.txt", "w").close()
            st.rerun()

st.title("BangBangBang 🐔")
st.markdown("---")

if st.session_state.get('rodando', False):
    placeholder = st.empty()
    caminho_arquivo = "log_android.txt"
    if os.path.exists(caminho_arquivo):
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            f.seek(0, 2)
            with st.container():
                while st.session_state['rodando']:
                    linha = f.readline()
                    if linha:
                        try:
                            if "Logging event: " in linha:
                                parts = linha.split("Logging event: ")
                                timestamp_raw = linha.split(" ")[1] 
                                raw_content = parts[1]
                                
                                content_to_parse, was_truncated = resgatar_log_quebrado(raw_content)
                                data = extract_target_keys(content_to_parse, ["name", "params"])
                                event_name = data.get("name", "unknown")
                                params = data.get("params", {})
                                
                                if isinstance(params, list) and len(params) > 0: params = params[0]
                                if not isinstance(params, dict): params = {}

                                if "session_start" in event_name:
                                    badge_cls, icon = "badge-start", "🏁"
                                elif any(x in event_name for x in ["add_payment_info", "add_shipping_info", "add_to_cart", "begin_checkout", "purchase", "remove_from_cart", "select_item", "view_cart", "view_item", "view_item_list"]):
                                    badge_cls, icon = "badge-ecom", "🛍️"
                                elif "screen_view" in event_name:
                                    badge_cls, icon = "badge-view", "👀"
                                elif any(x in event_name for x in ["purchase"]):
                                    badge_cls, icon = "badge-intr", "💸"
                                elif any(x in event_name for x in ["view_promotion", "select_promotion"]):
                                    badge_cls, icon = "badge-promo", "🎟️"
                                else:
                                    badge_cls, icon = "badge-sys", "🔹"

                                error_keys_map = [
                                    "ga_error_length", "ga_error_length(_el)", "_el",
                                    "ga_error_value", "ga_error_value(_ev)", "_ev",
                                    "ga_error", "ga_error(_err)", "_err"
                                ]
                                has_any_error = any(k in params for k in error_keys_map)
                                
                                is_missing_screen_name = False
                                if "screen_view" in event_name:
                                    if not any(k in params for k in ["ga_screen", "_sn", "ga_screen(_sn)"]):
                                        is_missing_screen_name = True

                                alerts_html = ""
                                if was_truncated:
                                    alerts_html += '<span class="badge-warn">⚠️ LOG CORTADO ( > 4KB )</span>'
                                if has_any_error:
                                    alerts_html += '<span class="badge-bug">🐛 BUG DETECTADO (Verificar Erro)</span>'
                                
                                if is_missing_screen_name:
                                    alerts_html += '<span class="badge-bug" style="border-color: #ff0000; color:#ff0000;">⚠️ FALTA SCREEN_NAME</span>'
                                
                                st.markdown(f"""
                                <div style="margin-top: 20px;">
                                    <span class="timestamp-label">⏱ {timestamp_raw}</span>
                                    <span class="evt-badge {badge_cls}">{icon} {event_name}</span>
                                    {alerts_html}
                                </div>
                                """, unsafe_allow_html=True)
                                
                                with st.expander("Ver detalhes", expanded=True if "purchase" in event_name or is_missing_screen_name else False):
                                    items_data = params.get("items")
                                    other_params = {k:v for k,v in params.items() if k != "items"}
                                    
                                    if items_data:
                                        title_suffix = " (Parcial)" if was_truncated else ""
                                        st.markdown(f"##### 📦 PRODUTOS {title_suffix}")
                                        st.markdown(render_items_complete(items_data), unsafe_allow_html=True)
                                        st.markdown("<div style='margin-bottom:15px'></div>", unsafe_allow_html=True)
                                    
                                    if is_missing_screen_name:
                                        st.markdown(f"""
                                        <div class="param-row-error">
                                            <span class="p-key">❌ MISSING PARAM</span>
                                            <span class="p-val">FirebaseAnalytics.Param.SCREEN_NAME</span>
                                        </div>
                                        """, unsafe_allow_html=True)

                                    if other_params:
                                        st.caption("🔧 PARÂMETROS")
                                        for k, v in other_params.items():
                                            val_str = json.dumps(v) if isinstance(v, (list, dict)) else str(v)
                                            
                                            if k in error_keys_map:
                                                st.markdown(f"""
                                                <div class="param-row-error">
                                                    <span class="p-key">⚠️ {k}</span>
                                                    <span class="p-val">{val_str}</span>
                                                </div>
                                                """, unsafe_allow_html=True)
                                            else:
                                                st.markdown(f"""
                                                <div class="param-row">
                                                    <span class="p-key">{k}</span>
                                                    <span class="p-val">{val_str}</span>
                                                </div>
                                                """, unsafe_allow_html=True)
                                    
                                    if has_any_error:
                                        st.markdown("""
                                        <a href="https://firebase.google.com/docs/analytics/errors?hl=pt-br" target="_blank" class="doc-btn">
                                            📖 Ver Documentação de Erros (Google Firebase)
                                        </a>
                                        """, unsafe_allow_html=True)

                        except Exception:
                            pass
                    else: time.sleep(0.1)
    else: st.warning("Aguardando log...")
else:
    st.markdown("<div style='text-align: center; margin-top: 50px; color: #555;'><h1>📡</h1><h3>Aguardando Conexão ADB</h3></div>", unsafe_allow_html=True)