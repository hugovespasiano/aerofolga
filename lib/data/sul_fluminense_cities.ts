/**
 * Tabela Canônica de Municípios e Feriados Municipais do Sul Fluminense (RJ).
 * Base de dados local para operação instantânea do AeroFolga.
 */

export interface MunicipalHoliday {
  day: number;
  month: number; // 1 a 12
  name: string;
  type: 'emancipacao' | 'padroeiro' | 'tradicional';
}

export interface CityProfile {
  id: string;
  name: string;
  state: 'RJ';
  institution: string;
  holidays: MunicipalHoliday[];
}

export const SUL_FLUMINENSE_CITIES: Record<string, CityProfile> = {
  resende: {
    id: 'resende',
    name: 'Resende',
    state: 'RJ',
    institution: 'Prefeitura Municipal de Resende',
    holidays: [
      { day: 29, month: 9, name: 'Aniversário de Resende', type: 'emancipacao' },
      { day: 24, month: 6, name: 'Dia de São João Batista', type: 'padroeiro' },
    ],
  },
  barra_mansa: {
    id: 'barra_mansa',
    name: 'Barra Mansa',
    state: 'RJ',
    institution: 'Prefeitura Municipal de Barra Mansa',
    holidays: [
      { day: 3, month: 10, name: 'Aniversário de Barra Mansa', type: 'emancipacao' },
      { day: 20, month: 1, name: 'Dia de São Sebastião', type: 'padroeiro' },
    ],
  },
  itatiaia: {
    id: 'itatiaia',
    name: 'Itatiaia',
    state: 'RJ',
    institution: 'Prefeitura Municipal de Itatiaia',
    holidays: [
      { day: 1, month: 6, name: 'Emancipação de Itatiaia', type: 'emancipacao' },
      { day: 19, month: 3, name: 'Dia de São José (Padroeiro)', type: 'padroeiro' },
    ],
  },
  volta_redonda: {
    id: 'volta_redonda',
    name: 'Volta Redonda',
    state: 'RJ',
    institution: 'Prefeitura Municipal de Volta Redonda',
    holidays: [
      { day: 17, month: 7, name: 'Aniversário de Volta Redonda', type: 'emancipacao' },
      { day: 13, month: 6, name: 'Dia de Santo Antônio (Padroeiro)', type: 'padroeiro' },
    ],
  },
  porto_real: {
    id: 'porto_real',
    name: 'Porto Real',
    state: 'RJ',
    institution: 'Prefeitura Municipal de Porto Real',
    holidays: [
      { day: 5, month: 11, name: 'Emancipação de Porto Real', type: 'emancipacao' },
      { day: 26, month: 7, name: 'Dia de Sant’Ana', type: 'padroeiro' },
    ],
  },
  pirai: {
    id: 'pirai',
    name: 'Piraí',
    state: 'RJ',
    institution: 'Prefeitura Municipal de Piraí',
    holidays: [
      { day: 17, month: 10, name: 'Emancipação de Piraí', type: 'emancipacao' },
      { day: 26, month: 7, name: 'Dia de Sant’Ana', type: 'padroeiro' },
    ],
  },
  quatis: {
    id: 'quatis',
    name: 'Quatis',
    state: 'RJ',
    institution: 'Prefeitura Municipal de Quatis',
    holidays: [
      { day: 25, month: 11, name: 'Emancipação de Quatis', type: 'emancipacao' },
      { day: 20, month: 1, name: 'Dia de São Sebastião', type: 'padroeiro' },
    ],
  },
};
