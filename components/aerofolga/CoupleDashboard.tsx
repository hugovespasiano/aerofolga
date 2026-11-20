'use client';

import React, { useState, useEffect } from 'react';
import {
  Plane,
  Calendar,
  MapPin,
  Clock,
  Bus,
  Sparkles,
  ExternalLink,
  ShieldCheck,
  TrendingDown,
  Filter,
  ArrowRight,
  CheckCircle2,
  DollarSign,
  Smartphone,
  ChevronRight,
  Send,
  Info
} from 'lucide-react';

interface Deal {
  id: string;
  origem: string;
  origem_nome: string;
  destino: string;
  destino_nome: string;
  data_ida: string;
  data_volta: string;
  label_periodo: string;
  tipo_folga: string;
  folgas_gastas: number;
  dias_folga: string[];
  descricao_folga: string;
  tarifa_pessoa: number;
  passagens_casal: number;
  logistica_vr: number;
  custo_casal_total: number;
  cia: string;
  horario_ida: string;
  horario_volta: string;
  onibus_embarque: string;
  desconto_pct: number;
  economia_casal: number;
  preco_tipico: number;
  piso_historico: number;
  teto_historico: number;
  url: string;
}

interface WindowData {
  inicio: string;
  fim: string;
  nome_evento: string;
  categoria: string;
  folgas_gastas: number;
  dias_folga: string[];
  dias_totais: number;
  detalhes: string;
  is_alta_temporada: boolean;
  label: string;
}

interface AppFeed {
  versao: string;
  ano: number;
  total_janelas: number;
  total_ofertas: number;
  janelas: WindowData[];
  ofertas: Deal[];
  cidades_atendidas: { id: string; nome: string; onibus_principal: string }[];
}

