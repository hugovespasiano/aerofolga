'use client';

import React, { useState } from 'react';
import { Plane, Calendar, MapPin, CheckCircle, ArrowRight, ShieldCheck, Sparkles, ExternalLink } from 'lucide-react';
import { SUL_FLUMINENSE_CITIES } from '@/lib/data/sul_fluminense_cities';
import { calculateMutualWindows, UserPartnerProfile } from '@/lib/engine/intersection';

export function CoupleDashboard() {
  const [userName, setUserName] = useState('Tito Lívio');
  const [userCity, setUserCity] = useState('resende');
  const [userTreDays, setUserTreDays] = useState(2);

  const [partnerName, setPartnerName] = useState('Luciana');
  const [partnerCity, setPartnerCity] = useState('barra_mansa');
  const [partnerBankHours, setPartnerBankHours] = useState(1);

  const userProfile: UserPartnerProfile = {
    name: userName,
    cityId: userCity,
    hasStateSeeduc: false,
    treLeaveDays: userTreDays,
    bankHoursDays: 0,
  };

  const partnerProfile: UserPartnerProfile = {
    name: partnerName,
    cityId: partnerCity,
    hasStateSeeduc: false,
    treLeaveDays: 0,
    bankHoursDays: partnerBankHours,
  };

  const windows = calculateMutualWindows(userProfile, partnerProfile, []);
  const activeWindow = windows[0];

  return (
    <div className="min-h-screen bg-[#090b0e] text-[#f0f3f6] font-sans antialiased p-4 md:p-8">
      {/* Top Header estilo Apple HIG */}
      <header className="max-w-5xl mx-auto flex items-center justify-between border-b border-[#21262d] pb-6 mb-8">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 to-sky-400 flex items-center justify-center shadow-lg shadow-sky-500/20">
            <Plane className="w-5 h-5 text-white transform -rotate-45" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              AeroFolga
              <span className="text-xs px-2 py-0.5 rounded-full bg-sky-950 text-sky-400 border border-sky-800 font-medium">
                Vespasiano Labs S-08
              </span>
            </h1>
            <p className="text-xs text-neutral-400">O radar inteligente que cruza folgas de servidores com voos em promoção</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-950/60 border border-emerald-800/80 text-emerald-400 text-xs font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Radar Ativo (Sul Fluminense)
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto space-y-8">
        {/* Painel do Casal (Configuração Rápida de Cidades) */}
        <section className="bg-[#12151b] border border-[#21262d] rounded-2xl p-6 shadow-xl">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-neutral-400 mb-4 flex items-center gap-2">
            <Calendar className="w-4 h-4 text-sky-400" /> Sincronização do Casal Servidor
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Usuário 1 */}
            <div className="bg-[#181c24] border border-[#262c37] rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-sky-950 text-sky-300 border border-sky-800">
                  Viajante 1 (Você)
                </span>
                <span className="text-xs text-emerald-400 flex items-center gap-1">
                  <CheckCircle className="w-3.5 h-3.5" /> Sincronizado
                </span>
              </div>

              <div>
                <label className="text-xs text-neutral-400 block mb-1">Nome do Servidor</label>
                <input
                  type="text"
                  value={userName}
                  onChange={(e) => setUserName(e.target.value)}
                  className="w-full bg-[#0d1015] border border-[#2b323e] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-sky-500"
                />
              </div>

              <div>
                <label className="text-xs text-neutral-400 block mb-1">Prefeitura / Lotação</label>
                <select
                  value={userCity}
                  onChange={(e) => setUserCity(e.target.value)}
                  className="w-full bg-[#0d1015] border border-[#2b323e] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-sky-500"
                >
                  {Object.values(SUL_FLUMINENSE_CITIES).map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} — {c.institution}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs text-neutral-400 block mb-1">Saldo de Folgas do TRE (Justiça Eleitoral)</label>
                <div className="flex items-center gap-3">
                  <input
                    type="number"
                    min="0"
                    max="10"
                    value={userTreDays}
                    onChange={(e) => setUserTreDays(Number(e.target.value))}
                    className="w-24 bg-[#0d1015] border border-[#2b323e] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-sky-500"
                  />
                  <span className="text-xs text-neutral-500">Dias disponíveis para emendar</span>
                </div>
              </div>
            </div>

            {/* Usuário 2 */}
            <div className="bg-[#181c24] border border-[#262c37] rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-purple-950 text-purple-300 border border-purple-800">
                  Viajante 2 (Parceiro/Esposa)
                </span>
                <span className="text-xs text-emerald-400 flex items-center gap-1">
                  <CheckCircle className="w-3.5 h-3.5" /> Sincronizado
                </span>
              </div>

              <div>
                <label className="text-xs text-neutral-400 block mb-1">Nome do Parceiro(a)</label>
                <input
                  type="text"
                  value={partnerName}
                  onChange={(e) => setPartnerName(e.target.value)}
                  className="w-full bg-[#0d1015] border border-[#2b323e] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-purple-500"
                />
              </div>

              <div>
                <label className="text-xs text-neutral-400 block mb-1">Prefeitura / Lotação</label>
                <select
                  value={partnerCity}
                  onChange={(e) => setPartnerCity(e.target.value)}
                  className="w-full bg-[#0d1015] border border-[#2b323e] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-purple-500"
                >
                  {Object.values(SUL_FLUMINENSE_CITIES).map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} — {c.institution}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs text-neutral-400 block mb-1">Banco de Horas / Folgas Compensatórias</label>
                <div className="flex items-center gap-3">
                  <input
                    type="number"
                    min="0"
                    max="10"
                    value={partnerBankHours}
                    onChange={(e) => setPartnerBankHours(Number(e.target.value))}
                    className="w-24 bg-[#0d1015] border border-[#2b323e] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-purple-500"
                  />
                  <span className="text-xs text-neutral-500">Dias compensatórios</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Destaque da Janela Perfeita Detectada */}
        {activeWindow && (
          <section className="bg-gradient-to-b from-[#151c27] to-[#10141d] border border-sky-900/60 rounded-2xl p-6 shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 transform translate-x-8 -translate-y-8 w-64 h-64 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />

            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6 pb-6 border-b border-[#212b3b]">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-500 text-black">
                    Oportunidade de Ouro
                  </span>
                  <span className="text-xs text-sky-400 font-medium">Interseção Mútua de Folgas</span>
                </div>
                <h3 className="text-2xl font-bold text-white tracking-tight">
                  {activeWindow.weekdaySummary} (14 a 18 de Maio • {activeWindow.nights} Noites)
                </h3>
                <p className="text-sm text-neutral-300 mt-1">
                  Cruzamento: {SUL_FLUMINENSE_CITIES[userCity]?.name} ⇄ {SUL_FLUMINENSE_CITIES[partnerCity]?.name}
                </p>
              </div>

              <div className="flex flex-wrap gap-2">
                {activeWindow.reasons.map((r, i) => (
                  <span key={i} className="text-xs px-3 py-1 rounded-md bg-[#182130] text-sky-200 border border-sky-800/60">
                    {r}
                  </span>
                ))}
              </div>
            </div>

            {/* Rotas em Destaque */}
            <div className="space-y-4">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-neutral-400">
                Voos com Tarifa Promocional Detectada (Filtro dos 8 Pilares do Tilli)
              </h4>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {activeWindow.suggestedRoutes.map((route, idx) => (
                  <div
                    key={idx}
                    className="bg-[#161c26] border border-[#283244] hover:border-sky-500/60 transition-all rounded-xl p-5 flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-sm font-bold text-white flex items-center gap-1.5">
                          {route.origin} <ArrowRight className="w-3.5 h-3.5 text-neutral-400" /> {route.destination}
                        </span>
                        <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 text-xs font-bold">
                          -{route.discountPercent}%
                        </span>
                      </div>
                      <p className="text-xs text-neutral-400 mb-4">{route.airline}</p>
                    </div>

                    <div className="border-t border-[#232b3b] pt-3 mt-2 flex items-center justify-between">
                      <div>
                        <span className="text-xs text-neutral-500 line-through block">
                          R$ {route.typicalPrice}
                        </span>
                        <span className="text-lg font-black text-white">
                          R$ {route.promoPrice}
                        </span>
                        <span className="text-[10px] text-neutral-400 block">ida e volta</span>
                      </div>

                      <a
                        href={`https://www.google.com/travel/flights?q=Flights%20to%20${route.destination}%20from%20${route.origin}%20on%202026-05-14%20through%202026-05-18`}
                        target="_blank"
                        rel="noreferrer"
                        className="px-3 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-lg shadow-sky-600/20"
                      >
                        Ver Voo <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Cláusula ANAC Res 400 */}
            <div className="mt-6 pt-4 border-t border-[#212b3b] flex items-center gap-2 text-xs text-neutral-400">
              <ShieldCheck className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span>
                <strong>Blindagem Jurídica Ativa:</strong> Proteção de no-show conforme Resolução 400 da ANAC e voos diretos sem troca física de aeroporto.
              </span>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
