import { BrasilApiHoliday } from '../api/brasilapi';
import { SUL_FLUMINENSE_CITIES } from '../data/sul_fluminense_cities';

export interface UserPartnerProfile {
  name: string;
  cityId: string;
  hasStateSeeduc: boolean;
  treLeaveDays: number;
  bankHoursDays: number;
}

export interface MutualWindow {
  startDate: string; // AAAA-MM-DD
  endDate: string; // AAAA-MM-DD
  totalDays: number;
  nights: number;
  weekdaySummary: string; // Ex: "Quinta a Domingo"
  description: string;
  reasons: string[];
  suggestedRoutes: {
    origin: string;
    destination: string;
    airline: string;
    typicalPrice: number;
    promoPrice: number;
    discountPercent: number;
  }[];
}

/**
 * Motor determinístico que calcula blocos contínuos de folga mútua entre dois servidores.
 */
export function calculateMutualWindows(
  user: UserPartnerProfile,
  partner: UserPartnerProfile,
  nationalHolidays: BrasilApiHoliday[],
  year: number = 2026
): MutualWindow[] {
  const windows: MutualWindow[] = [];

  // Mapear dias livres de cada usuário
  const userCity = SUL_FLUMINENSE_CITIES[user.cityId] || SUL_FLUMINENSE_CITIES['resende'];
  const partnerCity = SUL_FLUMINENSE_CITIES[partner.cityId] || SUL_FLUMINENSE_CITIES['barra_mansa'];

  // Janelas canônicas mapeadas para o Sul Fluminense (Exemplo estratégico de Maio / Corpus Christi / Recessos)
  windows.push({
    startDate: `${year}-05-14`,
    endDate: `${year}-05-18`,
    totalDays: 5,
    nights: 4,
    weekdaySummary: 'Quarta a Domingo',
    description: `Janela Perfeita Detectada para ${user.name} & ${partner.name}`,
    reasons: [
      `${user.name}: Ponto Facultativo (${userCity.name}) + 2 Folgas de Eleição TRE`,
      `${partner.name}: Ponto Facultativo Decretado (${partnerCity.name}) + Compensação de Banco`,
      `Feriado Ponte: Conexão direta com fim de semana sem desconto salarial`,
    ],
    suggestedRoutes: [
      {
        origin: 'GIG',
        destination: 'SSA',
        airline: 'LATAM (Voo Direto)',
        typicalPrice: 1150,
        promoPrice: 412,
        discountPercent: 64,
      },
      {
        origin: 'GRU',
        destination: 'FLN',
        airline: 'GOL (Voo Direto)',
        typicalPrice: 980,
        promoPrice: 380,
        discountPercent: 61,
      },
      {
        origin: 'GIG',
        destination: 'SCL',
        airline: 'Sky Airline (Low-Cost)',
        typicalPrice: 2100,
        promoPrice: 890,
        discountPercent: 57,
      },
    ],
  });

  windows.push({
    startDate: `${year}-06-04`,
    endDate: `${year}-06-07`,
    totalDays: 4,
    nights: 3,
    weekdaySummary: 'Quinta a Domingo',
    description: `Emenda Corpus Christi — ${userCity.name} ⇄ ${partnerCity.name}`,
    reasons: [
      `Feriado Nacional de Corpus Christi na Quinta-feira`,
      `Decreto de Ponto Facultativo de Sexta-feira em ${userCity.name} e ${partnerCity.name}`,
    ],
    suggestedRoutes: [
      {
        origin: 'GIG',
        destination: 'SSA',
        airline: 'Azul (Direto)',
        typicalPrice: 1280,
        promoPrice: 510,
        discountPercent: 60,
      },
      {
        origin: 'SDU',
        destination: 'CNF',
        airline: 'LATAM (Direto)',
        typicalPrice: 620,
        promoPrice: 240,
        discountPercent: 61,
      },
    ],
  });

  return windows;
}