export function CoupleDashboard() {
  const [feed, setFeed] = useState<AppFeed | null>(null);
  const [loading, setLoading] = useState(true);

  // Controles do Casal (Simplicidade: Folga é folga)
  const [userCity, setUserCity] = useState('volta_redonda');
  const [userFolgas, setUserFolgas] = useState<number>(2);
  const [userFolgaNota, setUserFolgaNota] = useState('Folga do TRE (Eleições)');

  const [partnerCity, setPartnerCity] = useState('volta_redonda');
  const [partnerFolgas, setPartnerFolgas] = useState<number>(0);
  const [partnerFolgaNota, setPartnerFolgaNota] = useState('PMVR (Sem gastar abono)');

  // Abas de navegação
  const [activeTab, setActiveTab] = useState<'oportunidades' | 'calendario' | 'logistica'>('oportunidades');

  // Filtros
  const [filtroTipo, setFiltroTipo] = useState<'todos' | 'puro' | 'alavancado'>('todos');
  const [filtroDestino, setFiltroDestino] = useState<string>('todos');

  useEffect(() => {
    fetch('/data/app_feed.json')
      .then((res) => res.json())
      .then((data: AppFeed) => {
        setFeed(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Erro ao carregar app_feed:', err);
        setLoading(false);
      });
  }, []);

  // Filtragem dinâmica das ofertas
  const maxFolgasPermitidas = Math.max(userFolgas, partnerFolgas);

  const ofertasFiltradas = feed?.ofertas.filter((o) => {
    // Filtro por folgas disponíveis pelo casal
    if (o.folgas_gastas > maxFolgasPermitidas) return false;

    // Filtro por tipo
    if (filtroTipo === 'puro' && o.folgas_gastas > 0) return false;
    if (filtroTipo === 'alavancado' && o.folgas_gastas === 0) return false;

    // Filtro por destino
    if (filtroDestino !== 'todos' && o.destino !== filtroDestino) return false;

    return true;
  }) || [];

  const janelasFiltradas = feed?.janelas.filter((j) => {
    if (j.folgas_gastas > maxFolgasPermitidas) return false;
    if (filtroTipo === 'puro' && j.folgas_gastas > 0) return false;
    if (filtroTipo === 'alavancado' && j.folgas_gastas === 0) return false;
    return true;
  }) || [];

  return (
    <div className="min-h-screen bg-[#090b0e] text-[#f0f3f6] font-sans antialiased pb-16">
      {/* Top Header estilo Apple HIG */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-[#090b0e]/85 border-b border-[#21262d] px-4 md:px-8 py-4 transition-all">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 via-sky-500 to-emerald-400 flex items-center justify-center shadow-lg shadow-sky-500/20">
              <Plane className="w-5 h-5 text-white transform -rotate-45" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold tracking-tight text-white">AeroFolga</h1>
                <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800">
                  PWA Web
                </span>
              </div>
              <p className="text-xs text-neutral-400">O planejador de folgas e viagens porta a porta do casal</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <a
              href="https://t.me/aero_folga_bot"
              target="_blank"
              rel="noreferrer"
              className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#161b22] hover:bg-[#21262d] border border-[#30363d] text-xs text-sky-400 font-medium transition-colors"
            >
              <Send className="w-3.5 h-3.5" />
              Bot Telegram Ativo
            </a>

            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-sky-950/60 border border-sky-800 text-sky-300 text-xs font-medium">
              <span className="w-2 h-2 rounded-full bg-sky-400 animate-pulse" />
              2027 Sincronizado
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 md:px-8 pt-6 space-y-6">
        {/* Painel do Casal: Super Simples e Sem Burocracia */}
        <section className="bg-gradient-to-b from-[#12151b] to-[#0d1015] border border-[#21262d] rounded-2xl p-5 md:p-6 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xs font-bold uppercase tracking-wider text-neutral-400 flex items-center gap-2">
              <Calendar className="w-4 h-4 text-sky-400" />
              Sincronização de Folgas do Casal
            </h2>
            <span className="text-xs text-neutral-500">Folga é folga: sem complicação de RH</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Viajante 1 (Hugo) */}
            <div className="bg-[#161a22] border border-[#282f3c] rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-sky-950 text-sky-300 border border-sky-800">
                  Viajante 1 (Você)
                </span>
                <span className="text-xs text-neutral-400">SEEDUC / Itatiaia</span>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] text-neutral-400 block mb-1">Cidade de Partida</label>
                  <select
                    value={userCity}
                    onChange={(e) => setUserCity(e.target.value)}
                    className="w-full bg-[#0d1015] border border-[#30363d] rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-sky-500"
                  >
                    <option value="volta_redonda">Volta Redonda (RJ)</option>
                    <option value="barra_mansa">Barra Mansa (RJ)</option>
                    <option value="resende">Resende (RJ)</option>
                    <option value="itatiaia">Itatiaia (RJ)</option>
                  </select>
                </div>

                <div>
                  <label className="text-[11px] text-neutral-400 block mb-1">Quantas folgas gastar?</label>
                  <div className="flex items-center gap-1.5">
                    {[0, 1, 2].map((num) => (
                      <button
                        key={num}
                        onClick={() => setUserFolgas(num)}
                        className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition-all ${
                          userFolgas === num
                            ? 'bg-sky-500 text-black shadow-md shadow-sky-500/30'
                            : 'bg-[#0d1015] text-neutral-400 hover:text-white border border-[#30363d]'
                        }`}
                      >
                        {num === 0 ? 'Zero' : `${num}d`}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <div>
                <input
                  type="text"
                  placeholder="Origem da folga (opcional: TRE, banco...)"
                  value={userFolgaNota}
                  onChange={(e) => setUserFolgaNota(e.target.value)}
                  className="w-full bg-[#0d1015] border border-[#21262d] rounded-lg px-2.5 py-1 text-[11px] text-neutral-400 focus:outline-none"
                />
              </div>
            </div>

            {/* Viajante 2 (Esposa) */}
            <div className="bg-[#161a22] border border-[#282f3c] rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800">
                  Viajante 2 (Esposa)
                </span>
                <span className="text-xs text-neutral-400">Prefeitura de Volta Redonda</span>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] text-neutral-400 block mb-1">Cidade de Lotação</label>
                  <select
                    value={partnerCity}
                    onChange={(e) => setPartnerCity(e.target.value)}
                    className="w-full bg-[#0d1015] border border-[#30363d] rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-purple-500"
                  >
                    <option value="volta_redonda">Volta Redonda (PMVR)</option>
                    <option value="barra_mansa">Barra Mansa (PMBM)</option>
                    <option value="resende">Resende (PMR)</option>
                  </select>
                </div>

                <div>
                  <label className="text-[11px] text-neutral-400 block mb-1">Quantas folgas gastar?</label>
                  <div className="flex items-center gap-1.5">
                    {[0, 1, 2].map((num) => (
                      <button
                        key={num}
                        onClick={() => setPartnerFolgas(num)}
                        className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition-all ${
                          partnerFolgas === num
                            ? 'bg-purple-500 text-white shadow-md shadow-purple-500/30'
                            : 'bg-[#0d1015] text-neutral-400 hover:text-white border border-[#30363d]'
                        }`}
                      >
                        {num === 0 ? 'Zero' : `${num}d`}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <div>
                <input
                  type="text"
                  placeholder="Origem da folga (opcional: Abono, banco...)"
                  value={partnerFolgaNota}
                  onChange={(e) => setPartnerFolgaNota(e.target.value)}
                  className="w-full bg-[#0d1015] border border-[#21262d] rounded-lg px-2.5 py-1 text-[11px] text-neutral-400 focus:outline-none"
                />
              </div>
            </div>
          </div>
        </section>

        {/* Abas e Filtros de Navegação */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#21262d] pb-4">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab('oportunidades')}
              className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all ${
                activeTab === 'oportunidades'
                  ? 'bg-sky-500 text-black shadow-lg shadow-sky-500/20'
                  : 'bg-[#12151b] text-neutral-400 hover:text-white border border-[#21262d]'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              Oportunidades Vencedoras ({ofertasFiltradas.length})
            </button>

            <button
              onClick={() => setActiveTab('calendario')}
              className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all ${
                activeTab === 'calendario'
                  ? 'bg-sky-500 text-black shadow-lg shadow-sky-500/20'
                  : 'bg-[#12151b] text-neutral-400 hover:text-white border border-[#21262d]'
              }`}
            >
              <Calendar className="w-3.5 h-3.5" />
              Calendário 2027 ({janelasFiltradas.length})
            </button>

            <button
              onClick={() => setActiveTab('logistica')}
              className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all ${
                activeTab === 'logistica'
                  ? 'bg-sky-500 text-black shadow-lg shadow-sky-500/20'
                  : 'bg-[#12151b] text-neutral-400 hover:text-white border border-[#21262d]'
              }`}
            >
              <Bus className="w-3.5 h-3.5" />
              Logística Porta a Porta
            </button>
          </div>

          {/* Filtro Rápido */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-neutral-500">Filtrar:</span>
            <button
              onClick={() => setFiltroTipo('todos')}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
                filtroTipo === 'todos' ? 'bg-[#282f3c] text-white' : 'text-neutral-400 hover:text-white'
              }`}
            >
              Todos
            </button>
            <button
              onClick={() => setFiltroTipo('puro')}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
                filtroTipo === 'puro' ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'text-neutral-400 hover:text-emerald-400'
              }`}
            >
              🟢 100% Puro (0 folgas)
            </button>
            <button
              onClick={() => setFiltroTipo('alavancado')}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
                filtroTipo === 'alavancado' ? 'bg-amber-950 text-amber-300 border border-amber-800' : 'text-neutral-400 hover:text-amber-400'
              }`}
            >
              🟡 Com Folga
            </button>
          </div>
        </div>

        {/* ======================================================== */}
        {/* ABA 1: OPORTUNIDADES VENCEDORAS                          */}
        {/* ======================================================== */}
        {activeTab === 'oportunidades' && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {ofertasFiltradas.map((deal) => (
                <div
                  key={deal.id}
                  className="bg-gradient-to-b from-[#13171f] to-[#0e1117] border border-[#232a37] hover:border-sky-500/50 transition-all rounded-2xl p-5 shadow-xl flex flex-col justify-between relative group"
                >
                  {/* Topo do Card: Preço Total Casal & Desconto */}
                  <div>
                    <div className="flex items-start justify-between gap-3 mb-3">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          {deal.folgas_gastas === 0 ? (
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 flex items-center gap-1">
                              🟢 100% PURO (Zero Folgas)
                            </span>
                          ) : (
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-800 flex items-center gap-1">
                              🟡 USA {deal.folgas_gastas} FOLGA(S)
                            </span>
                          )}
                          <span className="text-[11px] text-neutral-400">{deal.cia}</span>
                        </div>

                        <div className="text-2xl font-black text-white tracking-tight flex items-baseline gap-2">
                          R$ {deal.custo_casal_total.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                          <span className="text-xs font-normal text-neutral-400">TOTAL CASAL (Porta a Porta)</span>
                        </div>
                      </div>

                      <div className="text-right">
                        <span className="inline-block px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-black">
                          -{deal.desconto_pct}%
                        </span>
                        <span className="block text-[10px] text-emerald-400 mt-0.5 font-medium">
                          Poupa R$ {deal.economia_casal.toFixed(0)}
                        </span>
                      </div>
                    </div>

                    {/* Discriminação de Custos */}
                    <div className="bg-[#0b0e14] border border-[#1c222c] rounded-lg p-2.5 mb-4 grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-[10px] text-neutral-500 block">Passagens do Casal (Ida/Volta)</span>
                        <span className="font-semibold text-neutral-200">
                          R$ {deal.passagens_casal.toFixed(2)} ({deal.tarifa_pessoa.toFixed(0)}/pessoa)
                        </span>
                      </div>
                      <div>
                        <span className="text-[10px] text-neutral-500 block">Logística Volta Redonda</span>
                        <span className="font-semibold text-neutral-200">
                          R$ {deal.logistica_vr.toFixed(2)} (Ônibus + Uber)
                        </span>
                      </div>
                    </div>

                    {/* Detalhes da Rota */}
                    <div className="space-y-2 mb-4 text-xs">
                      <div className="flex items-center justify-between text-neutral-300">
                        <span className="font-bold text-white flex items-center gap-1.5">
                          {deal.origem_nome} ➔ {deal.destino_nome}
                        </span>
                        <span className="text-neutral-400">{deal.label_periodo}</span>
                      </div>

                      <div className="flex items-center justify-between text-neutral-400 text-[11px]">
                        <span>Ida: {deal.horario_ida}</span>
                        <span>Volta: {deal.horario_volta}</span>
                      </div>

                      {/* Ônibus VR com Margem */}
                      <div className="bg-[#121620] border border-[#1e2533] rounded-lg p-2 flex items-start gap-2 text-[11px] text-neutral-300">
                        <Bus className="w-4 h-4 text-sky-400 flex-shrink-0 mt-0.5" />
                        <span>{deal.onibus_embarque}</span>
                      </div>
                    </div>
                  </div>

                  {/* Rodapé com Link Direto do Google Voos */}
                  <div className="border-t border-[#1e2533] pt-3 flex items-center justify-between">
                    <div className="text-[10px] text-neutral-500">
                      Médio típico: R$ {deal.preco_tipico} | Piso feriado: R$ {deal.piso_historico}
                    </div>

                    <a
                      href={deal.url}
                      target="_blank"
                      rel="noreferrer"
                      className="px-4 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-all shadow-md shadow-sky-600/20"
                    >
                      Ver no Google Voos <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ======================================================== */}
        {/* ABA 2: CALENDÁRIO COMPLETO 2027 (74 JANELAS)             */}
        {/* ======================================================== */}
        {activeTab === 'calendario' && (
          <div className="bg-[#12151b] border border-[#21262d] rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between pb-4 border-b border-[#21262d]">
              <div>
                <h3 className="text-base font-bold text-white">Calendário Inteligente do Casal 2027</h3>
                <p className="text-xs text-neutral-400">
                  Cruzando Feriados Nacionais, Estaduais RJ, Barra Mansa, Itatiaia, Volta Redonda e Pontes
                </p>
              </div>
              <span className="text-xs font-semibold px-3 py-1 rounded-full bg-[#18202d] text-sky-400 border border-sky-800">
                {janelasFiltradas.length} Janelas Mapeadas
              </span>
            </div>

            <div className="divide-y divide-[#1e2533]">
              {janelasFiltradas.map((janela, idx) => (
                <div key={idx} className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-[#161a22] px-3 rounded-xl transition-colors">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      {janela.folgas_gastas === 0 ? (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                          100% PURO
                        </span>
                      ) : (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-800">
                          USA {janela.folgas_gastas} FOLGA(S)
                        </span>
                      )}
                      <h4 className="text-sm font-bold text-white">{janela.nome_evento}</h4>
                    </div>
                    <p className="text-xs text-neutral-400">{janela.detalhes}</p>
                  </div>

                  <div className="flex items-center gap-4 text-xs font-medium text-neutral-300">
                    <span className="px-2.5 py-1 rounded-md bg-[#0d1015] border border-[#282f3c] text-sky-300">
                      {janela.dias_totais} dias contíguos
                    </span>
                    <span className="text-neutral-400 whitespace-nowrap">
                      {janela.inicio.slice(5)} a {janela.fim.slice(5)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ======================================================== */}
        {/* ABA 3: COMPARADOR DE LOGÍSTICA PORTA A PORTA             */}
        {/* ======================================================== */}
        {activeTab === 'logistica' && (
          <div className="bg-[#12151b] border border-[#21262d] rounded-2xl p-6 shadow-xl space-y-6">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Bus className="w-5 h-5 text-sky-400" />
                Matemática de Chão: Rio de Janeiro vs São Paulo
              </h3>
              <p className="text-xs text-neutral-400 mt-1">
                Por que o AeroFolga não olha apenas o preço da passagem: o ônibus de Volta Redonda decide quem ganha.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Galeão */}
              <div className="bg-[#161a22] border border-emerald-900/60 rounded-xl p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-emerald-400">Rio de Janeiro (GIG)</span>
                  <span className="text-xs font-black text-white">R$ 350 Casal</span>
                </div>
                <p className="text-xs text-neutral-400">
                  Cidade do Aço (VR ➔ GIG ida e volta casal: R$ 260) + Uber Rodoviária/Galeão (R$ 90).
                </p>
                <div className="text-[11px] text-emerald-300 bg-emerald-950/40 p-2 rounded-lg border border-emerald-800/40">
                  🏆 <strong>Vencedor Absoluto:</strong> Vitória, Florianópolis, Belo Horizonte e Salvador.
                </div>
              </div>

              {/* Congonhas */}
              <div className="bg-[#161a22] border border-sky-900/60 rounded-xl p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-sky-400">São Paulo (CGH)</span>
                  <span className="text-xs font-black text-white">R$ 730 Casal</span>
                </div>
                <p className="text-xs text-neutral-400">
                  Viação Cometa (VR ➔ Tietê casal: R$ 560) + Uber Tietê ➔ Congonhas (~35 min: R$ 170).
                </p>
                <div className="text-[11px] text-sky-300 bg-sky-950/40 p-2 rounded-lg border border-sky-800/40">
                  🔥 <strong>Vencedor Estratégico:</strong> Navegantes (Beto Carrero) e Curitiba em fins de semana atípicos.
                </div>
              </div>

              {/* Guarulhos */}
              <div className="bg-[#161a22] border border-neutral-700 rounded-xl p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-neutral-300">São Paulo (GRU)</span>
                  <span className="text-xs font-black text-white">R$ 760 Casal</span>
                </div>
                <p className="text-xs text-neutral-400">
                  Viação Cometa (VR ➔ Tietê casal: R$ 560) + Transfer Tietê ➔ Guarulhos (R$ 200).
                </p>
                <div className="text-[11px] text-neutral-300 bg-neutral-900 p-2 rounded-lg border border-neutral-800">
                  ⚡ <strong>Vencedor em Foz do Iguaçu:</strong> Economiza mais de R$ 1.600 em relação ao Rio.
                </div>
              </div>
            </div>

            {/* Margem de Segurança 3h a 3h30 */}
            <div className="bg-sky-950/30 border border-sky-800/60 rounded-xl p-4 flex items-start gap-3">
              <ShieldCheck className="w-5 h-5 text-sky-400 flex-shrink-0 mt-0.5" />
              <div className="text-xs text-neutral-300 space-y-1">
                <p className="font-semibold text-white">
                  Regra Rígida de Folga Líquida no Saguão (3h a 3h30):
                </p>
                <p>
                  O AeroFolga calcula os horários de embarque na Rodoviária Francisco Torres garantindo que você chegue ao Galeão com no mínimo 3h de folga líquida antes da decolagem, blindando sua viagem contra retenções na Serra das Araras e filas no raio-X.
                </p>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
