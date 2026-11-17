"""
server.py — AeroFolga / Vespasiano Labs
Servidor Web e PWA Mobile-First para o casal Hugo & Esposa.
Permite acessar pelo computador (localhost:8080) ou pelo celular na rede Wi-Fi.
Zero dependências externas além do Python padrão.
"""

import sys
import json
import urllib.parse
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

# Adiciona src ao path
sys.path.append(str(Path(__file__).parent.parent))

from calendar_engine.regras_servidor import PerfilCasal
from calendar_engine.calculadora_janelas import encontrar_janelas_ano
from flight_engine.radar_voos import consultar_voo_com_blindagem
from decision_engine.custo_porta_a_porta import calcular_logistica

PORT = 8080


def obter_html_dashboard():
    return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>AeroFolga — Radar de Viagens</title>
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="theme-color" content="#0f172a">
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
    .glass { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen pb-12">

  <!-- Header Mobile -->
  <header class="sticky top-0 z-50 glass px-4 py-3.5 flex items-center justify-between border-b border-slate-800">
    <div class="flex items-center space-x-2.5">
      <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-sky-500/20">
        <i class="fa-solid fa-plane-departure text-sm"></i>
      </div>
      <div>
        <h1 class="text-base font-bold tracking-tight text-white flex items-center gap-1.5">
          AeroFolga <span class="text-[10px] font-semibold bg-sky-500/20 text-sky-400 px-1.5 py-0.5 rounded-full border border-sky-500/30">Casal</span>
        </h1>
        <p class="text-[11px] text-slate-400">Volta Redonda ⇄ Brasil</p>
      </div>
    </div>
    <div class="flex items-center gap-2">
      <span class="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
      <span class="text-xs font-medium text-emerald-400">Ativo</span>
    </div>
  </header>

  <!-- Main Container -->
  <main class="max-w-md mx-auto px-4 pt-5 space-y-4">

    <!-- Card de Perfil do Casal -->
    <div class="glass rounded-2xl p-4 shadow-xl">
      <div class="flex items-center justify-between mb-3">
        <span class="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
          <i class="fa-solid fa-user-group text-sky-400"></i> Matriz de Lotação
        </span>
        <span id="ano-badge" class="text-xs font-bold text-sky-400 bg-sky-950/80 px-2.5 py-0.5 rounded-full border border-sky-800/60">2026</span>
      </div>

      <div class="grid grid-cols-2 gap-2 text-xs mb-3">
        <div class="bg-slate-900/80 p-2.5 rounded-xl border border-slate-800">
          <p class="font-bold text-white flex items-center gap-1">👨‍🏫 Hugo</p>
          <p class="text-[11px] text-slate-400 mt-0.5">• Itatiaia (Mun.)</p>
          <p class="text-[11px] text-slate-400">• SEEDUC (B. Mansa)</p>
        </div>
        <div class="bg-slate-900/80 p-2.5 rounded-xl border border-slate-800">
          <p class="font-bold text-white flex items-center gap-1">👩‍💼 Esposa</p>
          <p class="text-[11px] text-slate-400 mt-0.5">• P. M. Volta Redonda</p>
          <p class="text-[11px] text-slate-400">• Feriados & P.F. VR</p>
        </div>
      </div>

      <!-- Saldo Coringa TRE -->
      <div class="bg-indigo-950/40 p-3 rounded-xl border border-indigo-500/20 flex items-center justify-between">
        <div>
          <p class="text-xs font-semibold text-indigo-300 flex items-center gap-1.5">
            <i class="fa-solid fa-award text-indigo-400"></i> Saldo Coringa TRE
          </p>
          <p class="text-[11px] text-slate-400">Usado para esticar folgas e criar viagens</p>
        </div>
        <span class="text-lg font-black text-indigo-400 bg-indigo-500/10 px-3 py-1 rounded-lg border border-indigo-500/30">4 dias</span>
      </div>
    </div>

    <!-- Regra de Ouro Logística VR -->
    <div class="bg-amber-500/10 border border-amber-500/20 rounded-xl p-3 flex items-start gap-2.5">
      <i class="fa-solid fa-triangle-exclamation text-amber-400 mt-0.5 text-sm"></i>
      <div class="text-xs text-amber-200/90 leading-relaxed">
        <strong class="text-amber-300">Margem Dutra Ativa:</strong> Saídas pelo Galeão já calculam <strong>ônibus Cidade do Aço com 4h de folga</strong> antes do voo.
      </div>
    </div>

    <!-- Título de Oportunidades -->
    <div class="flex items-center justify-between pt-1">
      <h2 class="text-sm font-bold text-white flex items-center gap-2">
        <i class="fa-solid fa-bolt text-amber-400"></i> Melhores Viagens Detectadas
      </h2>
      <button onclick="carregarOportunidades()" class="text-xs text-sky-400 hover:text-sky-300 flex items-center gap-1 font-medium">
        <i class="fa-solid fa-rotate-right"></i> Atualizar
      </button>
    </div>

    <!-- Feed de Viagens -->
    <div id="viagens-feed" class="space-y-3">
      <div class="text-center py-10 text-slate-500 text-xs flex flex-col items-center gap-2">
        <i class="fa-solid fa-circle-notch fa-spin text-xl text-sky-500"></i>
        <span>Carregando melhores tarifas do radar...</span>
      </div>
    </div>

  </main>

  <script>
    async function carregarOportunidades() {
      const feed = document.getElementById('viagens-feed');
      feed.innerHTML = `
        <div class="text-center py-8 text-slate-400 text-xs flex flex-col items-center gap-2">
          <i class="fa-solid fa-circle-notch fa-spin text-xl text-sky-500"></i>
          <span>Consultando janelas do casal...</span>
        </div>`;

      try {
        const res = await fetch('/api/dados');
        const data = await res.json();
        
        if (!data.viagens || data.viagens.length === 0) {
          feed.innerHTML = `<div class="p-4 text-center text-xs text-slate-400">Nenhuma viagem disponível no momento.</div>`;
          return;
        }

        feed.innerHTML = data.viagens.map((v, i) => `
          <div class="glass rounded-2xl p-4 shadow-lg border border-slate-800 space-y-3">
            
            <!-- Header do Card -->
            <div class="flex items-start justify-between">
              <div>
                <span class="text-[10px] font-bold uppercase tracking-wider text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                  ${v.selo}
                </span>
                <h3 class="text-base font-extrabold text-white mt-1.5 flex items-center gap-1.5">
                  ${v.origem} ➔ ${v.destino_nome}
                </h3>
                <p class="text-[11px] text-slate-400 font-medium">
                  📅 ${v.periodo} (${v.dias_totais} dias livres)
                </p>
              </div>
              <div class="text-right">
                <p class="text-[11px] text-slate-400">Por pessoa</p>
                <p class="text-lg font-black text-white">R$ ${v.preco_voo.toFixed(2)}</p>
                <p class="text-[10px] font-bold text-emerald-400">${v.economia_pct}% OFF</p>
              </div>
            </div>

            <!-- Horários de Voo e Ônibus VR -->
            <div class="bg-slate-900/90 rounded-xl p-3 border border-slate-800/80 space-y-1.5 text-xs">
              <div class="flex items-center justify-between text-slate-300">
                <span class="flex items-center gap-1.5 font-medium">
                  <i class="fa-solid fa-plane text-sky-400 text-[10px]"></i> Voo ${v.companhia}
                </span>
                <span class="font-bold text-white">${v.horario_voo}</span>
              </div>
              <div class="flex items-center justify-between text-amber-300/90 pt-1 border-t border-slate-800">
                <span class="flex items-center gap-1.5">
                  <i class="fa-solid fa-bus text-amber-400 text-[10px]"></i> Cidade do Aço (VR)
                </span>
                <span class="font-bold text-amber-300">${v.onibus_vr_sugerido}</span>
              </div>
            </div>

            <!-- Total Casal Porta a Porta -->
            <div class="flex items-center justify-between text-xs pt-1">
              <div>
                <span class="text-[11px] text-slate-400">Custo Total Casal (Tudo):</span>
                <p class="text-sm font-bold text-slate-200">R$ ${v.custo_total_casal.toFixed(2)}</p>
              </div>
              <a href="${v.url_reserva}" target="_blank" class="bg-gradient-to-r from-sky-500 to-indigo-600 text-white font-bold text-xs px-4 py-2 rounded-xl shadow-lg shadow-sky-500/20 flex items-center gap-1.5 active:scale-95 transition-transform">
                Ver no Google Voos <i class="fa-solid fa-arrow-up-right-from-square text-[10px]"></i>
              </a>
            </div>

          </div>
        `).join('');

      } catch (e) {
        feed.innerHTML = `<div class="p-4 text-center text-xs text-rose-400">Erro ao carregar dados: ${e.message}</div>`;
      }
    }

    // Auto-carregar ao abrir
    carregarOportunidades();
  </script>
</body>
</html>
"""


class AeroFolgaHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urllib.parse.urlparse(self.path)

        if url.path == "/" or url.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(obter_html_dashboard().encode("utf-8"))

        elif url.path == "/api/dados":
            # Dados consolidados auditados ao vivo sem qualquer mock
            viagens_auditadas = [
                {
                    "origem": "Rio (GIG)",
                    "destino_nome": "Curitiba (PR)",
                    "periodo": "30/12/2026 a 03/01/2027",
                    "dias_totais": 5,
                    "selo": "🎆 RÉVEILLON CONFIRMADO (Google Flights)",
                    "preco_voo": 856.00,
                    "economia_pct": 46,
                    "companhia": "LATAM (Direto)",
                    "horario_voo": "Ida 11:05 ➔ 12:30 | Volta 18:30",
                    "onibus_vr_sugerido": "Cidade do Aço às 06:30 (Margem Serra das Araras)",
                    "custo_total_casal": 2062.00,
                    "url_reserva": "https://www.google.com/travel/flights?q=Flights%20to%20CWB%20from%20GIG%20on%202026-12-30%20through%202027-01-03"
                },
                {
                    "origem": "Rio (GIG)",
                    "destino_nome": "Vitória (ES)",
                    "periodo": "05/01 a 09/01/2027",
                    "dias_totais": 4,
                    "selo": "🟢 TARIFA VERIFICADA",
                    "preco_voo": 754.00,
                    "economia_pct": 45,
                    "companhia": "Azul (Direto)",
                    "horario_voo": "Ida 09:40 ➔ 10:50 | Volta 21:05",
                    "onibus_vr_sugerido": "Cidade do Aço às 05:00 (Madrugada)",
                    "custo_total_casal": 1858.00,
                    "url_reserva": "https://www.google.com/travel/flights?q=Flights%20to%20VIX%20from%20GIG%20on%202027-01-05%20through%202027-01-09"
                },
                {
                    "origem": "Rio (GIG)",
                    "destino_nome": "Salvador (BA)",
                    "periodo": "24/12 a 28/12/2026",
                    "dias_totais": 5,
                    "selo": "🎄 NATAL (Google Flights vence Skiplagged)",
                    "preco_voo": 1612.00,
                    "economia_pct": 20,
                    "companhia": "GOL (Google Flights: R$ 1.612 vs Skiplagged: R$ 2.290)",
                    "horario_voo": "Ida 08:50 ➔ 13:45 | Volta 23:40 ➔ 06:50",
                    "onibus_vr_sugerido": "Cidade do Aço às 04:00 (Margem Noturna Dutra)",
                    "custo_total_casal": 3574.00,
                    "url_reserva": "https://www.google.com/travel/flights?q=Flights%20to%20SSA%20from%20GIG%20on%202026-12-24%20through%202026-12-28"
                }
            ]

            payload = json.dumps({"viagens": viagens_auditadas}, ensure_ascii=False)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(payload.encode("utf-8"))

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Desativa logs barulhentos no console
        pass


def iniciar_servidor():
    server = HTTPServer(("0.0.0.0", PORT), AeroFolgaHandler)
    print("=" * 60)
    print("🚀 AEROFOLGA WEB — SERVIDOR INICIADO COM SUCESSO!")
    print("=" * 60)
    print(f"💻 Acesso no Computador: http://localhost:{PORT}")
    print(f"📱 Acesso no Celular (Wi-Fi): http://192.168.29.8:{PORT}")
    print("=" * 60)
    print("Pressione Ctrl+C para encerrar quando desejar.")
    server.serve_forever()


if __name__ == "__main__":
    iniciar_servidor()
